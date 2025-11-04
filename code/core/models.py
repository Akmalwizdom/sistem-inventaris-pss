# core/models.py
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.urls import reverse
from decimal import Decimal

class Category(models.Model):
    name = models.CharField("Nama Kategori", max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Kategori"
        verbose_name_plural = "Kategori"
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return self.name

    # PERBAIKAN: Hapus get_absolute_url untuk nonaktifkan "View on site"
    # def get_absolute_url(self):
    #     return reverse('category_list')

    # PERBAIKAN: Ubah dari @property menjadi method
    def get_product_count(self):
        """Menghitung jumlah produk dalam kategori"""
        return self.products.count()


class Supplier(models.Model):
    name = models.CharField("Nama Supplier", max_length=200)
    phone = models.CharField("Telepon", max_length=20)
    address = models.TextField("Alamat")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Supplier"
        verbose_name_plural = "Supplier"
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return self.name

    # PERBAIKAN: Hapus get_absolute_url untuk nonaktifkan "View on site"
    # def get_absolute_url(self):
    #     return reverse('supplier_list')

    # PERBAIKAN: Ubah dari @property menjadi method
    def get_product_count(self):
        """Menghitung jumlah produk dari supplier"""
        return self.products.count()


class Product(models.Model):
    sku = models.CharField("SKU", max_length=50, unique=True, db_index=True)
    name = models.CharField("Nama Produk", max_length=200, db_index=True)
    category = models.ForeignKey(
        Category, 
        verbose_name="Kategori",
        on_delete=models.PROTECT,
        related_name='products'
    )
    supplier = models.ForeignKey(
        Supplier,
        verbose_name="Supplier",
        on_delete=models.PROTECT,
        related_name='products'
    )
    
    purchase_price = models.DecimalField(
        "Harga Beli",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        null=False,
        blank=False
    )
    selling_price = models.DecimalField(
        "Harga Jual",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        null=False,
        blank=False
    )
    
    stock_quantity = models.IntegerField(
        "Jumlah Stok",
        default=0,
        validators=[MinValueValidator(0)]
    )
    minimum_stock = models.IntegerField(
        "Stok Minimum",
        default=10,
        validators=[MinValueValidator(0)]
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Produk"
        verbose_name_plural = "Produk"
        ordering = ['name']
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['name']),
            models.Index(fields=['category', 'supplier']),
        ]
    
    def __str__(self):
        return f"{self.sku} - {self.name}"
    
    # PERBAIKAN: Hapus get_absolute_url karena sudah ada di URL
    def get_absolute_url(self):
        return reverse('product_detail', kwargs={'pk': self.pk})
    
    @property
    def is_low_stock(self):
        """Cek apakah stok rendah"""
        return self.stock_quantity <= self.minimum_stock
    
    @property
    def stock_value(self):
        """Hitung nilai total stok"""
        if self.purchase_price is not None and self.purchase_price > 0:
            return self.stock_quantity * self.purchase_price
        return Decimal('0.00')
    
    @property
    def profit_margin(self):
        """Hitung margin keuntungan dalam persen"""
        if self.purchase_price is not None and self.purchase_price > 0:
            return ((self.selling_price - self.purchase_price) /
                    self.purchase_price) * 100
        return 0


class StockTransaction(models.Model):
    TYPES = [
        ('IN', 'Stock In'),
        ('OUT', 'Stock Out'),
    ]
    
    product = models.ForeignKey(
        Product,
        verbose_name="Produk",
        on_delete=models.PROTECT,
        related_name='transactions'
    )
    transaction_type = models.CharField(
        "Tipe Transaksi",
        max_length=3,
        choices=TYPES
    )
    quantity = models.IntegerField(
        "Jumlah",
        validators=[MinValueValidator(1)]
    )
    notes = models.TextField("Catatan", blank=True)
    
    created_by = models.ForeignKey(
        User,
        verbose_name="Dibuat Oleh",
        on_delete=models.PROTECT,
        related_name='stock_transactions'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Transaksi Stok"
        verbose_name_plural = "Transaksi Stok"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['product', '-created_at']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['transaction_type']),
        ]
    
    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.product.name} ({self.quantity})"
    
