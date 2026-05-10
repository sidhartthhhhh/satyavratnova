from django.urls import path

from . import views

urlpatterns = [
    path("health/", views.health),
    path("users/", views.users),
    path("posts/", views.posts),
    path("posts/trending/", views.trending),
    path("posts/<int:post_id>/", views.one_post),
]
