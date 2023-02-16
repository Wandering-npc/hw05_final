from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, Client
from django.urls import reverse
from http import HTTPStatus

from posts.models import Post, Group

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создадим запись в БД
        cls.user = User.objects.create_user(username='StasBasov')
        cls.group = Group.objects.create(
            title='Тестгруппа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Текст',
            author=cls.user,
            group=cls.group
        )

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем пользователя
        self.user = User.objects.get(username='StasBasov')
        # Создаем второй клиент
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Шаблоны по адресам
        templates_url_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:profile', kwargs={
                    'username': self.user.username}): 'posts/profile.html',
            reverse('posts:post_detail', kwargs={
                'post_id': self.post.pk}): 'posts/post_detail.html',
            reverse('posts:group_list', kwargs={
                'slug': self.group.slug}): 'posts/group_list.html',
            reverse('posts:post_create'): 'posts/post_create.html',
            reverse('posts:post_edit', kwargs={
                'post_id': self.post.pk}): 'posts/post_create.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_guest_client(self):
        """Тест на доступность страниц."""
        addresses = (
            reverse('posts:index'),
            reverse('posts:profile', kwargs={
                    'username': self.user.username}),
            reverse('posts:post_detail', kwargs={
                'post_id': self.post.pk}),
            reverse('posts:group_list', kwargs={
                'slug': self.group.slug}),
        )
        for address in addresses:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_guest_client_no_access(self):
        """Тест на отсутствие доступа у неавторизованного пользователя."""
        addresses = (
            reverse('posts:post_create'),
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}))
        for address in addresses:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_auth_client_access(self):
        """Тест на доступность создания поста."""
        address = reverse('posts:post_create')
        response = self.authorized_client.get(address)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_author_access(self):
        """Тест на доступность редатирования поста автором."""
        address = reverse('posts:post_edit', kwargs={
            'post_id': self.post.pk})
        response = self.authorized_client.get(address)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_not_exist_page(self):
        """Тест на недоступность несуществующей страницы"""
        response = self.guest_client.get('/posts/not_exist/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
