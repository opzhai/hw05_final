# posts/tests/tests_url.py
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from posts.models import Post, Group
from http import HTTPStatus
from django.core.cache import cache

User = get_user_model()


class PostsURLTests(TestCase):
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
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая группа',
            pk=1
        )

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем второй клиент
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(self.user)

    def test_url_exists_at_desired_location_guest(self):
        """Страницы доступны любому пользователю."""
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, 200)
        url_status_codes = {
            '/': HTTPStatus.OK,
            '/about/author/': HTTPStatus.OK,
            '/about/tech/': HTTPStatus.OK,
            f'/group/{PostsURLTests.group.slug}/': HTTPStatus.OK,
            f'/profile/{PostsURLTests.user.username}/': HTTPStatus.OK,
            f'/posts/{PostsURLTests.post.id}/': HTTPStatus.OK,
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
        }
        for adress, code in url_status_codes.items():
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, code)

    def test_post_create_url_exists_at_desired_location_authorized(self):
        """Страница /create/ доступна авторизованному пользователю."""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, 200)

    def test_post_edit_url_exists_at_desired_location_authorized(self):
        """Страница /posts/pk/edit/ доступна автору."""
        response = self.authorized_client.get('/posts/1/edit/')
        self.assertEqual(response.status_code, 200)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Шаблоны по адресам
        cache.clear()
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{PostsURLTests.group.slug}/': 'posts/group_list.html',
            f'/profile/{PostsURLTests.user.username}/': 'posts/profile.html',
            f'/posts/{PostsURLTests.post.id}/': 'posts/posts.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{PostsURLTests.post.id}/edit/': 'posts/create_post.html'
        }
        for adress, template in templates_url_names.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertTemplateUsed(response, template)
