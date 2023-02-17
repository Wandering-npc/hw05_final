from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page
from .models import Post, Group, User, Follow
from .forms import PostForm, CommentForm
from .utils import paginate


@cache_page(20, key_prefix='index_page')
def index(request):
    """Функция вызова главной страницы."""
    post_list = Post.objects.all()
    page_obj = paginate(request, post_list)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    """Функция вызова страницы с постами групп."""
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    page_obj = paginate(request, post_list)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    """Функция вызова профиля пользователя."""
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    page_obj = paginate(request, post_list)
    following = request.user.is_authenticated
    if following:
        following = request.user.follower.filter(author=author).exists()
    context = {
        'author': author,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    """Отображение информации об определенном посте."""
    post = get_object_or_404(Post, pk=post_id)
    comments = post.comments.all()
    form = CommentForm()
    context = {
        'post': post,
        'form': form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    """Создание поста."""
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if request.method == 'POST' and form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', request.user.username)
    return render(request, 'posts/post_create.html', {'form': form})


@login_required
def post_edit(request, post_id):
    """Редактирование поста."""
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post,
    )
    context = {
        'post': post,
        'form': form,
        'is_edit': True,
    }
    if form.is_valid():
        post = form.save()
        return redirect('posts:post_detail', post_id=post_id)
    return render(request, 'posts/post_create.html', context)


@login_required
def add_comment(request, post_id):
    """Функция отправки комментария"""
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    """Посты избранных авторов."""
    post_list = Post.objects.filter(
        author__following__user=request.user.id).all()
    page_obj = paginate(request, post_list)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    """Подписка."""
    author = get_object_or_404(User, username=username)
    follow = Follow.objects.filter(user=request.user, author=author)
    if author == request.user or follow.exists():
        return redirect(
            'posts:profile', username=username
        )
    Follow.objects.create(user=request.user, author=author)
    return redirect(
        'posts:profile', username=username
    )


@login_required
def profile_unfollow(request, username):
    """Отписка."""
    author = get_object_or_404(User, username=username)
    Follow.objects.get(user=request.user, author=author).delete()
    return redirect('posts:profile', username=username)
