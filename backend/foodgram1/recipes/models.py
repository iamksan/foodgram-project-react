from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.db.models import Exists, OuterRef

User = get_user_model()


class CustomRecipeManager(models.Manager):
    def add_favorite_cart(self, user):
        return self.annotate(
            is_favorited=Exists(
                Favorite.objects.filter(
                    user=user, recipe__pk=OuterRef('pk')
                )
            ),
            is_in_shopping_cart=Exists(
                ShoppingCart.objects.filter(
                    user=user, recipe__pk=OuterRef('pk')
                )
            ),
        )


class Recipe(models.Model):
    name = models.CharField(
        verbose_name='Название рецепта',
        max_length=200
    )
    author = models.ForeignKey(
        User,
        verbose_name='',
        on_delete=models.CASCADE,
        related_name='recipes'
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации'
    )
    text = models.TextField(
        verbose_name='Описание рецепта'
    )
    image = models.ImageField(
        upload_to='recipe_images/',
        verbose_name='Изображение рецепта'
    )
    ingredients = models.ManyToManyField(
        'Ingredient',
        through='IngredientAmount',
        verbose_name='Ингридиенты рецепта',
        related_name='recipes'
    )
    tags = models.ManyToManyField(
        'Tag',
        verbose_name='Теги рецепта',
        related_name='recipes'
    )
    cooking_time = models.PositiveIntegerField(
        verbose_name='Время приготовления',
        validators=()
    )
    objects = CustomRecipeManager()

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = '-pub_date',
        constraints = (
            models.UniqueConstraint(
                fields=('name', 'author'),
                name='unique_recipe_author'
            ),
        )

    def __str__(self):
        return f'id: {self.pk}, название: {self.name[:30]}'


class Ingredient(models.Model):
    name = models.CharField(max_length=200)
    measurement_unit = models.CharField(max_length=200)

    class Meta:
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Ингридиент'
        constraints = (
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_ingredient'
            ),
        )
        indexes = (models.Index(fields=('name', 'measurement_unit')),)

    def __str__(self):
        return f'{self.name[:30]}, {self.measurement_unit}'


class IngredientAmount(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        related_name='ingredient',
        on_delete=models.CASCADE
    )
    ingredient = models.ForeignKey(
        Ingredient,
        verbose_name='Ингредиент',
        related_name='recipe',
        on_delete=models.CASCADE
    )
    amount = models.PositiveIntegerField(
        verbose_name='Количество',
        validators=(MinValueValidator(1),)
    )

    class Meta:
        verbose_name = 'Ингридиент в рецепте'
        verbose_name_plural = 'Ингридиенты в рецепте'
        constraints = (
            models.UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='unique_ingredient_in_recipe'
            ),
        )


class Tag(models.Model):
    name = models.CharField(
        verbose_name='Название тега',
        max_length=200,
        unique=True
    )
    color = models.CharField(
        verbose_name='Цвет тега',
        max_length=7,
        unique=True,
        validators=(RegexValidator(
            '^#?([0-9a-fA-F]{6}|[0-9a-fA-F]{3})$',
            'Значение не соответствует формату hex'
        ),
        )
    )
    slug = models.SlugField(
        verbose_name='Слаг тега',
        max_length=200,
        unique=True
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name[:30]


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        related_name='favorite',
        on_delete=models.CASCADE,
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        related_name='favorite',
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_user_recipe_favorite'
            ),
        )
        indexes = (models.Index(fields=('recipe',)),)

    def __str__(self):
        return f'{self.user.username[:30]} : {self.recipe.name[:30]}'


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        related_name='shopping_cart',
        on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        related_name='shopping_cart',
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_user_recipe_cart'
            ),
        )
        indexes = (models.Index(fields=('recipe',)),)

    def __str__(self):
        return f'{self.user.username[:30]} : {self.recipe.name[:30]}'
