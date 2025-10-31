# core/management/commands/seed_data.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db.models import F
from core.models import Category, Supplier, Product, StockTransaction
from decimal import Decimal
import random
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Seed database with sample data for InventoryPro'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            StockTransaction.objects.all().delete()
            Product.objects.all().delete()
            Supplier.objects.all().delete()
            Category.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('✓ Data cleared'))

        # Create superuser if not exists
        self.stdout.write('Creating users...')
        user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@inventorypro.com',
                'is_superuser': True,
                'is_staff': True
            }
        )
        if created:
            user.set_password('admin123')
            user.save()
            self.stdout.write(self.style.SUCCESS('✓ Admin user created'))
        else:
            self.stdout.write('✓ Admin user exists')

        # Additional users for transactions
        staff_users = []
        for i in range(3):
            staff, created = User.objects.get_or_create(
                username=f'staff{i+1}',
                defaults={
                    'email': f'staff{i+1}@inventorypro.com',
                    'is_staff': True
                }
            )
            if created:
                staff.set_password('staff123')
                staff.save()
            staff_users.append(staff)

        # Create Categories
        self.stdout.write('Creating categories...')
        categories_data = [
            'Elektronik',
            'Fashion & Pakaian',
            'Makanan & Minuman',
            'Alat Tulis & Kantor',
            'Kesehatan & Kecantikan',
            'Rumah Tangga',
            'Olahraga & Outdoor',
            'Mainan & Hobi',
        ]
        
        categories = []
        for cat_name in categories_data:
            cat, created = Category.objects.get_or_create(name=cat_name)
            categories.append(cat)
            if created:
                self.stdout.write(f'  ✓ Created: {cat_name}')

        # Create Suppliers
        self.stdout.write('Creating suppliers...')
        suppliers_data = [
            {
                'name': 'PT Elektronik Sejahtera',
                'phone': '021-1234567',
                'address': 'Jl. Sudirman No. 123, Jakarta Pusat'
            },
            {
                'name': 'CV Fashion Modern',
                'phone': '021-2345678',
                'address': 'Jl. Thamrin No. 45, Jakarta Pusat'
            },
            {
                'name': 'Toko Grosir Makmur',
                'phone': '021-3456789',
                'address': 'Jl. Mangga Dua No. 78, Jakarta Utara'
            },
            {
                'name': 'Supplier Alat Kantor',
                'phone': '021-4567890',
                'address': 'Jl. Gatot Subroto No. 90, Jakarta Selatan'
            },
            {
                'name': 'Distributor Kesehatan',
                'phone': '021-5678901',
                'address': 'Jl. Kuningan No. 12, Jakarta Selatan'
            },
        ]
        
        suppliers = []
        for sup_data in suppliers_data:
            sup, created = Supplier.objects.get_or_create(
                name=sup_data['name'],
                defaults={
                    'phone': sup_data['phone'],
                    'address': sup_data['address']
                }
            )
            suppliers.append(sup)
            if created:
                self.stdout.write(f'  ✓ Created: {sup_data["name"]}')

        # Create Products
        self.stdout.write('Creating products...')
        products_data = [
            # Elektronik
            {
                'name': 'Laptop ASUS ROG',
                'category': 'Elektronik',
                'supplier': 'PT Elektronik Sejahtera',
                'purchase_price': 12000000,
                'selling_price': 15000000,
                'stock_quantity': 15,
                'minimum_stock': 5
            },
            {
                'name': 'Mouse Logitech MX Master',
                'category': 'Elektronik',
                'supplier': 'PT Elektronik Sejahtera',
                'purchase_price': 800000,
                'selling_price': 1100000,
                'stock_quantity': 45,
                'minimum_stock': 20
            },
            {
                'name': 'Keyboard Mechanical RGB',
                'category': 'Elektronik',
                'supplier': 'PT Elektronik Sejahtera',
                'purchase_price': 600000,
                'selling_price': 850000,
                'stock_quantity': 8,  # Low stock
                'minimum_stock': 10
            },
            {
                'name': 'Monitor LG 27 inch',
                'category': 'Elektronik',
                'supplier': 'PT Elektronik Sejahtera',
                'purchase_price': 2500000,
                'selling_price': 3200000,
                'stock_quantity': 0,  # Out of stock
                'minimum_stock': 5
            },
            {
                'name': 'Webcam HD 1080p',
                'category': 'Elektronik',
                'supplier': 'PT Elektronik Sejahtera',
                'purchase_price': 450000,
                'selling_price': 650000,
                'stock_quantity': 25,
                'minimum_stock': 15
            },
            
            # Fashion
            {
                'name': 'Kemeja Formal Pria',
                'category': 'Fashion & Pakaian',
                'supplier': 'CV Fashion Modern',
                'purchase_price': 150000,
                'selling_price': 250000,
                'stock_quantity': 100,
                'minimum_stock': 30
            },
            {
                'name': 'Celana Jeans Wanita',
                'category': 'Fashion & Pakaian',
                'supplier': 'CV Fashion Modern',
                'purchase_price': 180000,
                'selling_price': 300000,
                'stock_quantity': 75,
                'minimum_stock': 40
            },
            {
                'name': 'Jaket Hoodie Unisex',
                'category': 'Fashion & Pakaian',
                'supplier': 'CV Fashion Modern',
                'purchase_price': 200000,
                'selling_price': 350000,
                'stock_quantity': 12,  # Low stock
                'minimum_stock': 20
            },
            {
                'name': 'Sepatu Sneakers Sport',
                'category': 'Fashion & Pakaian',
                'supplier': 'CV Fashion Modern',
                'purchase_price': 350000,
                'selling_price': 550000,
                'stock_quantity': 50,
                'minimum_stock': 25
            },
            
            # Makanan & Minuman
            {
                'name': 'Kopi Arabica Premium 1kg',
                'category': 'Makanan & Minuman',
                'supplier': 'Toko Grosir Makmur',
                'purchase_price': 120000,
                'selling_price': 180000,
                'stock_quantity': 200,
                'minimum_stock': 50
            },
            {
                'name': 'Teh Hijau Organik Box',
                'category': 'Makanan & Minuman',
                'supplier': 'Toko Grosir Makmur',
                'purchase_price': 45000,
                'selling_price': 75000,
                'stock_quantity': 150,
                'minimum_stock': 60
            },
            {
                'name': 'Mie Instan Box (isi 40)',
                'category': 'Makanan & Minuman',
                'supplier': 'Toko Grosir Makmur',
                'purchase_price': 95000,
                'selling_price': 125000,
                'stock_quantity': 8,  # Low stock
                'minimum_stock': 20
            },
            {
                'name': 'Susu UHT Kotak (1 dus)',
                'category': 'Makanan & Minuman',
                'supplier': 'Toko Grosir Makmur',
                'purchase_price': 85000,
                'selling_price': 115000,
                'stock_quantity': 0,  # Out of stock
                'minimum_stock': 30
            },
            
            # Alat Tulis
            {
                'name': 'Pulpen Gel Hitam (box 50)',
                'category': 'Alat Tulis & Kantor',
                'supplier': 'Supplier Alat Kantor',
                'purchase_price': 75000,
                'selling_price': 110000,
                'stock_quantity': 80,
                'minimum_stock': 40
            },
            {
                'name': 'Buku Tulis 100 Lembar',
                'category': 'Alat Tulis & Kantor',
                'supplier': 'Supplier Alat Kantor',
                'purchase_price': 8000,
                'selling_price': 15000,
                'stock_quantity': 500,
                'minimum_stock': 200
            },
            {
                'name': 'Spidol Whiteboard Set',
                'category': 'Alat Tulis & Kantor',
                'supplier': 'Supplier Alat Kantor',
                'purchase_price': 35000,
                'selling_price': 55000,
                'stock_quantity': 5,  # Low stock
                'minimum_stock': 15
            },
            {
                'name': 'Kertas A4 (1 Rim)',
                'category': 'Alat Tulis & Kantor',
                'supplier': 'Supplier Alat Kantor',
                'purchase_price': 40000,
                'selling_price': 60000,
                'stock_quantity': 120,
                'minimum_stock': 50
            },
            
            # Kesehatan & Kecantikan
            {
                'name': 'Masker Wajah N95 (box 50)',
                'category': 'Kesehatan & Kecantikan',
                'supplier': 'Distributor Kesehatan',
                'purchase_price': 180000,
                'selling_price': 250000,
                'stock_quantity': 90,
                'minimum_stock': 40
            },
            {
                'name': 'Hand Sanitizer 500ml',
                'category': 'Kesehatan & Kecantikan',
                'supplier': 'Distributor Kesehatan',
                'purchase_price': 35000,
                'selling_price': 55000,
                'stock_quantity': 3,  # Low stock
                'minimum_stock': 20
            },
            {
                'name': 'Vitamin C 1000mg (isi 30)',
                'category': 'Kesehatan & Kecantikan',
                'supplier': 'Distributor Kesehatan',
                'purchase_price': 65000,
                'selling_price': 95000,
                'stock_quantity': 150,
                'minimum_stock': 60
            },
            {
                'name': 'Sabun Mandi Cair 500ml',
                'category': 'Kesehatan & Kecantikan',
                'supplier': 'Distributor Kesehatan',
                'purchase_price': 25000,
                'selling_price': 42000,
                'stock_quantity': 200,
                'minimum_stock': 80
            },
            
            # Rumah Tangga
            {
                'name': 'Sapu Lantai Ijuk',
                'category': 'Rumah Tangga',
                'supplier': 'Toko Grosir Makmur',
                'purchase_price': 15000,
                'selling_price': 25000,
                'stock_quantity': 60,
                'minimum_stock': 30
            },
            {
                'name': 'Pel Microfiber + Tongkat',
                'category': 'Rumah Tangga',
                'supplier': 'Toko Grosir Makmur',
                'purchase_price': 45000,
                'selling_price': 75000,
                'stock_quantity': 35,
                'minimum_stock': 20
            },
            {
                'name': 'Ember Plastik 20 Liter',
                'category': 'Rumah Tangga',
                'supplier': 'Toko Grosir Makmur',
                'purchase_price': 25000,
                'selling_price': 40000,
                'stock_quantity': 7,  # Low stock
                'minimum_stock': 15
            },
            
            # Olahraga
            {
                'name': 'Matras Yoga Premium',
                'category': 'Olahraga & Outdoor',
                'supplier': 'CV Fashion Modern',
                'purchase_price': 150000,
                'selling_price': 250000,
                'stock_quantity': 40,
                'minimum_stock': 15
            },
            {
                'name': 'Dumbbell 5kg (sepasang)',
                'category': 'Olahraga & Outdoor',
                'supplier': 'CV Fashion Modern',
                'purchase_price': 180000,
                'selling_price': 280000,
                'stock_quantity': 25,
                'minimum_stock': 10
            },
            {
                'name': 'Bola Futsal Original',
                'category': 'Olahraga & Outdoor',
                'supplier': 'CV Fashion Modern',
                'purchase_price': 250000,
                'selling_price': 380000,
                'stock_quantity': 2,  # Low stock
                'minimum_stock': 8
            },
        ]
        
        products = []
        for idx, prod_data in enumerate(products_data, start=1):
            category = Category.objects.get(name=prod_data['category'])
            supplier = Supplier.objects.get(name=prod_data['supplier'])
            
            sku = f'PRD-{category.name[:3].upper()}-{idx:04d}'
            
            prod, created = Product.objects.get_or_create(
                sku=sku,
                defaults={
                    'name': prod_data['name'],
                    'category': category,
                    'supplier': supplier,
                    'purchase_price': Decimal(prod_data['purchase_price']),
                    'selling_price': Decimal(prod_data['selling_price']),
                    'stock_quantity': prod_data['stock_quantity'],
                    'minimum_stock': prod_data['minimum_stock']
                }
            )
            products.append(prod)
            if created:
                status = '🔴 OUT' if prod.stock_quantity == 0 else '🟡 LOW' if prod.is_low_stock else '🟢 OK'
                self.stdout.write(f'  ✓ {status} {prod.name} (Stock: {prod.stock_quantity})')

        # Create Stock Transactions
        self.stdout.write('Creating stock transactions...')
        
        transaction_count = 0
        for product in products:
            # Create initial stock IN transactions (masa lalu)
            num_transactions = random.randint(3, 8)
            
            for i in range(num_transactions):
                days_ago = random.randint(1, 90)
                trans_date = timezone.now() - timedelta(days=days_ago)
                
                # Randomly decide if IN or OUT
                trans_type = random.choices(['IN', 'OUT'], weights=[0.6, 0.4])[0]
                
                if trans_type == 'IN':
                    quantity = random.randint(10, 100)
                    notes = random.choice([
                        'Pembelian dari supplier',
                        'Restocking bulanan',
                        'Order tambahan',
                        'Pembelian reguler'
                    ])
                else:  # OUT
                    quantity = random.randint(5, 30)
                    notes = random.choice([
                        'Penjualan ke customer',
                        'Order online',
                        'Penjualan retail',
                        'Pengiriman ke cabang'
                    ])
                
                trans = StockTransaction.objects.create(
                    product=product,
                    transaction_type=trans_type,
                    quantity=quantity,
                    notes=notes,
                    created_by=random.choice(staff_users),
                )
                trans.created_at = trans_date
                trans.save()
                
                transaction_count += 1

        self.stdout.write(self.style.SUCCESS(f'✓ Created {transaction_count} transactions'))

        # Summary
        self.stdout.write(' ' + '='*50)
        self.stdout.write(self.style.SUCCESS('DATABASE SEEDING COMPLETED!'))
        self.stdout.write('='*50)
        self.stdout.write(f'✓ Categories: {Category.objects.count()}')
        self.stdout.write(f'✓ Suppliers: {Supplier.objects.count()}')
        self.stdout.write(f'✓ Products: {Product.objects.count()}')
        self.stdout.write(f'✓ Transactions: {StockTransaction.objects.count()}')
        self.stdout.write(f'✓ Users: {User.objects.count()}')
        
        # Low stock warning
        low_stock = Product.objects.filter(stock_quantity__lte=F('minimum_stock'))
        self.stdout.write(' ' + '-'*50)
        self.stdout.write(self.style.WARNING(f'⚠️  {low_stock.count()} products have low stock!'))
        
        # Login info
        self.stdout.write(' ' + '-'*50)
        self.stdout.write(self.style.SUCCESS('LOGIN CREDENTIALS:'))
        self.stdout.write('Admin: admin / admin123')
        self.stdout.write('Staff: staff1, staff2, staff3 / staff123')
        self.stdout.write('-'*50)