# core/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django import forms
from django.db.models import Count
from .models import Product, Category, Supplier, StockTransaction

class CustomUserCreationForm(forms.ModelForm):
    """Form custom untuk membuat user baru dengan help text Indonesia"""
    password1 = forms.CharField(
        label='Kata Sandi',
        widget=forms.PasswordInput,
        help_text='Kata sandi harus memiliki minimal 8 karakter.'
    )
    password2 = forms.CharField(
        label='Konfirmasi Kata Sandi',
        widget=forms.PasswordInput,
        help_text='Masukkan kata sandi yang sama untuk verifikasi.'
    )
    
    class Meta:
        model = User
        fields = ('username', 'email')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ubah help_text dan label untuk username
        self.fields['username'].help_text = 'Wajib. Maksimal 150 karakter. Hanya huruf, angka, dan @/./+/-/_'
        self.fields['username'].label = 'Nama Pengguna'
        self.fields['email'].label = 'Alamat Email'
        self.fields['email'].required = False
    
    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Kata sandi tidak cocok.")
        return password2
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class CustomUserChangeForm(forms.ModelForm):
    """Form custom untuk edit user dengan help text Indonesia"""
    
    class Meta:
        model = User
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ubah help_text dan label
        if 'username' in self.fields:
            self.fields['username'].help_text = 'Wajib. Maksimal 150 karakter. Hanya huruf, angka, dan @/./+/-/_'
            self.fields['username'].label = 'Nama Pengguna'
        if 'email' in self.fields:
            self.fields['email'].label = 'Alamat Email'
        if 'password' in self.fields:
            self.fields['password'].help_text = (
                'Kata sandi tidak disimpan dalam format teks biasa. '
                'Gunakan <a href="../password/">form ini</a> untuk mengubah kata sandi.'
            )


class CustomUserAdmin(BaseUserAdmin):
    """Custom User Admin dengan Bahasa Indonesia tanpa nama depan/belakang"""
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    
    list_display = ('username', 'email', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_active', 'is_superuser', 'date_joined')
    search_fields = ('username', 'email')
    ordering = ('-date_joined',)
    filter_horizontal = ('groups', 'user_permissions')
    
    fieldsets = (
        ('Informasi Akun', {
            'fields': ('username', 'password', 'email')
        }),
        ('Hak Akses & Izin', {
            'fields': ('is_active', 'is_staff', 'is_superuser'),
            'description': 'Atur status dan level akses pengguna'
        }),
        ('Grup & Izin Detail', {
            'fields': ('groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Informasi Waktu', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        ('Buat Pengguna Baru', {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
            'description': 'Isi formulir di bawah ini untuk membuat pengguna baru'
        }),
        ('Hak Akses (Opsional)', {
            'classes': ('collapse',),
            'fields': ('is_staff', 'is_active'),
        }),
    )


# Unregister User model default dan register dengan custom admin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


admin.site.site_header = "InventoryPro Administration"
admin.site.site_title = "InventoryPro Admin Portal"
admin.site.index_title = "Selamat Datang di Dashboard InventoryPro"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'product_count', 'created_at', 'updated_at')
    search_fields = ('name',)
    readonly_fields = ('created_at', 'updated_at')
    list_per_page = 25
    view_on_site = False  
    
    fieldsets = (
        ('Informasi Kategori', {
            'fields': ('name',),
            'description': 'Masukkan informasi kategori produk'
        }),
        ('Informasi Waktu', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
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
    list_display = ('name', 'phone', 'product_count', 'created_at', 'updated_at')
    search_fields = ('name', 'phone', 'address')
    readonly_fields = ('created_at', 'updated_at')
    list_per_page = 25
    view_on_site = False 
    
    fieldsets = (
        ('Informasi Supplier', {
            'fields': ('name', 'phone', 'address'),
            'description': 'Masukkan informasi detail supplier'
        }),
        ('Informasi Waktu', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
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
        'selling_price', 'profit_margin_display', 'created_at'
    )
    list_filter = ('category', 'supplier', 'created_at')
    search_fields = ('sku', 'name', 'category__name', 'supplier__name')
    readonly_fields = ('created_at', 'updated_at', 'stock_value', 'profit_margin')
    list_per_page = 25
    view_on_site = False  
    
    fieldsets = (
        ('Informasi Dasar', {
            'fields': ('sku', 'name', 'category', 'supplier'),
            'description': 'Informasi identitas produk'
        }),
        ('Informasi Harga', {
            'fields': ('purchase_price', 'selling_price', 'profit_margin'),
            'description': 'Informasi harga dan margin keuntungan'
        }),
        ('Manajemen Stok', {
            'fields': ('stock_quantity', 'minimum_stock', 'stock_value'),
            'description': 'Informasi persediaan barang'
        }),
        ('Informasi Waktu', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        # OPTIMASI: select_related untuk foreign keys
        queryset = queryset.select_related('category', 'supplier')
        return queryset

    def stock_status(self, obj):
        if obj.is_low_stock:
            return '🔴 Stok Rendah'
        return '✅ Stok Aman'
    stock_status.short_description = 'Status Stok'
    
    def profit_margin_display(self, obj):
        return f"{obj.profit_margin:.2f}%"
    profit_margin_display.short_description = 'Margin (%)'
    profit_margin_display.admin_order_field = 'selling_price'


@admin.register(StockTransaction)
class StockTransactionAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'product', 'transaction_type_display', 'quantity', 
        'created_by', 'created_at'
    )
    list_filter = ('transaction_type', 'created_at', 'product__category')
    search_fields = ('product__name', 'product__sku', 'notes', 'created_by__username')
    readonly_fields = ('created_at', 'created_by')
    list_per_page = 50
    view_on_site = False  
    
    fieldsets = (
        ('Informasi Transaksi', {
            'fields': ('product', 'transaction_type', 'quantity'),
            'description': 'Detail transaksi stok barang'
        }),
        ('Catatan & Informasi Tambahan', {
            'fields': ('notes',),
        }),
        ('Informasi Sistem', {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        # OPTIMASI: select_related untuk foreign keys
        queryset = super().get_queryset(request)
        queryset = queryset.select_related(
            'product', 
            'product__category', 
            'product__supplier',
            'created_by'
        )
        return queryset
    
    def transaction_type_display(self, obj):
        if obj.transaction_type == 'IN':
            return '📥 Stok Masuk'
        return '📤 Stok Keluar'
    transaction_type_display.short_description = 'Tipe Transaksi'
    transaction_type_display.admin_order_field = 'transaction_type'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Hanya untuk create baru
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def has_delete_permission(self, request, obj=None):
        # Opsional: Batasi penghapusan transaksi untuk audit trail
        return request.user.is_superuser