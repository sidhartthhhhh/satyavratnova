from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def home(request):
    return JsonResponse(
        {
            "message": "Gen Z Posts API is running",
            "try_these": [
                "/api/health/",
                "/api/users/",
                "/api/posts/?limit=10&offset=0",
                "/api/posts/trending/top10/",
                "/api/posts/search/?q=fyp",
                "/api/media/presigned-url/",
            ],
        }
    )


urlpatterns = [
    path("", home),
    path("admin/", admin.site.urls),
    path("api/", include("api.urls")),
]
