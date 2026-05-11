import json

import boto3
from django.conf import settings
from django.db.models import Q
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .cache_utils import cache_get_json, cache_set_json
from .media_utils import validate_media_file
from .models import Post, User


def post_to_json(p):
    return {
        "id": p.id,
        "user_id": p.user_id,
        "caption": p.caption,
        "media_url": p.media_url,
        "bitrate_status": p.bitrate_status,
        "timestamp": p.timestamp.isoformat(),
    }


def user_to_json(u):
    return {
        "id": u.id,
        "username": u.username,
        "email": u.email,
        "created_at": u.created_at.isoformat(),
    }


def get_body(request):
    try:
        return json.loads(request.body.decode("utf-8"))
    except Exception:
        return {}


def get_int_param(request, name, default, max_value):
    try:
        num = int(request.GET.get(name, default))
    except Exception:
        num = default
    if num < 0:
        num = 0
    if num > max_value:
        num = max_value
    return num


def get_trending_posts(limit=20):
    tags = ["#viral", "#fyp", "#trending", "#slay"]
    my_filter = Q()
    for tag in tags:
        my_filter = my_filter | Q(caption__icontains=tag)

    posts = Post.objects.filter(my_filter).order_by("-timestamp")[:limit]
    return tags, [post_to_json(p) for p in posts]


def health(request):
    return JsonResponse({"ok": True, "time": timezone.now().isoformat()})


@csrf_exempt
@require_http_methods(["GET", "POST"])
def users(request):
    if request.method == "GET":
        all_users = User.objects.all().order_by("-created_at")
        return JsonResponse({"users": [user_to_json(x) for x in all_users]})

    data = get_body(request)
    if not data.get("username") or not data.get("email"):
        return JsonResponse({"error": "username and email are needed"}, status=400)

    try:
        new_user = User.objects.create(
            username=data.get("username"),
            email=data.get("email"),
        )
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse(user_to_json(new_user), status=201)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def posts(request):
    if request.method == "GET":
        limit = get_int_param(request, "limit", 20, 100)
        offset = get_int_param(request, "offset", 0, 100000)
        query = Post.objects.select_related("user").all()
        total = query.count()
        page = query[offset : offset + limit]
        next_offset = offset + limit
        if next_offset >= total:
            next_offset = None
        return JsonResponse(
            {
                "limit": limit,
                "offset": offset,
                "next_offset": next_offset,
                "total": total,
                "posts": [post_to_json(p) for p in page],
            }
        )

    data = get_body(request)
    required_fields = ["user_id", "caption", "media_url"]
    for field in required_fields:
        if not data.get(field):
            return JsonResponse({"error": field + " is missing"}, status=400)

    try:
        user = User.objects.get(id=data.get("user_id"))
    except User.DoesNotExist:
        return JsonResponse({"error": "user does not exist"}, status=404)

    new_post = Post.objects.create(
        user=user,
        caption=data.get("caption"),
        media_url=data.get("media_url"),
        bitrate_status=data.get("bitrate_status", "pending"),
    )
    cache_set_json("top10trending:v1", "", ttl=1)
    return JsonResponse(post_to_json(new_post), status=201)


@csrf_exempt
@require_http_methods(["GET", "DELETE"])
def one_post(request, post_id):
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return JsonResponse({"error": "post not found"}, status=404)

    if request.method == "GET":
        return JsonResponse(post_to_json(post))

    post.delete()
    cache_set_json("top10trending:v1", "", ttl=1)
    return JsonResponse({"deleted": True, "post_id": post_id})


@csrf_exempt
@require_http_methods(["POST"])
def make_upload_url(request):
    data = get_body(request)
    result = validate_media_file(data.get("file_name"), data.get("file_size"))
    if not result["ok"]:
        return JsonResponse({"error": "bad media file", "details": result["errors"]}, status=400)

    content_type = data.get("content_type") or result["content_type"]
    if content_type != result["content_type"]:
        return JsonResponse({"error": "content_type does not match file extension"}, status=400)

    try:
        s3 = boto3.client(
            "s3",
            region_name=settings.AWS_REGION,
            endpoint_url=settings.AWS_S3_ENDPOINT_URL or None,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )
        signed = s3.generate_presigned_post(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=result["s3_key"],
            Fields={"Content-Type": content_type},
            Conditions=[
                {"Content-Type": content_type},
                ["content-length-range", 1, settings.MAX_UPLOAD_BYTES],
            ],
            ExpiresIn=settings.AWS_PRESIGNED_SECONDS,
        )
    except Exception as e:
        return JsonResponse({"error": "could not make s3 url", "details": str(e)}, status=500)

    return JsonResponse(
        {
            "upload_url": signed["url"],
            "fields": signed["fields"],
            "s3_key": result["s3_key"],
            "media_url": signed["url"].rstrip("/") + "/" + result["s3_key"],
            "max_upload_bytes": settings.MAX_UPLOAD_BYTES,
            "expires_in": settings.AWS_PRESIGNED_SECONDS,
        },
        status=201,
    )


@require_http_methods(["GET"])
def trending(request):
    hashtag_text = request.GET.get("hashtags", "#viral,#fyp,#trending,#slay")
    tags = [x.strip() for x in hashtag_text.split(",") if x.strip()]

    my_filter = Q()
    for tag in tags:
        my_filter = my_filter | Q(caption__icontains=tag)

    try:
        limit = int(request.GET.get("limit", 20))
    except Exception:
        limit = 20

    if limit > 50:
        limit = 50
    if limit < 1:
        limit = 1

    trending_posts = Post.objects.filter(my_filter).order_by("-timestamp")[:limit]
    return JsonResponse(
        {
            "algorithm": "recent posts matching the requested hashtags",
            "hashtags": tags,
            "posts": [post_to_json(p) for p in trending_posts],
        }
    )


@require_http_methods(["GET"])
def top_trending(request):
    cached = cache_get_json("top10trending:v1")
    if cached:
        cached["cache"] = "hit"
        return JsonResponse(cached)

    tags, posts = get_trending_posts(limit=10)
    payload = {
        "algorithm": "top 10 recent posts with the main gen z hashtags",
        "hashtags": tags,
        "posts": posts,
    }
    cache_set_json("top10trending:v1", payload, ttl=60)
    payload["cache"] = "miss"
    return JsonResponse(payload)


@require_http_methods(["GET"])
def search_posts(request):
    q = request.GET.get("q", "").strip()
    if not q:
        return JsonResponse({"error": "q is required"}, status=400)

    limit = get_int_param(request, "limit", 20, 100)
    offset = get_int_param(request, "offset", 0, 100000)
    results = Post.objects.filter(caption__icontains=q).order_by("-timestamp")
    total = results.count()
    page = results[offset : offset + limit]
    next_offset = offset + limit
    if next_offset >= total:
        next_offset = None

    return JsonResponse(
        {
            "q": q,
            "strategy": "PostgreSQL pg_trgm GIN index, with Django icontains lookup",
            "limit": limit,
            "offset": offset,
            "next_offset": next_offset,
            "total": total,
            "posts": [post_to_json(p) for p in page],
        }
    )
