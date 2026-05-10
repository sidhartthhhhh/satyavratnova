from django.db import models


class User(models.Model):
    username = models.CharField(max_length=80, unique=True)
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "users"

    def __str__(self):
        return self.username


class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    caption = models.TextField()
    media_url = models.URLField(max_length=700)
    bitrate_status = models.CharField(max_length=40, default="pending")
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "posts"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["-timestamp"], name="posts_time_idx"),
        ]

    def __str__(self):
        return self.caption[:40]
