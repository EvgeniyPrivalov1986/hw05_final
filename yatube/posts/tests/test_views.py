from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from django import forms

from ..models import Comment, Group, Post, User
from ..servises import PAGINATOR_QUANTITY

POSTS_ON_SECOND_PAGE = 3


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(
            username='post_author',
        )
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            slug='test-slug',
            description='Тестовое описание группы',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Random_text',
            author=PostPagesTests.user,
            group=PostPagesTests.group,
            image=uploaded,
        )
        cls.group_fake = Group.objects.create(
            title='Фейк группа',
            slug='fake-slug',
            description='Описание фейк группы',
        )
        cls.comment = Comment.objects.create(
            text='Comment_text',
            author=PostPagesTests.user,
            post=PostPagesTests.post,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_views_use_correct_template(self):
        """Во view-функциях используются правильные html-шаблоны."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list', args={self.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', args={self.user.username}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail', args={self.post.id}
            ): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/post_create.html',
            reverse(
                'posts:post_edit', args={self.post.id}
            ): 'posts/post_create.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_pages_show_correct_context(self):
        """В шаблоны передается правильный словарь context для страниц"""
        context = {
            reverse('posts:index'): self.post,
            reverse('posts:group_list', args={self.group.slug}): self.post,
            reverse('posts:profile', args={self.user.username}): self.post,
        }
        for reverse_page, object in context.items():
            with self.subTest(reverse_page=reverse_page):
                response = self.authorized_client.get(reverse_page)
                page_object = response.context['page_obj'][0]
                self.assertEqual(page_object.text, object.text)
                self.assertEqual(page_object.pub_date, object.pub_date)
                self.assertEqual(page_object.author, object.author)
                self.assertEqual(page_object.group, object.group)
                self.assertEqual(page_object.image, object.image)

    def test_groups_page_show_correct_context(self):
        """В шаблоны передается правильный словарь context для групп"""
        context = {
            reverse('posts:group_list', args={self.group.slug}): self.group,
            reverse(
                'posts:group_list', args={self.group_fake.slug}
            ): self.group_fake,
        }
        response = self.authorized_client.get(
            reverse('posts:group_list', args={self.group_fake.slug}))
        self.assertFalse(response.context['page_obj'])
        for reverse_page, object in context.items():
            with self.subTest(reverse_page=reverse_page):
                response = self.authorized_client.get(reverse_page)
                group_object = response.context['group']
                self.assertEqual(group_object.title, object.title)
                self.assertEqual(group_object.slug, object.slug)
                self.assertEqual(group_object.description,
                                 object.description)

    def test_authors_show_correct_context(self):
        """В шаблоны передается правильный словарь context для авторов"""
        context = {reverse('posts:profile',
                   args={self.user.username}): self.user,
                   }
        for reverse_page, object in context.items():
            with self.subTest(reverse_page=reverse_page):
                response = self.authorized_client.get(reverse_page)
                author_object = response.context['author']
                self.assertEqual(author_object.id, object.id)
                self.assertEqual(author_object.username, object.username)

    def test_post_page_show_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:post_detail',
                    args={self.post.id}))
        post_object = response.context['post']
        self.assertEqual(post_object.text, self.post.text)
        self.assertEqual(post_object.pub_date, self.post.pub_date)
        self.assertEqual(post_object.author, self.user)
        self.assertEqual(post_object.group, self.group)
        self.assertEqual(post_object.image, self.post.image)

    def test_forms_show_correct_instance(self):
        """В шаблоны передаются правильные формы"""
        context = {
            reverse('posts:post_create'),
            reverse('posts:post_edit', args={self.post.id}),
        }
        for reverse_page in context:
            with self.subTest(reverse_page=reverse_page):
                response = self.authorized_client.get(reverse_page)
                self.assertIsInstance(response.context['form'].fields['text'],
                                      forms.fields.CharField)
                self.assertIsInstance(response.context['form'].fields['group'],
                                      forms.fields.ChoiceField)
                self.assertIsInstance(response.context['form'].fields['image'],
                                      forms.fields.ImageField)

    def test_comments_show_correct_context(self):
        """Комментарий отображается на странице поста"""
        response = self.authorized_client.get(
            reverse('posts:post_detail',
                    args={self.post.id}))
        post_object = response.context['comments'][0]
        self.assertEqual(post_object.text, self.comment.text)
        self.assertEqual(post_object.author, self.user)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(
            username='posts_author',
        )
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            slug='test-slug',
            description='Тестовое описание группы',
        )
        posts = [
            Post(
                text='Пост №' + str(i),
                author=PaginatorViewsTest.user,
                group=PaginatorViewsTest.group
            )
            for i in range(PAGINATOR_QUANTITY + POSTS_ON_SECOND_PAGE)]
        Post.objects.bulk_create(posts)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_paginator_on_pages(self):
        """На страницах выводиться правильное количество постов"""
        context = {
            reverse('posts:index'): PAGINATOR_QUANTITY,
            reverse('posts:index') + '?page=2': POSTS_ON_SECOND_PAGE,
            reverse(
                'posts:group_list', args={self.group.slug}
            ): PAGINATOR_QUANTITY,
            reverse(
                'posts:group_list', args={self.group.slug}
            ) + '?page=2': POSTS_ON_SECOND_PAGE,
            reverse(
                'posts:profile', args={self.user.username}
            ): PAGINATOR_QUANTITY,
            reverse(
                'posts:profile', args={self.user.username}
            ) + '?page=2': POSTS_ON_SECOND_PAGE,
        }
        for reverse_page, len_posts in context.items():
            with self.subTest(reverse=reverse):
                self.assertEqual(len(
                    self.client.get(reverse_page).context.get('page_obj')
                ), len_posts)


class CacheIndexPageTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(
            username='posts_author',
        )

    def setUp(self):
        self.guest_client = Client()
        self.guest_client.force_login(self.user)

    def test_cache(self):
        """Список постов на главной странице храниться в кеше"""
        content = self.guest_client.get(reverse('posts:index')).content
        Post.objects.create(
            text='Пост №1',
            author=self.user,
        )
        content_1 = self.guest_client.get(reverse('posts:index')).content
        self.assertEqual(content, content_1)
        cache.clear()
        content_2 = self.guest_client.get(reverse('posts:index')).content
        self.assertNotEqual(content_1, content_2)


class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(
            username='posts_author',
        )
        cls.follower = User.objects.create(
            username='follower',
        )
        cls.post = Post.objects.create(
            author=FollowViewsTest.author,
            text='Текст поста',
        )

    def setUp(self):
        cache.clear()
        self.follower_client = Client()
        self.follower_client.force_login(self.follower)
        self.author_client = Client()
        self.author_client.force_login(self.author)

    def test_follow_page_context(self):
        """Авторизированный пользователь может подписаться на автора"""
        response = self.follower_client.get(reverse('posts:follow_index'))
        page_object = response.context.get('page_obj').object_list
        self.assertEqual((len(page_object)), 0)
        self.follower_client.get(
            reverse('posts:profile_follow', args={self.author.username})
        )
        response = self.follower_client.get(reverse('posts:follow_index'))
        self.assertEqual((len(response.context['page_obj'])), 1)
        page_object = response.context.get('page_obj').object_list[0]
        self.assertEqual(page_object.author, self.author)
        self.assertEqual(page_object.text, self.post.text)
        self.assertEqual(page_object.pub_date, self.post.pub_date)

    def test_unfollow_page_context(self):
        """Авторизированный пользователь может отписаться от автора"""
        response = self.follower_client.get(reverse('posts:follow_index'))
        page_object = response.context.get('page_obj').object_list
        self.assertEqual((len(page_object)), 0)
        self.follower_client.get(
            reverse('posts:profile_follow', args={self.author.username})
        )
        response = self.follower_client.get(reverse('posts:follow_index'))
        self.assertEqual((len(response.context['page_obj'])), 1)
        self.follower_client.get(
            reverse('posts:profile_unfollow', args={self.author.username})
        )
        response = self.follower_client.get(reverse('posts:follow_index'))
        page_object = response.context.get('page_obj').object_list
        self.assertEqual((len(page_object)), 0)

    def test_cant_following_self(self):
        """Неавторизированный пользователь не может подписаться на автора"""
        response = self.author_client.get(reverse('posts:follow_index'))
        self.assertEqual(
            (len(response.context.get('page_obj').object_list)), 0
        )
        self.author_client.get(
            reverse('posts:profile_follow', args={self.author.username})
        )
        response = self.author_client.get(reverse('posts:follow_index'))
        self.assertEqual(
            (len(response.context.get('page_obj').object_list)), 0
        )
