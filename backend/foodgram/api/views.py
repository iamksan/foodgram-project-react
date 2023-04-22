from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.conf import settings
from djoser.views import UserViewSet as DjUserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from .filters import IngredientFilter, RecipeFilter
from users.models import Follow
from .pagination import CustomPagination
from .permissions import AuthorOrReadOnly
from .serializers import (FavoriteSerializer, IngredientSerializer,
                          RecipeReadSerializer,
                          RecipeWriteSerializer, ShoppingCartSerializer,
                          TagSerializer)

User = get_user_model()


class UserViewSet(DjUserViewSet):
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.action == 'subscribe':
            return settings.SERIALIZERS.subscribe
        elif self.action == 'subscriptions':
            return settings.SERIALIZERS.subscriptions
        return super().get_serializer_class()

    @action(methods=['post', 'delete'], detail=True)
    def subscribe(self, request, id):
        author = get_object_or_404(User, id=id)
        current_user = request.user
        if request.method == 'POST':
            serializer = self.get_serializer(
                data={'author': author.id, 'user': current_user.id},
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            Follow.objects.filter(
                user=current_user,
                author=author
            ).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['get'], detail=False)
    def subscriptions(self, request):
        pages = self.paginate_queryset(
            User.objects.filter(following__user=request.user)
        )
        serializer = self.get_serializer(
            pages,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)


class RecipeViewSet(viewsets.ModelViewSet):
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    permission_classes = (AuthorOrReadOnly,)

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return (
                Recipe.objects.add_favorite_cart(self.request.user)
                .prefetch_related('tags', 'author', 'ingredients')
            )

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeReadSerializer
        return RecipeWriteSerializer

    @action(
        methods=['get'],
        detail=False,
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        current_user = request.user
        if not current_user.shopping_cart.exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)

        ingredients = (
            Ingredient.objects.filter(
                recipes__shopping_cart__user=current_user
            ).annotate(amount=Sum('recipe__amount')).
            values_list('name', 'amount', 'measurement_unit')
        )
        cart = 'Список покупок\n\n'
        for item in ingredients:
            cart += ' '.join(map(str, item)) + '\n'

        return FileResponse(
            cart,
            content_type='text/plain',
            as_attachment=True,
            status=status.HTTP_200_OK
        )


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = None
