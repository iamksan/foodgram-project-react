import json

from django.core.management import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('args', nargs='*')

    def handle(self, *args, **options):
        with open(
                'ingredients.json',
                encoding='utf-8') as f:
                ingredients = json.load(f)

        for ingredient in ingredients:
            name = ingredient['name']
            measurement_unit = ingredient['measurement_unit']
            Ingredient.objects.create(
                name=name,
                measurement_unit=measurement_unit
            )