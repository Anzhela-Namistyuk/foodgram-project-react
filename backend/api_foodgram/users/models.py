from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(unique=True, max_length=254)
    first_name = models.CharField(max_length=150)
    password = models.CharField(max_length=150)

    USER = 'user'
    ADMIN = 'admin'
    ANONYMOUS = 'AnonymousUser'
    USER_ROLES = [
        (USER, 'User'),
        (ADMIN, 'Administrator'),
        (ANONYMOUS, 'AnonymousUser')
    ]
    role = models.CharField(
        choices=USER_ROLES,
        default=USER,
        blank=False,
        max_length=16
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['id', 'username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'


class Subscription(models.Model):
    subscriber = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='subscriber',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='subscription_author',
        verbose_name='Автор'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['author', 'subscriber'],
                name='unique_author_subscriber'
            )
        ]

        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f'{self.subscriber} подписан на {self.author}'
