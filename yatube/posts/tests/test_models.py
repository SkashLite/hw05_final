from django.conf import settings
from django.test import TestCase

from ..models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        self.assertEqual(
            str(self.post), PostModelTest.post.text[
                :settings.SLICE_TEXT
            ],
            f'проверьте что __str__ метод модели {Post.__name__} '
            f'возвращает значение {Post.__name__}'
            f'.text[:{settings.SLICE_TEXT}] '
        )
        self.assertEqual(
            str(self.group), PostModelTest.group.title,
            f"проверьте что __str__ метод модели {Group.__name__}"
            f"возвращает значение из поля 'title'"
        )
