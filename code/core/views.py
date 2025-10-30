# core/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.db.models import Q, F, Sum, Count, Prefetch
from django.db import transaction
from django.contrib import messages
from django.utils import timezone
from .models import Product, Category, Supplier, StockTransaction
from .forms import (
    ProductForm, CategoryForm, SupplierForm, 
    StockTransactionForm, ProductSearchForm, DateRangeForm
)


# ============= DASHBOARD =============
@login_required
def dashboard(request):
    """Dashboard dengan statistik dan optimasi ORM"""
    today = timezone.now().date()
    
    # OPTIMASI: Aggregate queries untuk statistik
    stats = {
        'total_products': Product.objects.count(),
        'total_stock_value': Product.objects.aggregate(
            total=Sum(F('stock_quantity') * F('purchase_price'))
        )['total'] or 0,
        'low_stock_count': Product.objects.filter(
            stock_quantity__lte=F('minimum_stock')
        ).count(),
        'today_transactions': StockTransaction.objects.filter(
            created_at__date=today
        ).count(),
    }
    
    # OPTIMASI: select_related untuk produk low stock
    low_stock_products = Product.objects.select_related(
        'category', 'supplier'
    ).filter(
        stock_quantity__lte=F('minimum_stock')
    ).order_by('stock_quantity')[:5]
    
    # Transaksi terbaru dengan optimasi
    recent_transactions = StockTransaction.objects.select_related(
        'product', 'created_by'
    ).order_by('-created_at')[:5]
    
    context = {
        'stats': stats,
        'low_stock_products': low_stock_products,
        'recent_transactions': recent_transactions,
    }
    
    return render(request, 'inventory/dashboard.html', context)


# ============= PRODUCTS =============
class ProductListView(LoginRequiredMixin, ListView):
    model = Product
    template_name = 'inventory/product_list.html'
    context_object_name = 'products'
    paginate_by = 20
    
    def get_queryset(self):
        # OPTIMASI: select_related untuk foreign keys
        queryset = Product.objects.select_related(
            'category', 'supplier'
        )
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(sku__icontains=search)
            )
        
        # Filter by category
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category_id=category)
        
        # Filter by supplier
        supplier = self.request.GET.get('supplier')
        if supplier:
            queryset = queryset.filter(supplier_id=supplier)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = ProductSearchForm(self.request.GET)
        return context


class ProductDetailView(LoginRequiredMixin, DetailView):
    model = Product
    template_name = 'inventory/product_detail.html'
    context_object_name = 'product'
    
    def get_object(self):
        # OPTIMASI: prefetch last 10 transactions
        return Product.objects.select_related(
            'category', 'supplier'
        ).prefetch_related(
            Prefetch(
                'transactions',
                queryset=StockTransaction.objects.select_related(
                    'created_by'
                ).order_by('-created_at')[:10],
                to_attr='recent_transactions'
            )
        ).get(pk=self.kwargs['pk'])


class ProductCreateView(LoginRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'inventory/product_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Produk berhasil ditambahkan!')
        return super().form_valid(form)


class ProductUpdateView(LoginRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'inventory/product_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Produk berhasil diupdate!')
        return super().form_valid(form)


class ProductDeleteView(LoginRequiredMixin, DeleteView):
    model = Product
    template_name = 'inventory/product_confirm_delete.html'
    success_url = reverse_lazy('product_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Produk berhasil dihapus!')
        return super().delete(request, *args, **kwargs)


# ============= TRANSACTIONS =============
class TransactionListView(LoginRequiredMixin, ListView):
    model = StockTransaction
    template_name = 'inventory/transaction_list.html'
    context_object_name = 'transactions'
    paginate_by = 50
    
    def get_queryset(self):
        # OPTIMASI: select_related untuk menghindari N+1
        queryset = StockTransaction.objects.select_related(
            'product',
            'product__category',
            'created_by'
        )
        
        # Filter by date range
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        
        if start_date and end_date:
            queryset = queryset.filter(
                created_at__date__range=[start_date, end_date]
            )
        
        # Filter by type
        trans_type = self.request.GET.get('type')
        if trans_type:
            queryset = queryset.filter(transaction_type=trans_type)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['date_form'] = DateRangeForm(self.request.GET)
        return context


class TransactionCreateView(LoginRequiredMixin, CreateView):
    model = StockTransaction
    form_class = StockTransactionForm
    template_name = 'inventory/transaction_form.html'
    
    @transaction.atomic
    def form_valid(self, form):
        # OPTIMASI: select_for_update untuk prevent race condition
        product = Product.objects.select_for_update().get(
            pk=form.cleaned_data['product'].pk
        )
        
        quantity = form.cleaned_data['quantity']
        trans_type = form.cleaned_data['transaction_type']
        
        # Update stock
        if trans_type == 'IN':
            product.stock_quantity += quantity
            messages.success(
                self.request, 
                f'Stock IN berhasil! Stok {product.name} sekarang: {product.stock_quantity}'
            )
        else:  # OUT
            product.stock_quantity -= quantity
            messages.success(
                self.request, 
                f'Stock OUT berhasil! Stok {product.name} sekarang: {product.stock_quantity}'
            )
            
            # Warning jika low stock
            if product.is_low_stock:
                messages.warning(
                    self.request,
                    f'Peringatan: Stok {product.name} sudah mencapai batas minimum!'
                )
        
        product.save(update_fields=['stock_quantity'])
        
        # Save transaction
        form.instance.created_by = self.request.user
        
        return super().form_valid(form)


# ============= CATEGORIES =============
class CategoryListView(LoginRequiredMixin, ListView):
    model = Category
    template_name = 'inventory/category_list.html'
    context_object_name = 'categories'
    
    def get_queryset(self):
        # OPTIMASI: annotate product count
        return Category.objects.annotate(
            product_count=Count('products')
        )


class CategoryCreateView(LoginRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'inventory/category_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Kategori berhasil ditambahkan!')
        return super().form_valid(form)


class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = 'inventory/category_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Kategori berhasil diupdate!')
        return super().form_valid(form)


class CategoryDeleteView(LoginRequiredMixin, DeleteView):
    model = Category
    template_name = 'inventory/category_confirm_delete.html'
    success_url = reverse_lazy('category_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Kategori berhasil dihapus!')
        return super().delete(request, *args, **kwargs)


# ============= SUPPLIERS =============
class SupplierListView(LoginRequiredMixin, ListView):
    model = Supplier
    template_name = 'inventory/supplier_list.html'
    context_object_name = 'suppliers'
    
    def get_queryset(self):
        # OPTIMASI: annotate product count
        return Supplier.objects.annotate(
            product_count=Count('products')
        )


class SupplierCreateView(LoginRequiredMixin, CreateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'inventory/supplier_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Supplier berhasil ditambahkan!')
        return super().form_valid(form)


class SupplierUpdateView(LoginRequiredMixin, UpdateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'inventory/supplier_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Supplier berhasil diupdate!')
        return super().form_valid(form)


class SupplierDeleteView(LoginRequiredMixin, DeleteView):
    model = Supplier
    template_name = 'inventory/supplier_confirm_delete.html'
    success_url = reverse_lazy('supplier_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Supplier berhasil dihapus!')
        return super().delete(request, *args, **kwargs)


# ============= REPORTS =============
@login_required
def stock_report(request):
    """Laporan stok dengan optimasi ORM"""
    # OPTIMASI: select_related + annotate
    products = Product.objects.select_related(
        'category', 'supplier'
    ).annotate(
        stock_value=F('stock_quantity') * F('purchase_price')
    )
    
    # Filter by category
    category = request.GET.get('category')
    if category:
        products = products.filter(category_id=category)
    
    # Summary statistics
    summary = products.aggregate(
        total_items=Count('id'),
        total_value=Sum('stock_value')
    )
    
    context = {
        'products': products,
        'summary': summary,
        'categories': Category.objects.all(),
    }
    
    return render(request, 'inventory/reports/stock_report.html', context)


@login_required
def low_stock_report(request):
    """Laporan produk dengan stok rendah"""
    products = Product.objects.select_related(
        'category', 'supplier'
    ).filter(
        stock_quantity__lte=F('minimum_stock')
    ).order_by('stock_quantity')
    
    context = {
        'products': products,
        'total_low_stock': products.count(),
    }
    
    return render(request, 'inventory/reports/low_stock_report.html', context)


@login_required
def transaction_report(request):
    """Laporan transaksi dengan filter date range"""
    # OPTIMASI: select_related
    transactions = StockTransaction.objects.select_related(
        'product', 'product__category', 'created_by'
    )
    
    # Filter by date
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if start_date and end_date:
        transactions = transactions.filter(
            created_at__date__range=[start_date, end_date]
        )
    
    # Summary statistics
    summary = transactions.aggregate(
        total_in=Sum('quantity', filter=Q(transaction_type='IN')),
        total_out=Sum('quantity', filter=Q(transaction_type='OUT')),
        total_transactions=Count('id')
    )
    
    context = {
        'transactions': transactions,
        'summary': summary,
        'date_form': DateRangeForm(request.GET),
    }
    
    return render(request, 'inventory/reports/transaction_report.html', context)