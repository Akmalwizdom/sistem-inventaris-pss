# core/admin.py
from django.contrib import admin
from django.db.models import Count
from .models import Product, Category, Supplier, StockTransaction

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'product_count', 'created_at')
    search_fields = ('name',)
    readonly_fields = ('created_at', 'updated_at')
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        # OPTIMASI: Annotate product count
        queryset = queryset.annotate(
            _product_count=Count('products', distinct=True)
        )
        return queryset
    
    def product_count(self, obj):
        return obj._product_count
    product_count.admin_order_field = '_product_count'
    product_count.short_description = 'Jumlah Produk'


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'product_count', 'created_at')
    search_fields = ('name', 'phone')
    readonly_fields = ('created_at', 'updated_at')
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        # OPTIMASI: Annotate product count
        queryset = queryset.annotate(
            _product_count=Count('products', distinct=True)
        )
        return queryset
    
    def product_count(self, obj):
        return obj._product_count
    product_count.admin_order_field = '_product_count'
    product_count.short_description = 'Jumlah Produk'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'sku', 'name', 'category', 'supplier', 
        'stock_quantity', 'stock_status', 'purchase_price', 
        'selling_price', 'created_at'
    )
    list_filter = ('category', 'supplier', 'created_at')
    search_fields = ('sku', 'name')
    readonly_fields = ('created_at', 'updated_at', 'stock_value', 'profit_margin')
    
    fieldsets = (
        ('Informasi Dasar', {
            'fields': ('sku', 'name', 'category', 'supplier')
        }),
        ('Harga', {
            'fields': ('purchase_price', 'selling_price', 'profit_margin')
        }),
        ('Stok', {
            'fields': ('stock_quantity', 'minimum_stock', 'stock_value')
        }),
        ('Timestamp', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        # OPTIMASI: select_related untuk foreign keys
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('category', 'supplier')
        return queryset
    
    def stock_status(self, obj):
        if obj.is_low_stock:
            return '🔴 Low Stock'
        return '✅ OK'
    stock_status.short_description = 'Status Stok'


@admin.register(StockTransaction)
class StockTransactionAdmin(admin.ModelAdmin):
    list_display = (
        'product', 'transaction_type', 'quantity', 
        'created_by', 'created_at'
    )
    list_filter = ('transaction_type', 'created_at')
    search_fields = ('product__name', 'product__sku', 'notes')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Informasi Transaksi', {
            'fields': ('product', 'transaction_type', 'quantity')
        }),
        ('Detail', {
            'fields': ('notes', 'created_by', 'created_at')
        }),
    )
    
    def get_queryset(self, request):
        # OPTIMASI: select_related untuk foreign keys
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('product', 'product__category', 'created_by')
        return queryset
    
    def save_model(self, request, obj, form, change):
        if not change:  # Hanya untuk create baru
            obj.created_by = request.user
        super().save_model(request, obj, form, change)