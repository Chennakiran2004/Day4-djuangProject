from django.db import models

# Create your models here.
class Post(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published')
    ]

    title = models.CharField(max_length = 200)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add = True)
    
    status = models.CharField(max_length = 10, choices=STATUS_CHOICES, default='draft')

    def __str__(self):
        return self.title


