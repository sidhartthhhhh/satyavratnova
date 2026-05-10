from django.urls import path

from . import views

urlpatterns = [
    path("health/", views.health),
    path("users/", views.users),
    path("media/presigned-url/", views.make_upload_url),
    path("posts/", views.posts),
    path("posts/search/", views.search_posts),
    path("posts/trending/top10/", views.top_trending),
    path("posts/trending/", views.trending),
    path("posts/<int:post_id>/", views.one_post),
]
