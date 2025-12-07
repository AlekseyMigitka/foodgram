import csv
import json
from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Load ingredients from JSON or CSV'

    def add_arguments(self, parser):
        parser.add_argument(
            '--format',
            choices=['json', 'csv'],
            default='json',
            help='Input data format'
        )

        parser.add_argument(
            '--path',
            default='data/ingredients.json',
            help='Path to file'
        )

    def handle(self, *args, **options):
        file_format = options['format']
        path = options['path']

        if file_format == 'json':
            with open(path, encoding='utf-8') as f:
                data = json.load(f)

        else:  # CSV
            with open(path, encoding='utf-8') as f:
                reader = csv.reader(f)
                data = [
                    {'name': row[0], 'measurement_unit': row[1]}
                    for row in reader
                ]

        count = 0
        for item in data:
            Ingredient.objects.get_or_create(
                name=item['name'],
                measurement_unit=item['measurement_unit']
            )
            count += 1

        self.stdout.write(self.style.SUCCESS(f'Loaded {count} ingredients'))
