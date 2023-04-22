from django.contrib.auth import get_user_model
from django.db.models import F
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.fields import SerializerMethodField
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import (
    Favorite, Ingredient, IngredientAmount, Recipe,
    ShoppingCart, Tag
)
from users.models import Follow
from .pagination import CustomPagination

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'password',
            'first_name',
            'last_name',
            'email',
            'is_subscribed',
        )
        read_only_fields = ('is_subscribed',)
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def get_is_subscribed(self, author):
        current_user = self.context['request'].user
        if current_user.is_anonymous or current_user == author:
            return False
        return current_user.follower.filter(author=author).exists()

    def create(self, validated_data):
        return User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
        )


class RecipeShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )
        read_only_fields = ('__all__',)


class UserFollowSerializer(serializers.ModelSerializer):
    recipes = SerializerMethodField()
    recipes_count = SerializerMethodField()
    is_subscribed = SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'is_subscribed',
            'recipes',
            'recipes_count',
        )
        read_only_fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'is_subscribed',
            'recipes',
            'recipes_count',
        )

    def get_recipes_count(self, author):
        return author.recipes.count()

    def get_is_subscribed(self, author):
        request = self.context.get('request')
        current_user = self.context['request'].user
        if request.user.is_anonymos:
            return False
        return current_user.follower.filter(author=author).exists()

    def get_recipes(self, author):
        request = self.context['request']
        recipes = author.recipes.all()[:int(CustomPagination)]
        serializer = RecipeShortSerializer(recipes, many=True, read_only=True)
        return serializer.data


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = (
            'id',
            'name',
            'color',
            'slug',
        )


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = (
            'id',
            'name',
            'measurement_unit',
        )


class RecipeReadSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    ingredients = SerializerMethodField()
    is_favorited = serializers.BooleanField()
    is_in_shopping_cart = serializers.BooleanField()
    author = UserSerializer(read_only=True)

    class Meta:
        model = Recipe
        exclude = ('pub_date',)

    def get_ingredients(self, recipe):
        ingredients = recipe.ingredients.values(
            'id', 'name', 'measurement_unit', amount=F('recipe__amount')
        )
        return ingredients


class IngredientAmountSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient'
    )

    class Meta:
        model = IngredientAmount
        fields = ('id', 'amount')


class RecipeWriteSerializer(RecipeReadSerializer):
    image = Base64ImageField()
    ingredients = IngredientAmountSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'name', 'image',
                  'text', 'cooking_time')

    def validate(self, data):
        request = self.context.get('request')
        ingredients = self.initial_data.get('ingredients')
        ingredients = [ingredient['id'] for ingredient in ingredients]
        amount = ingredients['amount']
        cooking_time = Recipe[cooking_time]
        if len(ingredients) != len(set(ingredients)):
            raise serializers.ValidationError(
                'Ингредиенты должны быть в одном экземпляре'
            )
        if request.method == 'POST' and Recipe.objects.filter(
            author=request.user,
            name=self.initial_data.get('name')
        ).exists():
            raise serializers.ValidationError(
                'У вас уже есть рецепт с таким названием'
            )
        if int(amount) <= 0:
            raise serializers.ValidationError(
                'Вес ингредиента не может быть меньше или равен нулю'
            )
        if int(cooking_time) <= 0:
            raise serializers.ValidationError(
                'Время приготовления не может быть меньше или равен нулю'
            )
        return data
        
         

    def create_ingredients(self, ingredients, recipe):
        IngredientAmount.objects.bulk_create([IngredientAmount(
            ingredient=ingredient['ingredient'],
            recipe=recipe,
            amount=ingredient['amount']
        ) for ingredient in ingredients])

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        current_user = self.context.get('request').user
        recipe = Recipe.objects.create(author=current_user, **validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(ingredients, recipe)
        recipe.save()
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients')
        IngredientAmount.objects.filter(recipe=instance).delete()
        self.create_ingredients(ingredients, instance)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        user = self.context['request'].user
        is_favorited = Favorite.objects.filter(
            user=user,
            recipe=instance
        ).exists()
        is_in_shopping_cart = ShoppingCart.objects.filter(
            user=user,
            recipe=instance
        ).exists()
        setattr(instance, 'is_favorited', is_favorited)
        setattr(instance, 'is_in_shopping_cart', is_in_shopping_cart)
        serializer = RecipeReadSerializer(
            instance,
            context={'request': self.context.get('request')}
        )
        return serializer.data


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = (
            'id',
            'user',
            'recipe',
        )
        validators = (
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('recipe', 'user'),
            ),
        )

    def to_representation(self, instance):
        return RecipeShortSerializer(instance.recipe).data


class ShoppingCartSerializer(FavoriteSerializer):
    class Meta:
        model = ShoppingCart
        fields = (
            'id',
            'user',
            'recipe',
        )
        validators = (
            UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=('recipe', 'user'),
            ),
        )


class FollowSerializer(FavoriteSerializer):
    class Meta:
        model = Follow
        fields = (
            'id',
            'author',
            'user',
        )
        validators = (
            UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=('author', 'user'),
            ),
        )


    def validate_user(self, data):
        user = self.context['request'].user
        if data['author'] == user:
            raise serializers.ValidationError(
                'Вы не можете подписаться на самого себя'
            )

    def to_representation(self, instance):
        return UserFollowSerializer(
            instance.author,
            context=self.context
        ).data
