from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
User = get_user_model()

class Recipe(models.Model):
    name = models.CharField(
        verbose_name='Рецепт',
        max_length=200
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        related_name='Рецепт',
        on_delete=models.CASCADE
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации'
    )
    text = models.TextField(
        verbose_name='Описание'
    )
    image = models.ImageField(
        upload_to='recipe_images/',
        verbose_name='Мзображение'
    )
    tag = models.ManyToManyField(
        'Tag',
        verbose_name='Тег рецепта',
        related_name='Рецепт'
    )
    ingredients = models.ManyToManyField(
        'Ingredient',
        through='IngredientAmount',
        verbose_name='Ингредиент',
        related_name='Рецепт'
    )
    сooking_time = models.PositiveIntegerField(
        verbose_name='Время приготовления',
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'


class Tag(models.Model):
    name = models.CharField(
        verbose_name='Название тега',
        max_length=200,
        unique=True
    )
    color = models.CharField(
        verbose_name='Цвет тега',
        max_length=7,
        unique=True
    )
    slug = models.SlugField(
        verbose_name='Слаг тега',
        max_length=200,
        unique=True,
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
    
    def __str__(self):
        return self.name[:30]


class Ingredient(models.Model):
    name = models.CharField(
        max_length=200
    )
    measurement_unit = models.CharField(
        max_length=200
    )
    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = (
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_ingredient'
            ),
        )
        indexes = (models.Index(fields=('name', 'measurement_unit')),)

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class IngredientAmount(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        related_name='Ингредиент',
        on_delete=models.CASCADE
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE
    )
    amount = models.PositiveIntegerField(
        verbose_name='Количество',
        validators=[MinValueValidator(1)]
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'
        constraints = (
            models.UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='unique_ingredient_in_recipe'
            ),
        )


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        related_name='Фаворит',
        on_delete=models.CASCADE,
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        related_name='Фаворит',
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'
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
