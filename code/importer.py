# code/importer.py
import os
import sys
import csv
from decimal import Decimal
from random import randint, choice

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'simplelms.settings')

import django
django.setup()

from django.contrib.auth.models import User
from core.models import Category, Supplier, Product, StockTransaction

print("🚀 Starting import process...")

# 1) Create admin user if not exists
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser(
        username='admin',
        email='admin@inventory.com',
        password='admin123'
    )
    print("✅ Admin user created")
else:
    print("ℹ️  Admin user already exists")

# 2) Import Categories from CSV
categories_file = os.path.join(BASE_DIR, 'csv_data', 'categories.csv')
if os.path.exists(categories_file):
    with open(categories_file, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            Category.objects.get_or_create(name=row['name'].strip())
    print("✅ Categories imported from CSV")
else:
    # Fallback to default data
    categories_data = [
        "Elektronik",
        "Pakaian",
        "Makanan & Minuman",
        "Peralatan Rumah Tangga",
        "Alat Tulis",
        "Mainan",
        "Olahraga",
        "Kesehatan",
    ]
    for cat_name in categories_data:
        Category.objects.get_or_create(name=cat_name)
    print("✅ Categories imported from default data")

# 3) Import Suppliers from CSV
suppliers_file = os.path.join(BASE_DIR, 'csv_data', 'suppliers.csv')
if os.path.exists(suppliers_file):
    with open(suppliers_file, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            Supplier.objects.get_or_create(
                name=row['name'].strip(),
                defaults={
                    'phone': row.get('phone', ''),
                    'address': row.get('address', ''),
                }
            )
    print("✅ Suppliers imported from CSV")
else:
    # Fallback to default data
    suppliers_data = [
        {"name": "PT Elektronik Jaya", "phone": "021-1234567", "address": "Jakarta Pusat"},
        {"name": "CV Maju Bersama", "phone": "021-7654321", "address": "Tangerang"},
        {"name": "UD Sumber Rezeki", "phone": "022-1112222", "address": "Bandung"},
        {"name": "PT Distribusi Nusantara", "phone": "031-3334444", "address": "Surabaya"},
        {"name": "Toko Grosir Sentosa", "phone": "024-5556666", "address": "Semarang"},
    ]
    for supplier_data in suppliers_data:
        Supplier.objects.get_or_create(
            name=supplier_data['name'],
            defaults={
                'phone': supplier_data['phone'],
                'address': supplier_data['address']
            }
        )
    print("✅ Suppliers imported from default data")

# 4) Import Products from CSV
products_file = os.path.join(BASE_DIR, 'csv_data', 'products.csv')
if os.path.exists(products_file):
    with open(products_file, newline='', encoding='utf-8') as csvfile:
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
                }
            )
    print("✅ Products imported from CSV")
else:
    # Fallback to default data
    products_data = [
        {"sku": "ELK001", "name": "Laptop ASUS ROG", "category": "Elektronik", "purchase": 8000000, "selling": 10000000, "stock": 15, "min": 5},
        {"sku": "ELK002", "name": "Mouse Logitech", "category": "Elektronik", "purchase": 150000, "selling": 200000, "stock": 50, "min": 10},
        {"sku": "PKN001", "name": "Kaos Polos Hitam", "category": "Pakaian", "purchase": 30000, "selling": 50000, "stock": 100, "min": 20},
        {"sku": "PKN002", "name": "Celana Jeans", "category": "Pakaian", "purchase": 100000, "selling": 150000, "stock": 30, "min": 10},
        {"sku": "MKN001", "name": "Kopi Arabica 1kg", "category": "Makanan & Minuman", "purchase": 80000, "selling": 120000, "stock": 25, "min": 15},
        {"sku": "MKN002", "name": "Teh Melati 500gr", "category": "Makanan & Minuman", "purchase": 35000, "selling": 50000, "stock": 40, "min": 10},
        {"sku": "PRT001", "name": "Panci Stainless 24cm", "category": "Peralatan Rumah Tangga", "purchase": 120000, "selling": 180000, "stock": 20, "min": 5},
        {"sku": "PRT002", "name": "Wajan Teflon", "category": "Peralatan Rumah Tangga", "purchase": 90000, "selling": 130000, "stock": 35, "min": 10},
        {"sku": "ATK001", "name": "Pensil 2B (box)", "category": "Alat Tulis", "purchase": 12000, "selling": 18000, "stock": 80, "min": 20},
        {"sku": "ATK002", "name": "Buku Tulis 50 lembar", "category": "Alat Tulis", "purchase": 3500, "selling": 5000, "stock": 150, "min": 50},
        {"sku": "MYN001", "name": "Lego Classic Set", "category": "Mainan", "purchase": 250000, "selling": 350000, "stock": 12, "min": 5},
        {"sku": "OLG001", "name": "Bola Sepak Nike", "category": "Olahraga", "purchase": 180000, "selling": 250000, "stock": 20, "min": 8},
        {"sku": "KSH001", "name": "Masker Medis (box)", "category": "Kesehatan", "purchase": 45000, "selling": 65000, "stock": 60, "min": 15},
    ]
    
    categories = {cat.name: cat for cat in Category.objects.all()}
    suppliers = list(Supplier.objects.all())
    
    for prod_data in products_data:
        Product.objects.get_or_create(
            sku=prod_data['sku'],
            defaults={
                'name': prod_data['name'],
                'category': categories[prod_data['category']],
                'supplier': choice(suppliers),
                'purchase_price': Decimal(prod_data['purchase']),
                'selling_price': Decimal(prod_data['selling']),
                'stock_quantity': prod_data['stock'],
                'minimum_stock': prod_data['min'],
            }
        )
    print("✅ Products imported from default data")

# 5) Generate sample transactions
admin_user = User.objects.get(username='admin')
products = list(Product.objects.all())

if products:
    transaction_count = 0
    for i in range(30):
        product = choice(products)
        trans_type = choice(['IN', 'OUT'])
        
        if trans_type == 'IN':
            qty = randint(5, 20)
        else:
            qty = randint(1, min(10, max(1, product.stock_quantity)))
        
        StockTransaction.objects.create(
            product=product,
            transaction_type=trans_type,
            quantity=qty,
            notes=f"Sample transaction {i+1}",
            created_by=admin_user
        )
        
        # Update stock
        if trans_type == 'IN':
            product.stock_quantity += qty
        else:
            product.stock_quantity = max(0, product.stock_quantity - qty)
        product.save()
        transaction_count += 1
    
    print(f"✅ {transaction_count} sample transactions created")

print("🎉 Import completed successfully!")
print("📝 Login credentials:")
print("   Username: admin")
print("   Password: admin123")
print("🔗 API Endpoints:")
print("   GET  /products/                    - All products")
print("   GET  /stats/inventory/             - Inventory statistics")
print("   GET  /stats/low-stock/             - Low stock products")
print("   GET  /products/search/?q=laptop    - Search products")