# deals/tests/test_views.py
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Post, Group, Follow
from django import forms
from django.core.cache import cache


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

    # Проверяем используемые шаблоны
    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        cache.clear()
        # Собираем в словарь пары "имя_html_шаблона: reverse(name)"
        templates_pages_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html': reverse('posts:group_posts',
                                             kwargs={'slug': 'test_slug'}
                                             ),
            'posts/profile.html': reverse('posts:profile',
                                          kwargs={'username': 'test-username'}
                                          ),
            'posts/create_post.html': reverse('posts:post_create'),
            'posts/posts.html': reverse('posts:post_detail',
                                        kwargs={'post_id': '1'}
                                        ),
            'posts/follow.html': reverse('posts:follow_index'),
        }

        # Проверяем, что при обращении к name
        # вызывается соответствующий HTML-шаблон
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    # Проверка словаря контекста главной страницы (в нём передаётся форма)
    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        # Словарь ожидаемых типов полей формы:
        # указываем, объектами какого класса должны быть поля формы
        form_fields = {
            'text': forms.fields.CharField,
        }

        # Проверяем, что типы полей формы в словаре
        # context соответствуют ожиданиям
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                # Проверяет, что поле формы является экземпляром
                # указанного класса
                self.assertIsInstance(form_field, expected)

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
        # Проверка: количество постов на первой странице равно 10.
        self.assertEqual(len(response.context['page_obj']), 10)

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
        index_content = self.authorized_client.get(
                            reverse('posts:index')
                                                  ).content
        Post.objects.create(
            text='Тестовый текст',
            author=self.user,
        )
        index_content_cache = self.authorized_client.get(
                                  reverse('posts:index')
                                                        ).content
        self.assertEqual(index_content, index_content_cache)
        cache.clear()
        index_content_cache_clear = self.authorized_client.get(
                                    reverse('posts:index')
                                                               ).content
        self.assertNotEqual(index_content, index_content_cache_clear)


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        cache.clear()
        super().setUpClass()
        cls.user1 = User.objects.create_user(username='test-following')
        cls.post = Post.objects.create(
            author=cls.user1,
            text='Тестовый пост',
            pk=1
        )
        cls.user2 = User.objects.create_user(username='test-follower')
        cls.follow_object = Follow.objects.create(
            author=cls.user1,
            user=cls.user2,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user2)

    def test_follow_index_context(self):
        # Проверка: контекст view-функции index работает правильно"""
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertEqual(len(response.context['page_obj']), 1)
