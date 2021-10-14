from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from .models import Post, Group, User, Follow
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page
from posts.forms import PostForm, CommentForm


@cache_page(60 * 15)
def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'posts/index.html', {'page_obj': page, })


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, "posts/group_list.html", {"group": group,
                                                     "page_obj": page,
                                                     }
                  )


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    posts_number = posts.count()
    paginator = Paginator(posts, 10)
    page_num = request.GET.get('page')
    page_obj = paginator.get_page(page_num)
    full_name = author.get_full_name()
    following = None
    if request.user.is_authenticated:
        following = Follow.objects.filter(user=request.user,
                                          author=author
                                          ).exists()
    context = {'author': author,
               "username": username,
               "full_name": full_name,
               'page_obj': page_obj,
               "posts_number": posts_number,
               'following': following,
               }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    author = post.author
    all_posts = Post.objects.filter(author=post.author)
    post_count = all_posts.count()
    comments = post.comments.all()
    form = CommentForm()
    context = {
        'author': author,
        'post': post,
        'post_count': post_count,
        'comments': comments,
        'form': form,
    }

    return render(request, 'posts/posts.html', context)


@login_required
def post_create(request):
    if request.method == 'POST':
        form = PostForm(request.POST, files=request.FILES or None,
                        )
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            form.save()
            return redirect(
                reverse('posts:profile',
                        kwargs={
                            'username': post.author.username,
                        }
                        )
            )
        return render(request, 'posts/create_post.html', {"form": form})
    form = PostForm()
    return render(request, 'posts/create_post.html',
                  {"form": form, 'new': True}
                  )


@login_required
def post_edit(request, post_id):
    post_to_edit = get_object_or_404(Post, pk=post_id)
    if request.user == post_to_edit.author:
        form = PostForm(request.POST or None, 
                        files=request.FILES or None,
                        instance=post_to_edit)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            form.save()
            return redirect('posts:post_detail', post_id)
        return render(request, 'posts/create_post.html',
                      {"form": form, 'is_edit': True})
    return redirect('posts:post_detail', post_id)


@login_required
def add_comment(request, post_id):
    # Получите пост
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
    post_list = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    if user != author:
        Follow.objects.get_or_create(user=user, author=author)
    return redirect('posts:profile', username=author.username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('posts:profile', username=username)
