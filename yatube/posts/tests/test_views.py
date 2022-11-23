import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Follow, Group, Post, User


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.userSecond = User.objects.create_user(username='auth2')
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.upload = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.userSecond,
            group=cls.group,
            text='Тестовый пост',
            image=cls.upload
        )
        cls.public_url = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:profile', args={cls.userSecond}
                    ): 'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': cls.post.id}
                    ): 'posts/post_detail.html',
            reverse('posts:group_list', kwargs={'slug': cls.group.slug}
                    ): 'posts/group_list.html',
        }
        cls.private_url = {
            reverse('posts:create_post'): 'posts/create_post.html',
            reverse('posts:post_edit', kwargs={'post_id': cls.post.id}
                    ): 'posts/create_post.html',
            reverse('posts:follow_index'): 'posts/follow.html'
        }

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_2 = Client()
        self.authorized_client_2.force_login(self.userSecond)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def check_post(self, post):
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.group, self.post.group)
        self.assertEqual(post.pk, self.post.pk)
        self.assertEqual(post.image, self.post.image)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for reverse_name, template in {
                **self.private_url, **self.public_url}.items():
            with self.subTest(template=template):
                response = self.authorized_client_2.get(reverse_name)
                self.assertTemplateUsed(
                    response, template,
                    f'Неверный шаблон {template} для адреса {reverse_name}')

    def test_post_pages_show_correct_context(self):
        for address in self.public_url:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                context = response.context
                post = (context.get('page_obj')[
                        0] if 'page_obj' in context else context.get('post'))
                self.check_post(post)

    def test_group_list_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}
                    ))
        self.assertEqual(response.context["group"].title,
                         f'{self.group}')
        self.assertEqual(response.context["group"].slug,
                         f'{self.group.slug}')
        self.assertEqual(response.context["group"].description,
                         f'{self.group.description}')

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.userSecond}))
        self.assertEqual(response.context['author'].username,
                         f'{self.post.author}')

    def test_post_create_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:create_post'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_added_correctly(self):
        """Пост при создании добавлен корректно"""
        post = Post.objects.create(
            text='Тестовый текст',
            author=self.user,
            group=self.group,
            image=self.upload)
        response_index = self.authorized_client.get(
            reverse('posts:index'))
        response_group = self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': f'{self.group.slug}'}))
        response_profile = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': f'{self.user.username}'}))
        index = response_index.context['page_obj']
        group = response_group.context['page_obj']
        profile = response_profile.context['page_obj']
        self.assertIn(post, index, 'поста нет на главной')
        self.assertIn(post, group, 'поста нет в профиле')
        self.assertIn(post, profile, 'поста нет в группе')

    def test_post_added_correctly_user2(self):
        """Пост при создании не добавляется другому пользователю"""
        group2 = Group.objects.create(title='Тестовая группа 2',
                                      slug='test_group2')
        posts_count = self.group.posts.count()
        post = Post.objects.create(
            text='Тестовый пост от другого автора',
            author=self.user,
            group=group2)
        response_profile = self.authorized_client.get(
            reverse('posts:profile',
                    args={self.userSecond}))
        group = Post.objects.filter(group=self.group).count()
        profile = response_profile.context['page_obj']
        self.assertEqual(group, posts_count, 'поста нет в другой группе')
        self.assertNotIn(post, profile,
                         'поста нет в группе другого пользователя')

    def test_comment(self):
        post_comments = self.post.comments.count()
        form_data = {'text': 'тестовый комментарий'}
        self.authorized_client.post(f'/posts/{self.post.pk}/comment/',
                                    data=form_data,
                                    follow=True)
        self.assertEqual(self.post.comments.count(), post_comments + 1)
        new_comment = self.post.comments.last()
        self.assertEqual(new_comment.text, form_data['text'])

    def test_cache_index(self):
        """Тест кэширования главной страницы."""
        first = self.authorized_client.get(reverse('posts:index'))
        post = Post.objects.get(pk=self.post.id)
        post.text = 'Измененный текст'
        post.save()
        second = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(first.content, second.content)
        cache.clear()
        third = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(first.content, third.content)


class PaginatorViewsTest(TestCase):
    POSTS_PAGE = 3

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='auth')
        cls.authorized_client = Client()
        cls.group = Group.objects.create(
            title='Заголовок для тестовой группы',
            slug='test_slug',
            description='Тестовое описание')
        Post.objects.bulk_create(
            [
                Post(text=f'Тестовый пост {i}',
                     author=cls.author,
                     group=cls.group
                     ) for i in range(settings.POSTS_ON_PAGE + cls.POSTS_PAGE)
            ]
        )
        cls.tamplates = {
            reverse('posts:index'): 'index',
            reverse('posts:group_list', kwargs={"slug": cls.group.slug}
                    ): 'group_list',
            reverse('posts:profile', kwargs={"username": cls.author}
                    ): 'profile'
        }

    def test_first_page_contains(self):
        for test_url in self.tamplates:
            with self.subTest(test_url=test_url):
                response = self.client.get(test_url)
                self.assertEqual(len(response.context['page_obj']
                                     ), settings.POSTS_ON_PAGE)

    def test_second_page_contains_three_records(self):
        list_urls = {
            reverse('posts:index') + '?page=2': 'index',
            reverse('posts:group_list', kwargs={"slug": "test_slug"}
                    ) + '?page=2': 'group_list',
            reverse('posts:profile', kwargs={"username": "auth"}
                    ) + '?page=2': 'profile'
        }
        for test_url in list_urls.keys():
            with self.subTest(test_url=test_url):
                response = self.client.get(test_url)
                self.assertEqual(len(response.context['page_obj']
                                     ), self.POSTS_PAGE)


class FollowTests(TestCase):
    def setUp(self):
        self.client_auth_follower = Client()
        self.client_auth_following = Client()
        self.user_follower = User.objects.create(username='follower')
        self.user_following = User.objects.create(username='following')
        self.post = Post.objects.create(
            author=self.user_following,
            text='Тестовая запись для тестирования ленты'
        )
        self.client_auth_follower.force_login(self.user_follower)
        self.client_auth_following.force_login(self.user_following)
        self.follow = reverse(
            'posts:profile_follow', kwargs={
                'username': self.user_following.username}
        )
        self.unfollow = reverse('posts:profile_unfollow',
                                kwargs={
                                    'username': self.user_following.username
                                })
        self.follow_index = reverse('posts:follow_index')

    def test_follow(self):
        self.client_auth_follower.get(self.follow)
        self.client_auth_follower.get(self.follow)
        self.assertEqual(Follow.objects.all().count(), 1)

    def test_unfollow(self):
        self.client_auth_follower.get(self.follow)
        self.client_auth_follower.get(self.unfollow)
        self.assertEqual(Follow.objects.all().count(), 0)

    def test_subscription(self):
        """Запись появляется в ленте подписчиков"""
        Follow.objects.create(
            user=self.user_follower,
            author=self.user_following
        )
        response = self.client_auth_follower.get(self.follow_index)
        post_text_0 = response.context['page_obj'][0].text
        self.assertEqual(post_text_0, self.post.text)
        response = self.client_auth_following.get(self.follow_index)
        self.assertNotEqual(response, self.post.text)

    def test_folower_folowing(self):
        self.client_auth_following.get(self.follow)
        self.assertEqual(Follow.objects.all().count(), 0)
