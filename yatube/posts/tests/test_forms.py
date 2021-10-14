import tempfile
import shutil
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.forms import PostForm
from posts.models import Group, Post, Comment

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.form = PostForm()
        cls.user = User.objects.create_user(username='test-username')
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Тестовый комментарий',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_posts_create(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст 2',
            'group': PostFormTests.group.pk,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )

        self.assertRedirects(response, reverse('posts:profile',
                                               kwargs={'username':
                                                       'test-username',
                                                       }
                                               )
                             )
        self.assertEqual(Post.objects.count(), posts_count + 1)

    def test_guest_cant_create(self):
        new_post_create = self.guest_client.post(
            reverse('posts:post_create'),
            data={'text': 'Test text',
                  'author': self.guest_client,
                  'group': self.group.id, })
        login_url = reverse('login')
        new_post_url = reverse('posts:post_create')
        target_url = f'{login_url}?next={new_post_url}'
        self.assertRedirects(new_post_create, target_url)

    def test_not_author_cant_edit(self):
        user2 = User.objects.create_user(username='test-username2')
        authorized_client2 = Client()
        authorized_client2.force_login(user2)
        post_id = PostFormTests.post.pk
        post_url = reverse(
            'posts:post_edit',
            kwargs={'post_id': post_id})
        form_data = {
            'text': 'Измененный текст',
            'group': self.group.pk,
        }
        response_edit = authorized_client2.post(
            post_url,
            data=form_data,
            follow=True,)
        self.assertRedirects(response_edit,
                             reverse('posts:post_detail',
                                     kwargs={'post_id': post_id})
                             )

    def test_post_edit(self):
        post_id = PostFormTests.post.pk
        post_url = reverse(
            'posts:post_edit',
            kwargs={'post_id': post_id})
        form_data = {
            'text': 'Измененный текст',
            'group': self.group.pk,
        }
        response_edit = self.authorized_client.post(
            post_url,
            data=form_data,
            follow=True,)
        edited_post = response_edit.context.get('post')
        self.assertRedirects(response_edit,
                             reverse('posts:post_detail',
                                     kwargs={'post_id': post_id})
                             )
        self.assertEqual(edited_post.author, self.post.author)
        self.assertEqual(edited_post.text, form_data['text'])

    def test_create_post_img(self):
        """Валидная форма создает запись с картинкой в Post."""
        post_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif')

        form_data = {
            'title': 'Тестовый заголовок',
            'text': 'Тестовый текст',
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:profile',
                             kwargs={'username': self.user.username}))
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                author=self.user,
                text='Тестовый текст',
                image='posts/small.gif',
            ).exists()
        )

    def test_comment_create(self):
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый текст',
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:post_detail',
                             kwargs={'post_id': self.post.id}))
        self.assertEqual(Comment.objects.count(), comments_count + 1)

    def test_guest_cant_comment(self):
        self.guest_client.post(
            reverse('posts:add_comment',
                    kwargs={'post_id': self.post.id}), {"text": "test_comment"})
        self.assertFalse(Comment.objects.filter(text="test_comment").exists())
