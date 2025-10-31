# core/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q, F, Sum, Count
from django.utils import timezone
from .models import Product, Category, Supplier, StockTransaction

# ============= DASHBOARD (HOMEPAGE) =============
def home(request):
    """Homepage dengan katalog produk dan statistik"""
    # Statistics
    stats = {
        'total_products': Product.objects.count(),
        'total_stock_value': Product.objects.aggregate(
            total=Sum(F('stock_quantity') * F('purchase_price'))
        )['total'] or 0,
        'low_stock_count': Product.objects.filter(
            stock_quantity__lte=F('minimum_stock')
        ).count(),
    }
    
    # Get all products with related data
    products = Product.objects.select_related('category', 'supplier').all()
    
    # Search functionality
    search = request.GET.get('search', '')
    if search:
        products = products.filter(
            Q(name__icontains=search) | 
            Q(sku__icontains=search)
        )
    
    # Filter by category
    category_id = request.GET.get('category', '')
    if category_id:
        products = products.filter(category_id=category_id)
    
    # Filter by supplier
    supplier_id = request.GET.get('supplier', '')
    if supplier_id:
        products = products.filter(supplier_id=supplier_id)
    
    # Filter low stock
    low_stock = request.GET.get('low_stock', '')
    if low_stock == 'true':
        products = products.filter(stock_quantity__lte=F('minimum_stock'))
    
    # Order by name
    products = products.order_by('name')
    
    # Get categories and suppliers for filters
    categories = Category.objects.annotate(
        product_count=Count('products')
    ).order_by('name')
    
    suppliers = Supplier.objects.annotate(
        product_count=Count('products')
    ).order_by('name')
    
    context = {
        'stats': stats,
        'products': products,
        'categories': categories,
        'suppliers': suppliers,
        'search': search,
        'selected_category': category_id,
        'selected_supplier': supplier_id,
        'low_stock_filter': low_stock,
    }
    
    return render(request, 'inventory/home.html', context)

# ============= PRODUCT DETAIL =============
def product_detail(request, pk):
    """Detail produk dengan riwayat transaksi"""
    product = get_object_or_404(
        Product.objects.select_related('category', 'supplier'),
        pk=pk
    )
    
    # Get recent transactions
    transactions = StockTransaction.objects.select_related(
        'created_by'
    ).filter(
        product=product
    ).order_by('-created_at')[:10]
    
    context = {
        'product': product,
        'transactions': transactions,
    }
    
    return render(request, 'inventory/product_detail.html', context)

# ============= REPORTS =============
def stock_report(request):
    """Laporan stok"""
    products = Product.objects.select_related('category', 'supplier').all()
    
    # Filter by category
    category_id = request.GET.get('category', '')
    if category_id:
        products = products.filter(category_id=category_id)
    
    # Calculate summary
    summary = products.aggregate(
        total_items=Count('id'),
        total_value=Sum(F('stock_quantity') * F('purchase_price'))
    )
    
    categories = Category.objects.all()
    
    context = {
        'products': products,
        'summary': summary,
        'categories': categories,
        'selected_category': category_id,
    }
    
    return render(request, 'inventory/reports/stock_report.html', context)

def low_stock_report(request):
    """Laporan produk stok rendah"""
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

def transaction_report(request):
    """Laporan transaksi"""
    transactions = StockTransaction.objects.select_related(
        'product', 'product__category', 'created_by'
    ).all()
    
    # Filter by date
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    
    if start_date and end_date:
        transactions = transactions.filter(
            created_at__date__range=[start_date, end_date]
        )
    
    # Summary
    summary = transactions.aggregate(
        total_in=Sum('quantity', filter=Q(transaction_type='IN')),
        total_out=Sum('quantity', filter=Q(transaction_type='OUT')),
        total_transactions=Count('id')
    )
    
    context = {
        'transactions': transactions,
        'summary': summary,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'inventory/reports/transaction_report.html', context)