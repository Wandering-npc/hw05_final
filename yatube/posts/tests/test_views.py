import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django import forms

from posts.models import Post, Group, Follow

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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
            content_type='image/gif')
        # Создадим запись в БД
        cls.author = User.objects.create_user(username='StasBasov')
        cls.group = Group.objects.create(
            title='Тестгруппа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Текст',
            author=cls.author,
            group=cls.group,
            image=cls.uploaded,
        )
        cls.follow = Follow.objects.create(
            user=User.objects.get(username='StasBasov'),
            author=User.objects.create_user(username='AntonChekhov')
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.user = User.objects.get(username='StasBasov')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()
        

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:profile', kwargs={
                    'username': self.author.username}): 'posts/profile.html',
            reverse('posts:post_detail', kwargs={
                'post_id': self.post.pk}): 'posts/post_detail.html',
            reverse('posts:group_list', kwargs={
                'slug': self.group.slug}): 'posts/group_list.html',
            reverse('posts:post_create'): 'posts/post_create.html',
            reverse('posts:post_edit', kwargs={
                'post_id': self.post.pk}): 'posts/post_create.html',
            reverse('posts:follow_index'): 'posts/follow.html',
        }
        for reverse_name, template in templates_url_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_form_pages_show_correct_context(self):
        """Шаблоны с формами сформированы с правильным контекстом."""
        url_names = (
            reverse('posts:post_create'),
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for reverse_name in url_names:
            response = self.authorized_client.get(reverse_name)
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context.get('form').fields.get(value)
                    self.assertIsInstance(form_field, expected)

    def test_post_detail_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = (self.authorized_client.get(
            reverse('posts:post_detail', kwargs={
                'post_id': self.post.pk})))
        self.assertEqual(response.context.get('post').text, self.post.text)
        self.assertEqual(response.context.get('post').author, self.post.author)
        self.assertEqual(response.context.get('post').group, self.post.group)
        self.assertEqual(response.context.get('post').image, self.post.image)

    def test_post_list_pages_show_correct_context(self):
        """Шаблоны со списками постов сформированы с правильным контекстом."""
        addresses = {
            reverse('posts:index'),
            reverse('posts:profile', kwargs={
                    'username': self.author.username}),
            reverse('posts:group_list', kwargs={
                'slug': self.group.slug}),
        }
        for reverse_name in addresses:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                first_object = response.context['page_obj'][0]
                post_author_0 = first_object.author
                post_text_0 = first_object.text
                post_group_0 = first_object.group
                post_image_0 = first_object.image
                self.assertEqual(post_author_0, self.post.author)
                self.assertEqual(post_text_0, self.post.text)
                self.assertEqual(post_group_0, self.post.group)
                self.assertEqual(post_image_0, self.post.image)

    def test_paginator(self):
        """Тест паджинации."""
        paginator_posts = []
        for _ in range(1, 12):
            new_post = Post(
                author=PostPagesTests.author,
                text='Тестовый пост',
                group=PostPagesTests.group
            )
            paginator_posts.append(new_post)

        Post.objects.bulk_create(paginator_posts)
        paginator_urls = {
            'posts:index': None,
            'posts:group_list': {'slug': self.group.slug},
            'posts:profile': {'username': self.author},
        }
        for url, kwargs in paginator_urls.items():
            with self.subTest(url=url):
                response_1 = self.authorized_client.get(reverse(
                    url, kwargs=kwargs))
                response_2 = self.authorized_client.get(reverse(
                    url, kwargs=kwargs) + '?page=2')
                self.assertEqual(len(
                    response_1.context['page_obj']), 10)
                self.assertEqual(len(
                    response_2.context['page_obj']), 2)

    def test_post_correct_destination(self):
        """Тест на отображение поста на нужных страницах."""
        group_2 = Group.objects.create(
            title='Тестгруппа2',
            slug='test-slug2',
            description='Тестовое описание2',)
        addresses = {
            reverse('posts:index'),
            reverse('posts:profile', kwargs={
                    'username': self.author.username}),
            reverse('posts:group_list', kwargs={
                'slug': self.group.slug}),
        }
        for reverse_name in addresses:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                page_obj = response.context['page_obj']
                self.assertIn(self.post, page_obj, 'Нет поста')
        incorrect_group_url = reverse('posts:group_list', kwargs={
            'slug': group_2.slug})
        response = self.authorized_client.get(incorrect_group_url)
        page_obj = response.context['page_obj']
        self.assertNotIn(self.post, page_obj)

    def test_index_cache(self):
        Post.objects.create(
            text='Тест кэша',
            author=self.author,
        )
        response = self.authorized_client.get(reverse('posts:index'))
        page_obj = response.content
        Post.objects.last().delete()
        response_cache = self.authorized_client.get(reverse('posts:index'))
        page_obj_cache = response_cache.content
        self.assertEqual(page_obj, page_obj_cache)
        cache.clear()
        response_after_clear = self.authorized_client.get(reverse('posts:index'))
        page_obj_after_clear = response_after_clear.content
        self.assertNotEqual(page_obj, page_obj_after_clear)

    def test_follow_works_correct(self):
        author = User.objects.create_user(username='Author')
        self.authorized_client.get(reverse('posts:profile_follow', kwargs={
            'username': author.username}))
        self.assertTrue(
            Follow.objects.filter(
                user=self.user,
                author=author,
            ).exists())
        self.authorized_client.get(reverse('posts:profile_unfollow', kwargs={
            'username': author.username}))
        self.assertFalse(
            Follow.objects.filter(
                user=self.user,
                author=author,
            ).exists())
    def test_f(self):
        author_1 = User.objects.create_user(username='Author')
        authors = (author_1, self.follow.author )
        posts = []
        for author in authors:
            post = Post.objects.create(
                author=author,
                text='Тестовый пост',
            )
            posts.append(post)
        response = self.authorized_client.get(reverse('posts:follow_index'))
        context = response.context['page_obj']
        self.assertNotIn(posts[0], context)
        self.assertIn(posts[1], context)


        

        
        
        



'''
Создаешь пост
Сохраняешь ответ в переменную
Потом пост удалчешь
Снова сохраняешь рещльутат со страницу в переменную
И у тебя две страницы ровны должны быьь
'''