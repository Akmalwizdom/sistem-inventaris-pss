# core/models.py
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal

class Category(models.Model):
    name = models.CharField("nama kategori", max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Kategori"
        verbose_name_plural = "Kategori"
        ordering = ['name']

    def __str__(self):
        return self.name


class Supplier(models.Model):
    name = models.CharField("nama supplier", max_length=200)
    phone = models.CharField("telepon", max_length=20)
    address = models.TextField("alamat")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Supplier"
        verbose_name_plural = "Supplier"
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    sku = models.CharField("SKU", max_length=50, unique=True, db_index=True)
    name = models.CharField("nama produk", max_length=200, db_index=True)
    category = models.ForeignKey(
        Category, 
        verbose_name="kategori",
        on_delete=models.RESTRICT,
        related_name='products'
    )
    supplier = models.ForeignKey(
        Supplier,
        verbose_name="supplier",
        on_delete=models.RESTRICT,
        related_name='products'
    )
    purchase_price = models.DecimalField(
        "harga beli",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    selling_price = models.DecimalField(
        "harga jual",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    stock_quantity = models.IntegerField(
        "jumlah stok",
        default=0,
        validators=[MinValueValidator(0)]
    )
    minimum_stock = models.IntegerField(
        "stok minimum",
        default=10,
        validators=[MinValueValidator(0)]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Produk"
        verbose_name_plural = "Produk"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.sku} - {self.name}"


TRANSACTION_TYPES = [
    ('IN', 'Stock In'),
    ('OUT', 'Stock Out'),
]

class StockTransaction(models.Model):
    product = models.ForeignKey(
        Product,
        verbose_name="produk",
        on_delete=models.RESTRICT,
        related_name='transactions'
    )
    transaction_type = models.CharField(
        "tipe transaksi",
        max_length=3,
        choices=TRANSACTION_TYPES
    )
    quantity = models.IntegerField(
        "jumlah",
        validators=[MinValueValidator(1)]
    )
    notes = models.TextField("catatan", blank=True)
    created_by = models.ForeignKey(
        User,
        verbose_name="dibuat oleh",
        on_delete=models.RESTRICT,
        related_name='stock_transactions'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Transaksi Stok"
        verbose_name_plural = "Transaksi Stok"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.product.name} ({self.quantity})"