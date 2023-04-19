from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError

class User(AbstractUser):
    email = models.EmailField(
        max_length=254, 
        blank=False,
        unique=True,
        verbose_name='Адрес электронной почты'
    )
    username = models.CharField(
        max_length=150,
        blank=False,
        unique=True,
        verbose_name='Имя пользователя'
    )
    first_name = models.CharField(
        max_length=150, 
        blank=False, 
        verbose_name='Имя'
    )
    last_name = models.CharField(
        max_length=150,
        blank=False, 
        verbose_name='Фамилия'
    )
    password = models.CharField(
        max_length=150, 
        verbose_name='Пароль'
    )
    
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name' ]

class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following'
    )

    def validate_follow(self):
        if self.user == self.author:
            raise ValidationError('Подписываться на самого себя нельзя.')
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_following',
            )
        ]
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
    
    def __str__(self) -> str:
        return f'{self.user} подписан на {self.author}'
