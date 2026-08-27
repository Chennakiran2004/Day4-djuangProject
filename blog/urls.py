from django.urls import path
from . import views

urlpatterns = [
    path("", views.posts_list, name="posts_list"),
    path("<int:post_id>/", views.post_detail, name="post_detail"),
]