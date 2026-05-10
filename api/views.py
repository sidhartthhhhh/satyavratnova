import json

from django.db.models import Q
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

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


def health(request):
    return JsonResponse({"ok": True, "time": timezone.now().isoformat()})


@csrf_exempt
@require_http_methods(["GET", "POST"])
def users(request):
    if request.method == "GET":
        all_users = User.objects.all().order_by("-created_at")
        return JsonResponse({"users": [user_to_json(x) for x in all_users]})

    stuff = get_body(request)
    if not stuff.get("username") or not stuff.get("email"):
        return JsonResponse({"error": "username and email are needed"}, status=400)

    try:
        new_user = User.objects.create(
            username=stuff.get("username"),
            email=stuff.get("email"),
        )
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse(user_to_json(new_user), status=201)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def posts(request):
    if request.method == "GET":
        all_the_posts = Post.objects.select_related("user").all()
        return JsonResponse({"posts": [post_to_json(p) for p in all_the_posts]})

    data = get_body(request)
    needed = ["user_id", "caption", "media_url"]
    for thing in needed:
        if not data.get(thing):
            return JsonResponse({"error": thing + " is missing"}, status=400)

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
    return JsonResponse({"deleted": True, "post_id": post_id})


@require_http_methods(["GET"])
def trending(request):
    hash_tags = request.GET.get("hashtags", "#viral,#fyp,#trending,#slay")
    tags = [x.strip() for x in hash_tags.split(",") if x.strip()]

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

    cool_posts = Post.objects.filter(my_filter).order_by("-timestamp")[:limit]
    return JsonResponse(
        {
            "algorithm": "recent posts that have the hashtags, very advanced obviously",
            "hashtags": tags,
            "posts": [post_to_json(p) for p in cool_posts],
        }
    )
