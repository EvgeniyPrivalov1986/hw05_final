from django.views.decorators.cache import cache_page
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required

from .forms import CommentForm, PostForm
from .models import Comment, Group, Follow, Post, User
from .servises import get_paginator


@cache_page(20)
def index(request):
    """Выводит шаблон главной страницы"""
    page_obj = get_paginator(request, Post.objects.all())
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    page_obj = get_paginator(request, group.posts.all())
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    page_obj = get_paginator(request, author.posts.all())
    following = Follow.objects.filter(
        user=request.user.id, author=author.id
    ).all()
    context = {
        'author': author,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm()
    comments = Comment.objects.filter(post=post)
    context = {
        'post': post,
        'form': form,
        'comments': comments
    }
    return render(request, 'posts/post_detail.html', context)


@ login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    user = get_object_or_404(User, username=request.user)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', username=user.username)
    context = {
        'form': form,
    }
    return render(request, 'posts/post_create.html', context)


@ login_required
def post_edit(request, post_id):
    post = Post.objects.get(id=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        post.save()
        return redirect('posts:post_detail', post_id=post_id)
    is_edit = True
    context = {
        'form': form,
        'is_edit': is_edit
    }
    return render(request, 'posts/post_create.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user).all()
    page_obj = get_paginator(request, post_list)
    context = {
        'page_obj': page_obj
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    follow_check = Follow.objects.filter(
        user=request.user.id, author=author.id
    ).count()
    if follow_check == 0 and author.id != request.user.id:
        Follow.objects.create(user=request.user, author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    follow_check = Follow.objects.filter(
        user=request.user.id, author=author.id
    ).count()
    if follow_check == 1:
        Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('posts:profile', username=username)