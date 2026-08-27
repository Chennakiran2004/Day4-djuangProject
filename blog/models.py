from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.name


class Post(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
    ]

    title = models.CharField(max_length=200)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    categories = models.ManyToManyField(Category, related_name='posts', blank=True)

    def __str__(self):
        return self.title


class Comments(models.Model):
    name = models.CharField(max_length=200)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')

    def __str__(self):
        return f"Comment by {self.name} on {self.post.title}"