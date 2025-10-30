# core/forms.py
from django import forms
from .models import Product, Category, Supplier, StockTransaction

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'sku', 'name', 'category', 'supplier', 
            'purchase_price', 'selling_price', 
            'stock_quantity', 'minimum_stock'
        ]
        widgets = {
            'sku': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'PRD001'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nama Produk'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'supplier': forms.Select(attrs={'class': 'form-control'}),
            'purchase_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'selling_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'stock_quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'minimum_stock': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'value': '10'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        selling_price = cleaned_data.get('selling_price')
        purchase_price = cleaned_data.get('purchase_price')
        
        if selling_price and purchase_price:
            if selling_price < purchase_price:
                self.add_error('selling_price', 
                    'Peringatan: Harga jual lebih rendah dari harga beli!')
        
        return cleaned_data


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Nama Kategori'
            }),
        }


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'phone', 'address']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Nama Supplier'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': '08123456789'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3,
                'placeholder': 'Alamat lengkap supplier'
            }),
        }


class StockTransactionForm(forms.ModelForm):
    class Meta:
        model = StockTransaction
        fields = ['product', 'transaction_type', 'quantity', 'notes']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-control'}),
            'transaction_type': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3,
                'placeholder': 'Catatan transaksi (opsional)'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # OPTIMASI: select_related untuk dropdown product
        self.fields['product'].queryset = Product.objects.select_related(
            'category', 'supplier'
        ).all()
        # Custom label dengan stok
        self.fields['product'].label_from_instance = lambda obj: \
            f"{obj.name} (Stok: {obj.stock_quantity})"
    
    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get('product')
        quantity = cleaned_data.get('quantity')
        transaction_type = cleaned_data.get('transaction_type')
        
        if product and quantity and transaction_type == 'OUT':
            if product.stock_quantity < quantity:
                raise forms.ValidationError(
                    f'Stok tidak mencukupi! Stok tersedia: {product.stock_quantity}'
                )
        
        return cleaned_data


class ProductSearchForm(forms.Form):
    """Form untuk search dan filter produk"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Cari nama atau SKU produk...'
        })
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        empty_label="Semua Kategori",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    supplier = forms.ModelChoiceField(
        queryset=Supplier.objects.all(),
        required=False,
        empty_label="Semua Supplier",
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class DateRangeForm(forms.Form):
    """Form untuk filter date range di laporan"""
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )