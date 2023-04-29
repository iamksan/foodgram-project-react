from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response

from recipes.models import Recipe


def recipe_m2m_create_delete(request, pk, model, serializer):
    recipe = get_object_or_404(Recipe, id=pk)
    user = request.user
    if request.method == 'POST':
        serializer = serializer(data={'recipe': recipe.id, 'user': user.id})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status.HTTP_201_CREATED)
    elif request.method == 'DELETE':
        model.objects.filter(
            user=user,
            recipe=recipe
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    return Response(status=status.HTTP_400_BAD_REQUEST)
