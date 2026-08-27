from django.shortcuts import render
from django.http import Http404
from .models import Post

def posts_list(request):
    posts = Post.objects.all()
    return render(request, "blog/posts_list.html", {"posts" : posts})


def post_detail(request, post_id):
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        raise Http404("Post not found")
    return render(request, "blog/post_detail.html", {"post" : post})



