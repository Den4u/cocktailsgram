from django.core.management import BaseCommand
import csv
from django.conf import settings
import os

from recipes.models import Ingredient


DATA_ROOT = os.path.join(settings.BASE_DIR, 'data')


class Command(BaseCommand):
    """Выгрузка csv-ингредиентов."""

    def add_arguments(self, parser):
        parser.add_argument(
            'csv_file',
            default='ingredients.csv',
            type=str)

    def handle(self, *args, **options):

        csv_file = options['csv_file']
        ingredients_list = []
        with open(os.path.join(DATA_ROOT, csv_file),
                  'r', encoding="utf-8") as f:
            reader = csv.reader(f, delimiter=',')
            for row in reader:
                name, measurement_unit = row
                ingredient = Ingredient(
                    name=name,
                    measurement_unit=measurement_unit)
                ingredients_list.append(ingredient)
        Ingredient.objects.bulk_create(ingredients_list)
