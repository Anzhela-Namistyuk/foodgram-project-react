import csv

from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'import ingredients from csv or json in db'

    def handle(self, *args, **options):
        csv_file = '/app/ingredients.csv'
        with open(csv_file, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f, fieldnames=['name', 'measurement_unit'])
            count = 0
            for row in reader:
                Ingredient.objects.update_or_create(
                    id=count, name=row['name'],
                    measurement_unit=row['measurement_unit']
                )
                count += 1
