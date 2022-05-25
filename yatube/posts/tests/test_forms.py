from django.test import Client, TestCase
from django.urls import reverse


from ..models import Group, Post, User


class PostCreateEditFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='post_author')
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            slug='test-slug',
            description='Тестовое описание группы',
        )
        cls.group_2 = Group.objects.create(
            title='Фейк группа',
            slug='group2-slug',
            description='Описание фейк группы',
        )
        cls.post = Post.objects.create(
            text='Текст поста',
            author=PostCreateEditFormTests.user,
            group=PostCreateEditFormTests.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_authorized_client_create_post(self):
        """Авторизированный клиент может создать пост."""
        post_count = Post.objects.count()
        form_data = {
            'text': 'Текст поста',
            'group': self.group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile', args={self.user.username}
        ))
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                author=self.user,
                group=self.group,
            ).exists()
        )

    def test_author_edit_post(self):
        """Автор поста может редактировать пост."""
        form_data = {
            'text': 'Новый текст поста',
            'group': self.group_2.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', args={
                self.post.id
            }),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail', args={self.post.id}
        ))
        first_post = Post.objects.get(id=self.post.id)
        self.assertEqual(first_post.text, form_data['text'])
        self.assertEqual(first_post.author, self.user)
        self.assertEqual(first_post.group, self.group_2)
        self.assertEqual(Post.objects.filter(group=self.group).count(), 0)

    def test_authorized_client_add_comment(self):
        """Авторизированный пользователь добавляет комментарий"""
        self.assertEqual(self.post.comments.count(), 0)
        form_data = {
            'text': 'Текст комментария',
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', args={self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail', args={self.post.id}
        ))
        self.assertEqual(self.post.comments.count(), 1)
        comment_request = self.authorized_client.get(
            reverse('posts:post_detail', args={self.post.id})
        )
        first_object = comment_request.context['comments'][0]
        self.assertEqual(first_object.text, 'Текст комментария')
        self.assertEqual(first_object.author, self.user)
