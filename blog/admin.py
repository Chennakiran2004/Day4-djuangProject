from django.contrib import admin
from .models import Post, Comments, Category

# Register your models here.

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'body', 'created_at')
    search_fields = ('title', 'body', 'created_at')

@admin.register(Comments)
class CommentsAdmin(admin.ModelAdmin):
    list_display = ('post', 'name', 'created_at')
    search_fields = ('name', 'created_at')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fileds = ('name',)