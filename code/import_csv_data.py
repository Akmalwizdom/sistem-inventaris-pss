# code/import_csv_data.py
import os
import csv
from decimal import Decimal
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'simplelms.settings')
django.setup()

from core.models import Category, Supplier, Product

CSV_FOLDER = os.path.join(os.path.dirname(__file__), 'csv_data')


def import_categories():
    file_path = os.path.join(CSV_FOLDER, 'categories.csv')
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            name = row['name'].strip()
            Category.objects.get_or_create(name=name)
    print("✅ Categories imported successfully!")


def import_suppliers():
    file_path = os.path.join(CSV_FOLDER, 'suppliers.csv')
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            Supplier.objects.get_or_create(
                name=row['name'].strip(),
                defaults={
                    'phone': row.get('phone', ''),
                    'address': row.get('address', ''),
                }
            )
    print("✅ Suppliers imported successfully!")


def import_products():
    file_path = os.path.join(CSV_FOLDER, 'products.csv')
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            category, _ = Category.objects.get_or_create(name=row['category'])
            supplier, _ = Supplier.objects.get_or_create(name=row['supplier'])
            Product.objects.update_or_create(
                sku=row['sku'],
                defaults={
                    'name': row['name'],
                    'category': category,
                    'supplier': supplier,
                    'purchase_price': Decimal(row['purchase_price']),
                    'selling_price': Decimal(row['selling_price']),
                    'stock_quantity': int(row['stock_quantity']),
                    'minimum_stock': int(row['minimum_stock']),
                },
            )
    print("✅ Products imported successfully!")


def main():
    import_categories()
    import_suppliers()
    import_products()


if __name__ == '__main__':
    main()