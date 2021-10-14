import tempfile
import shutil
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Post, Group, Follow
from django import forms
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test-username')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая группа',
            group=cls.group,
            pk=1
        )

    def setUp(self):
        # Создаем авторизованный клиент
        self.user = User.objects.create_user(username='StasBasov')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        Post.objects.create(
            author=self.user,
            text='Тестовая группа 2',
            pk=2
        )
        Post.objects.create(
            author=self.user,
            text='Тестовая группа 2',
            pk=3
        )

    # Проверяем используемые шаблоны
    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        cache.clear()
        # Собираем в словарь пары "имя_html_шаблона: reverse(name)"
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_posts',
                    kwargs={'slug': 'test_slug'}
                    ): 'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': 'test-username'}
                    ): 'posts/profile.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_detail', kwargs={'post_id': '1'}
                    ): 'posts/posts.html',
            reverse('posts:follow_index'): 'posts/follow.html',
            reverse('posts:post_edit', kwargs={'post_id': '3'}
                    ): 'posts/create_post.html',
        }

        # Проверяем, что при обращении к name
        # вызывается соответствующий HTML-шаблон
        for reverse_name, template in templates_pages_names.items():
            cache.clear()
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    # Проверка словаря контекста главной страницы (в нём передаётся форма)
    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }

        # Проверяем, что типы полей формы в словаре
        # context соответствуют ожиданиям
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                # Проверяет, что поле формы является экземпляром
                # указанного класса
                self.assertIsInstance(form_field, expected)

    def test_group_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом"""
        response_group = self.authorized_client.get(
            reverse('posts:group_posts', kwargs={'slug': 'test_slug'}))
        group_posts = response_group.context['page_obj']
        for post in group_posts:
            with self.subTest(post=post):
                checked_post = Post.objects.get(id=post.id)
                self.assertEqual(post.text, checked_post.text)
                self.assertEqual(post.author, checked_post.author)
                self.assertEqual(post.group, checked_post.group)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_edit',
                                                      kwargs={'post_id': '2'}
                                                      )
                                              )
        # Словарь ожидаемых типов полей формы:
        # указываем, объектами какого класса должны быть поля формы
        form_fields = {
            'text': forms.fields.CharField,
        }

        # Проверяем, что типы полей формы в
        # словаре context соответствуют ожиданиям
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                # Проверяет, что поле формы является экземпляром
                # указанного класса
                self.assertIsInstance(form_field, expected)


class PaginatorViewsTest(TestCase):
    # Здесь создаются фикстуры: клиент и 13 тестовых записей.
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cache.clear()
        cls.user = User.objects.create_user(username='test-username')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.test_posts_list = []
        for i in range(1, 14):
            created_post = Post.objects.create(
                text=f'Тестовый текст для 1 группы {i}.',
                     author=cls.user, group=cls.group)
            cls.test_posts_list.append(created_post)
        cls.another_group = Group.objects.create(
            title='Другая группа', slug='test_slug_2',
                  description='Тестовое описание 2')

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='StasBasov')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_page_contains_ten_records(self):
        response = self.client.get(reverse('posts:index'))
        posts = response.context['page_obj']
        count = 0
        for post in posts:
            with self.subTest(post=post):
                count += 1
        self.assertEqual(count, 10)

        # Проверка: количество постов на первой странице равно 10.

    def test_second_page_contains_three_records(self):
        # Проверка: на второй странице должно быть три поста.
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_author_posts(self):
        # Проверка: посты на первой странице автора.
        response = self.client.get(reverse('posts:profile',
                                           kwargs={'username': 'test-username'}
                                           )
                                   )
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_group_posts(self):
        # Проверка: посты на первой странице группы.
        response = self.client.get(reverse('posts:group_posts',
                                           kwargs={'slug': 'test_slug'}
                                           )
                                   )
        self.assertEqual(len(response.context['page_obj']), 10)


class PostCreateTest(TestCase):
    # Здесь создаются фикстуры: клиент и 13 тестовых записей.
    @classmethod
    def setUpClass(cls):
        cache.clear()
        super().setUpClass()
        cls.user = User.objects.create_user(username='test-username')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.test_posts_list = []
        for i in range(1, 14):
            created_post = Post.objects.create(
                text=f'Тестовый текст для 1 группы {i}.',
                     author=cls.user, group=cls.group)
            cls.test_posts_list.append(created_post)
        cls.another_group = Group.objects.create(
            title='Другая группа', slug='test_slug_2',
                  description='Тестовое описание 2')

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='StasBasov')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_index_context(self):
        # Проверка: контекст view-функции index работает правильно"""
        response_index = self.client.get(reverse('posts:index'))
        posts = response_index.context['page_obj']
        for post in posts:
            with self.subTest(post=post):
                checked_post = Post.objects.get(id=post.id)
                self.assertEqual(post.text, checked_post.text)
                self.assertEqual(post.author, checked_post.author)
                self.assertEqual(post.group, checked_post.group)

    def test_profile_context(self):
        # Проверка: контекст view-функции profile работает правильно"""
        response_index = self.client.get(
            reverse('posts:profile', kwargs={'username': 'test-username'}))
        posts = response_index.context['page_obj']
        for post in posts:
            with self.subTest(post=post):
                checked_post = Post.objects.get(id=post.id)
                self.assertEqual(post.text, checked_post.text)
                self.assertEqual(post.author, checked_post.author)
                self.assertEqual(post.group, checked_post.group)

    def test_profile_context(self):
        # Проверка: контекст view-функции post_detail работает правильно"""
        response_index = self.client.get(
            reverse('posts:post_detail', kwargs={'post_id': '2'}))
        form_fields = {
            'text': forms.fields.CharField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response_index.context.get(
                    'form').fields.get(value)
                # Проверяет, что поле формы является экземпляром
                # указанного класса
                self.assertIsInstance(form_field, expected)

    def test_post_not_in_wrong_group(self):
        # Проверка: посты не попали в другую группу.
        response_group_2 = self.guest_client.get(reverse('posts:group_posts',
                                                 kwargs={'slug': 'test_slug_2'}
                                                         )
                                                 )
        posts = response_group_2.context['page_obj']
        for post in posts:
            with self.subTest(post=post):
                checked_post = Post.objects.get(id=post.id)
                self.assertNotIn(checked_post, posts)

    def test_index_page_cash(self):
        index_content = self.authorized_client.get(reverse('posts:index')
                                                   ).content
        Post.objects.create(
            text='Тестовый текст',
            author=self.user,
        )
        index_content_cache = self.authorized_client.get(reverse('posts:index')
                                                         ).content
        self.assertEqual(index_content, index_content_cache)
        cache.clear()
        index_content_clear = self.authorized_client.get(reverse('posts:index')
                                                         ).content
        self.assertNotEqual(index_content, index_content_clear)


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        cache.clear()
        super().setUpClass()
        cls.user1 = User.objects.create_user(username='test_following')
        cls.post = Post.objects.create(
            author=cls.user1,
            text='Тестовый пост',
            pk=1
        )
        cls.user2 = User.objects.create_user(username='test_follower')
        cls.follow_object = Follow.objects.create(
            author=cls.user1,
            user=cls.user2,
        )
        cls.user3 = User.objects.create_user(username='just_user')
        cls.post2 = Post.objects.create(
            author=cls.user3,
            text='Тестовый пост',
            pk=3
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user2)

    def test_follow_index_context(self):
        # Проверка: контекст view-функции index работает правильно"""
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertEqual(len(response.context['page_obj']), 1)

    def test_user_can_follow(self):
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': 'just_user'}))
        follow_count = Follow.objects.filter(user=self.user2,
                                             author=self.user3).count()
        self.assertEqual(follow_count, 1)

    def test_user_can_unfollow(self):
        self.authorized_client.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': 'just_user'}))
        follow_count = Follow.objects.filter(user=self.user2,
                                             author=self.user3).count()
        self.assertEqual(follow_count, 0)

    def test_new_post_in_index_follow(self):
        posts_count = Post.objects.filter(author=self.user1).count()
        Post.objects.create(
            author=self.user1,
            text='Тестовый пост',
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertEqual(len(response.context['page_obj']), posts_count + 1)

    def test_new_post_not_in_index_follow(self):
        posts_count = Post.objects.filter(author=self.user3).count()
        Post.objects.create(
            author=self.user3,
            text='Тестовый пост',
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertEqual(len(response.context['page_obj']), posts_count)


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ImageTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test-username')
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif',
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post_with_image = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
            image=cls.uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_image_profile_context(self):
        response_profile = self.client.get(reverse(
            'posts:profile', kwargs={'username': 'test-username'}))
        posts = response_profile.context['page_obj']
        self.assertIn(self.post_with_image, posts)
        self.assertEqual(
            self.post_with_image.image,
            Post.objects.get(pk=self.post_with_image.pk).image)

    def test_image_post_detail_context(self):
        response_post_detail = self.client.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post_with_image.pk}))
        context_post = response_post_detail.context['post']
        checked_post = Post.objects.get(id=context_post.id)
        self.assertEqual(context_post.text, checked_post.text)
        self.assertEqual(
            self.post_with_image.image,
            Post.objects.get(pk=context_post.pk).image)

    def test_image_index_context(self):
        response_index = self.client.get(reverse('posts:index'))
        posts = response_index.context['page_obj']
        self.assertIn(self.post_with_image, posts)
        self.assertEqual(
            self.post_with_image.image,
            Post.objects.get(pk=self.post_with_image.pk).image)

    def test_image_group_context(self):
        response_group = self.client.get(reverse(
            'posts:group_posts', kwargs={'slug': 'test_slug'}))
        posts = response_group.context['page_obj']
        self.assertIn(self.post_with_image, posts)
        self.assertEqual(
            self.post_with_image.image,
            Post.objects.get(pk=self.post_with_image.pk).image)
