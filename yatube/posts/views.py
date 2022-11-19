from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import PostForm, CommentForm
from .models import Comment, Group, Post, Follow, User
from .utils import get_page_obj


def index(request):
    posts = Post.objects.select_related('author', 'group')
    page_obj = get_page_obj(request, posts)
    return render(request, 'posts/index.html', {'page_obj': page_obj})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related('author')
    page_obj = get_page_obj(request, posts)
    return render(request, 'posts/group_list.html', {
        'group': group,
        'page_obj': page_obj
    })


def profile(request, username):
    user = get_object_or_404(User, username=username)
    posts_user = user.posts.select_related('group')
    page_obj = get_page_obj(request, posts_user)
    if request.user.is_authenticated and request.user != user:
        following = Follow.objects.select_related(
            'user', 'author'
        ).exists()
    else:
        following = False
    return render(request, 'posts/profile.html', {
        'author': user,
        'page_obj': page_obj,
        'following': following
    })


def post_detail(request, post_id):
    post = Post.objects.get(id=post_id)
    form = CommentForm(request.POST or None)
    comment = Comment.objects.filter(post=post)
    return render(request, 'posts/post_detail.html', {
        'post': post,
        'form': form,
        'comments': comment
    })


@login_required
def create_post(request):
    form = PostForm(request.POST or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect(reverse('posts:profile', args=[request.user]))
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = Post.objects.get(pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        post.save()
        return redirect('posts:post_detail', post_id)
    return render(request, 'posts/create_post.html', {
        'post': post,
        'form': form,
    })


@login_required
def add_comment(request, post_id):
    post = Post.objects.get(pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    page_obj = get_page_obj(request, post_list)
    return render(request, 'posts/follow.html', {
        'page_obj': page_obj
    })


@login_required
def profile_follow(request, username):
    user = request.user
    author = User.objects.get(username=username)
    is_follower = Follow.objects.filter(user=user, author=author)
    if user != author and not is_follower.exists():
        Follow.objects.create(user=user, author=author)
    return redirect(reverse('posts:profile', args=[username]))


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    is_follower = Follow.objects.filter(user=request.user, author=author)
    if is_follower.exists():
        is_follower.delete()
    return redirect('posts:profile', username=author)
