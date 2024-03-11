from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator


class User(AbstractUser):
    """Модель пользователя."""

    username = models.CharField('username', max_length=150,
                                unique=True,
                                validators=(UnicodeUsernameValidator(),))
    first_name = models.CharField('name', max_length=150)
    last_name = models.CharField('surname', max_length=150)
    email = models.EmailField('email', max_length=254, unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('id', 'username', 'first_name', 'last_name',)

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f'Username: {self.username}, Email: {self.email}.'


class Subscribe(models.Model):
    """Модель подписки."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'author'),
                name='unique_user_author'
            ),
        )

    def __str__(self):
        return f'{self.user} подписан на {self.author}.'
