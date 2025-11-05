# core/views.py
from django.contrib.auth.models import User
from django.db.models import Q, F, Sum, Count, Avg, Max, Min
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from decimal import Decimal
from .models import Product, Category, Supplier, StockTransaction

# ============= HTML VIEWS =============

def home(request):
    """Homepage dengan katalog produk (HTML)"""
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

    # Add calculated fields to products for template
    products_with_calcs = []
    for product in products:
        product.is_low_stock = product.stock_quantity <= product.minimum_stock
        product.stock_value = product.stock_quantity * product.purchase_price
        if product.purchase_price > 0:
            product.profit_margin = ((product.selling_price - product.purchase_price) / product.purchase_price) * 100
        else:
            product.profit_margin = 0
        products_with_calcs.append(product)

    context = {
        'stats': stats,
        'products': products_with_calcs,
        'categories': categories,
        'suppliers': suppliers,
        'search': search,
        'selected_category': category_id,
        'selected_supplier': supplier_id,
        'low_stock_filter': low_stock,
    }

    return render(request, 'inventory/home.html', context)


def product_detail_html(request, pk):
    """Detail produk dengan riwayat transaksi (HTML)"""
    product = get_object_or_404(
        Product.objects.select_related('category', 'supplier'),
        pk=pk
    )

    # Calculate metrics
    product.stock_value = product.stock_quantity * product.purchase_price
    product.total_stock_value = product.stock_value  # Alias for template
    
    if product.purchase_price > 0:
        product.profit_margin = ((product.selling_price - product.purchase_price) / product.purchase_price) * 100
    else:
        product.profit_margin = 0
    
    product.is_low_stock = product.stock_quantity <= product.minimum_stock
    
    # Alias sell_price for template compatibility
    product.sell_price = product.selling_price

    # Get recent transactions
    transactions = StockTransaction.objects.select_related(
        'created_by'
    ).filter(
        product=product
    ).order_by('-created_at')[:20]

    context = {
        'product': product,
        'transactions': transactions,
    }

    return render(request, 'inventory/product_detail.html', context)


def stock_report_html(request):
    """Laporan stok produk (HTML)"""
    category_id = request.GET.get('category')
    products = Product.objects.select_related('category', 'supplier').all()
    
    if category_id:
        products = products.filter(category_id=category_id)

    # Add calculated fields
    products_with_calcs = []
    for product in products:
        product.stock_value = product.stock_quantity * product.purchase_price
        products_with_calcs.append(product)

    # Hitung summary
    summary = {
        'total_items': len(products_with_calcs),
        'total_value': sum(p.stock_value for p in products_with_calcs)
    }

    categories = Category.objects.annotate(
        product_count=Count('products')
    ).order_by('name')

    context = {
        'products': products_with_calcs,
        'summary': summary,
        'categories': categories,
        'selected_category': category_id,
    }

    return render(request, 'inventory/reports/stock_report.html', context)


def transaction_report_html(request):
    """Laporan transaksi stok (HTML)"""
    transactions = StockTransaction.objects.select_related(
        'product', 'product__category', 'created_by'
    ).order_by('-created_at')

    # Filter tanggal
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')

    if start_date and end_date:
        transactions = transactions.filter(
            created_at__date__range=[start_date, end_date]
        )
    elif start_date:
        transactions = transactions.filter(created_at__date__gte=start_date)
    elif end_date:
        transactions = transactions.filter(created_at__date__lte=end_date)

    # Hitung summary
    summary = transactions.aggregate(
        total_in=Sum('quantity', filter=Q(transaction_type='IN')),
        total_out=Sum('quantity', filter=Q(transaction_type='OUT')),
        total_transactions=Count('id')
    )
    summary['total_in'] = summary['total_in'] or 0
    summary['total_out'] = summary['total_out'] or 0
    summary['total_transactions'] = summary['total_transactions'] or 0

    # Pagination
    paginator = Paginator(transactions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'transactions': page_obj,
        'summary': summary,
        'start_date': start_date,
        'end_date': end_date,
    }

    return render(request, 'inventory/reports/transaction_report.html', context)


def low_stock_report_html(request):
    """Laporan produk stok rendah (HTML)"""
    products = Product.objects.select_related('category', 'supplier').filter(
        stock_quantity__lte=F('minimum_stock')
    ).order_by('stock_quantity')

    # Tambahkan field restock_quantity di setiap produk
    products_with_restock = []
    for product in products:
        restock_quantity = max(0, product.minimum_stock - product.stock_quantity)
        product.restock_quantity = restock_quantity
        products_with_restock.append(product)

    total_low_stock = products.count()

    # Pagination
    paginator = Paginator(products_with_restock, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'products': page_obj,
        'total_low_stock': total_low_stock,
    }

    return render(request, 'inventory/reports/low_stock_report.html', context)


# ============= API JSON ENDPOINTS =============

def create_test_product(request):
    """Create test product from query parameters"""
    try:
        category = Category.objects.first()
        supplier = Supplier.objects.first()
        
        if not category or not supplier:
            return JsonResponse({
                "status": "error",
                "message": "Please create at least one category and supplier first"
            }, status=400)
        
        product = Product.objects.create(
            sku=request.GET.get("sku", "TEST001"),
            name=request.GET.get("name", "Test Product"),
            category=category,
            supplier=supplier,
            purchase_price=Decimal(request.GET.get("purchase_price", "10000")),
            selling_price=Decimal(request.GET.get("selling_price", "15000")),
            stock_quantity=int(request.GET.get("stock", "100")),
            minimum_stock=int(request.GET.get("min_stock", "10")),
        )
        return JsonResponse({
            "status": "success",
            "id": product.id,
            "sku": product.sku,
            "name": product.name
        })
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)


# ============= CRUD OPERATIONS - CATEGORY (API) =============

def api_all_categories(request):
    """Get all categories (JSON)"""
    categories = Category.objects.annotate(
        product_count=Count('products')
    )
    
    category_list = []
    for category in categories:
        category_list.append({
            'id': category.id,
            'name': category.name,
            'product_count': category.product_count
        })
    
    return JsonResponse({'categories': category_list}, safe=False)


def api_category_detail(request, category_id):
    """Get category detail with products (JSON)"""
    try:
        category = Category.objects.annotate(
            product_count=Count('products')
        ).get(pk=category_id)
        
        products = Product.objects.filter(category=category).values(
            'id', 'sku', 'name', 'stock_quantity', 'purchase_price', 'selling_price'
        )
        
        result = {
            'id': category.id,
            'name': category.name,
            'product_count': category.product_count,
            'products': list(products)
        }
        return JsonResponse(result, safe=False)
    except Category.DoesNotExist:
        return JsonResponse({'error': 'Category not found'}, status=404)


def api_delete_category(request, category_id):
    """Delete a category (JSON)"""
    try:
        category = Category.objects.get(pk=category_id)
        category_name = category.name
        category.delete()
        return JsonResponse({
            "status": "success",
            "message": f"Category '{category_name}' deleted"
        })
    except Category.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Category not found"}, status=404)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)


# ============= CRUD OPERATIONS - SUPPLIER (API) =============

def api_all_suppliers(request):
    """Get all suppliers (JSON)"""
    suppliers = Supplier.objects.annotate(
        product_count=Count('products')
    )
    
    supplier_list = []
    for supplier in suppliers:
        supplier_list.append({
            'id': supplier.id,
            'name': supplier.name,
            'phone': supplier.phone,
            'address': supplier.address,
            'product_count': supplier.product_count
        })
    
    return JsonResponse({'suppliers': supplier_list}, safe=False)


def api_supplier_detail(request, supplier_id):
    """Get supplier detail with products (JSON)"""
    try:
        supplier = Supplier.objects.annotate(
            product_count=Count('products')
        ).get(pk=supplier_id)
        
        products = Product.objects.filter(supplier=supplier).values(
            'id', 'sku', 'name', 'stock_quantity', 'purchase_price', 'selling_price'
        )
        
        result = {
            'id': supplier.id,
            'name': supplier.name,
            'phone': supplier.phone,
            'address': supplier.address,
            'product_count': supplier.product_count,
            'products': list(products)
        }
        return JsonResponse(result, safe=False)
    except Supplier.DoesNotExist:
        return JsonResponse({'error': 'Supplier not found'}, status=404)


def api_delete_supplier(request, supplier_id):
    """Delete a supplier (JSON)"""
    try:
        supplier = Supplier.objects.get(pk=supplier_id)
        supplier_name = supplier.name
        supplier.delete()
        return JsonResponse({
            "status": "success",
            "message": f"Supplier '{supplier_name}' deleted"
        })
    except Supplier.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Supplier not found"}, status=404)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)


# ============= CRUD OPERATIONS - PRODUCT (API) =============

def api_all_products(request):
    """Get all products (JSON)"""
    products = Product.objects.select_related('category', 'supplier').all()
    
    product_list = []
    for product in products:
        product_list.append({
            'id': product.id,
            'sku': product.sku,
            'name': product.name,
            'category': {
                'id': product.category.id,
                'name': product.category.name
            },
            'supplier': {
                'id': product.supplier.id,
                'name': product.supplier.name
            },
            'purchase_price': float(product.purchase_price),
            'selling_price': float(product.selling_price),
            'stock_quantity': product.stock_quantity,
            'minimum_stock': product.minimum_stock,
        })
    
    return JsonResponse({'products': product_list}, safe=False)


def api_product_detail(request, product_id):
    """Get product detail with recent transactions (JSON)"""
    try:
        product = Product.objects.select_related('category', 'supplier').get(pk=product_id)
        
        # Calculate metrics
        stock_value = float(product.stock_quantity * product.purchase_price)
        profit_margin = 0
        if product.purchase_price > 0:
            profit_margin = float(
                ((product.selling_price - product.purchase_price) / product.purchase_price) * 100
            )
        is_low_stock = product.stock_quantity <= product.minimum_stock
        
        # Get recent transactions
        transactions = StockTransaction.objects.filter(
            product=product
        ).select_related('created_by').order_by('-created_at')[:10]
        
        transaction_list = []
        for trans in transactions:
            transaction_list.append({
                'id': trans.id,
                'type': trans.transaction_type,
                'type_display': trans.get_transaction_type_display(),
                'quantity': trans.quantity,
                'notes': trans.notes,
                'created_by': trans.created_by.username,
                'created_at': trans.created_at.isoformat()
            })
        
        result = {
            'id': product.id,
            'sku': product.sku,
            'name': product.name,
            'category': {
                'id': product.category.id,
                'name': product.category.name
            },
            'supplier': {
                'id': product.supplier.id,
                'name': product.supplier.name,
                'phone': product.supplier.phone
            },
            'purchase_price': float(product.purchase_price),
            'selling_price': float(product.selling_price),
            'stock_quantity': product.stock_quantity,
            'minimum_stock': product.minimum_stock,
            'metrics': {
                'stock_value': stock_value,
                'profit_margin': profit_margin,
                'is_low_stock': is_low_stock
            },
            'recent_transactions': transaction_list
        }
        return JsonResponse(result, safe=False)
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)


def api_products_by_category(request, category_id):
    """Get all products in a category (JSON)"""
    products = Product.objects.filter(category_id=category_id).select_related('supplier')
    
    product_list = []
    for product in products:
        product_list.append({
            'id': product.id,
            'sku': product.sku,
            'name': product.name,
            'supplier': product.supplier.name,
            'stock_quantity': product.stock_quantity,
            'purchase_price': float(product.purchase_price),
            'selling_price': float(product.selling_price),
        })
    
    return JsonResponse({
        'category_id': category_id,
        'product_count': len(product_list),
        'products': product_list
    }, safe=False)


def api_products_by_supplier(request, supplier_id):
    """Get all products from a supplier (JSON)"""
    products = Product.objects.filter(supplier_id=supplier_id).select_related('category')
    
    product_list = []
    for product in products:
        product_list.append({
            'id': product.id,
            'sku': product.sku,
            'name': product.name,
            'category': product.category.name,
            'stock_quantity': product.stock_quantity,
            'purchase_price': float(product.purchase_price),
            'selling_price': float(product.selling_price),
        })
    
    return JsonResponse({
        'supplier_id': supplier_id,
        'product_count': len(product_list),
        'products': product_list
    }, safe=False)


def api_update_product_stock(request, product_id):
    """Update product stock quantity (JSON)"""
    try:
        product = Product.objects.get(pk=product_id)
        new_stock = int(request.POST.get("stock_quantity", product.stock_quantity))
        product.stock_quantity = new_stock
        product.save()
        
        return JsonResponse({
            "status": "success",
            "product_id": product.id,
            "sku": product.sku,
            "new_stock": product.stock_quantity
        })
    except Product.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Product not found"}, status=404)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)


def api_delete_product(request, product_id):
    """Delete a product (JSON)"""
    try:
        product = Product.objects.get(pk=product_id)
        product_name = product.name
        product.delete()
        return JsonResponse({
            "status": "success",
            "message": f"Product '{product_name}' deleted"
        })
    except Product.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Product not found"}, status=404)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)


def api_delete_all_products(request):
    """Delete all products (JSON)"""
    count = Product.objects.count()
    Product.objects.all().delete()
    return JsonResponse({
        "status": "success",
        "message": f"{count} products deleted"
    })


# ============= STATISTICS & REPORTS (API) =============

def api_inventory_stats(request):
    """Get overall inventory statistics (JSON)"""
    products = Product.objects.select_related('category', 'supplier')
    
    # Basic stats
    total_products = products.count()
    low_stock_count = products.filter(stock_quantity__lte=F('minimum_stock')).count()
    
    # Price and stock aggregations
    stats = products.aggregate(
        total_stock_value=Sum(F('stock_quantity') * F('purchase_price')),
        avg_purchase_price=Avg('purchase_price'),
        avg_selling_price=Avg('selling_price'),
        max_stock=Max('stock_quantity'),
        min_stock=Min('stock_quantity'),
        total_items_in_stock=Sum('stock_quantity')
    )
    
    # Most expensive and cheapest products
    most_expensive = products.order_by('-selling_price').first()
    cheapest = products.order_by('selling_price').first()
    
    # Products with highest and lowest stock
    highest_stock = products.order_by('-stock_quantity').first()
    lowest_stock = products.order_by('stock_quantity').first()
    
    # Category statistics
    category_stats = Category.objects.annotate(
        product_count=Count('products'),
        total_stock=Sum('products__stock_quantity')
    ).order_by('-product_count')[:5]
    
    category_data = []
    for cat in category_stats:
        category_data.append({
            'name': cat.name,
            'product_count': cat.product_count,
            'total_stock': cat.total_stock or 0
        })
    
    # Supplier statistics
    supplier_stats = Supplier.objects.annotate(
        product_count=Count('products'),
        total_stock=Sum('products__stock_quantity')
    ).order_by('-product_count')[:5]
    
    supplier_data = []
    for sup in supplier_stats:
        supplier_data.append({
            'name': sup.name,
            'product_count': sup.product_count,
            'total_stock': sup.total_stock or 0
        })
    
    result = {
        'overview': {
            'total_products': total_products,
            'total_stock_value': float(stats['total_stock_value'] or 0),
            'low_stock_count': low_stock_count,
            'total_items_in_stock': stats['total_items_in_stock'] or 0,
        },
        'price_stats': {
            'avg_purchase_price': float(stats['avg_purchase_price'] or 0),
            'avg_selling_price': float(stats['avg_selling_price'] or 0),
        },
        'stock_stats': {
            'max_stock': stats['max_stock'] or 0,
            'min_stock': stats['min_stock'] or 0,
        },
        'most_expensive': {
            'id': most_expensive.id if most_expensive else None,
            'name': most_expensive.name if most_expensive else None,
            'price': float(most_expensive.selling_price) if most_expensive else None
        } if most_expensive else None,
        'cheapest': {
            'id': cheapest.id if cheapest else None,
            'name': cheapest.name if cheapest else None,
            'price': float(cheapest.selling_price) if cheapest else None
        } if cheapest else None,
        'highest_stock': {
            'id': highest_stock.id if highest_stock else None,
            'name': highest_stock.name if highest_stock else None,
            'stock': highest_stock.stock_quantity if highest_stock else None
        } if highest_stock else None,
        'lowest_stock': {
            'id': lowest_stock.id if lowest_stock else None,
            'name': lowest_stock.name if lowest_stock else None,
            'stock': lowest_stock.stock_quantity if lowest_stock else None
        } if lowest_stock else None,
        'top_categories': category_data,
        'top_suppliers': supplier_data,
    }
    
    return JsonResponse(result, safe=False)


def api_low_stock_products(request):
    """Get products with low stock (JSON)"""
    products = Product.objects.filter(
        stock_quantity__lte=F('minimum_stock')
    ).select_related('category', 'supplier').order_by('stock_quantity')
    
    product_list = []
    for product in products:
        product_list.append({
            'id': product.id,
            'sku': product.sku,
            'name': product.name,
            'category': product.category.name,
            'supplier': product.supplier.name,
            'stock_quantity': product.stock_quantity,
            'minimum_stock': product.minimum_stock,
            'shortage': product.minimum_stock - product.stock_quantity
        })
    
    return JsonResponse({
        'low_stock_count': len(product_list),
        'products': product_list
    }, safe=False)


def api_stock_value_report(request):
    """Report of stock value by category and supplier (JSON)"""
    # By category
    category_values = Category.objects.annotate(
        product_count=Count('products'),
        total_stock=Sum('products__stock_quantity'),
        total_value=Sum(F('products__stock_quantity') * F('products__purchase_price'))
    ).order_by('-total_value')
    
    category_data = []
    for cat in category_values:
        category_data.append({
            'name': cat.name,
            'product_count': cat.product_count,
            'total_stock': cat.total_stock or 0,
            'total_value': float(cat.total_value or 0)
        })
    
    # By supplier
    supplier_values = Supplier.objects.annotate(
        product_count=Count('products'),
        total_stock=Sum('products__stock_quantity'),
        total_value=Sum(F('products__stock_quantity') * F('products__purchase_price'))
    ).order_by('-total_value')
    
    supplier_data = []
    for sup in supplier_values:
        supplier_data.append({
            'name': sup.name,
            'product_count': sup.product_count,
            'total_stock': sup.total_stock or 0,
            'total_value': float(sup.total_value or 0)
        })
    
    result = {
        'by_category': category_data,
        'by_supplier': supplier_data
    }
    
    return JsonResponse(result, safe=False)


def api_transaction_stats(request):
    """Get transaction statistics (JSON)"""
    transactions = StockTransaction.objects.select_related('product', 'created_by')
    
    # Overall stats
    stats = transactions.aggregate(
        total_transactions=Count('id'),
        total_in=Sum('quantity', filter=Q(transaction_type='IN')),
        total_out=Sum('quantity', filter=Q(transaction_type='OUT')),
    )
    
    # Recent transactions
    recent_transactions = transactions.order_by('-created_at')[:20]
    
    transaction_list = []
    for trans in recent_transactions:
        transaction_list.append({
            'id': trans.id,
            'product': {
                'id': trans.product.id,
                'sku': trans.product.sku,
                'name': trans.product.name
            },
            'type': trans.transaction_type,
            'type_display': trans.get_transaction_type_display(),
            'quantity': trans.quantity,
            'notes': trans.notes,
            'created_by': trans.created_by.username,
            'created_at': trans.created_at.isoformat()
        })
    
    # By user
    user_stats = User.objects.annotate(
        transaction_count=Count('stock_transactions')
    ).filter(transaction_count__gt=0).order_by('-transaction_count')[:10]
    
    user_data = []
    for user in user_stats:
        user_data.append({
            'username': user.username,
            'transaction_count': user.transaction_count
        })
    
    result = {
        'overview': {
            'total_transactions': stats['total_transactions'],
            'total_in': stats['total_in'] or 0,
            'total_out': stats['total_out'] or 0,
            'net_movement': (stats['total_in'] or 0) - (stats['total_out'] or 0)
        },
        'recent_transactions': transaction_list,
        'top_users': user_data
    }
    
    return JsonResponse(result, safe=False)


def api_product_transaction_history(request, product_id):
    """Get transaction history for a specific product (JSON)"""
    try:
        product = Product.objects.get(pk=product_id)
        
        transactions = StockTransaction.objects.filter(
            product=product
        ).select_related('created_by').order_by('-created_at')
        
        transaction_list = []
        for trans in transactions:
            transaction_list.append({
                'id': trans.id,
                'type': trans.transaction_type,
                'type_display': trans.get_transaction_type_display(),
                'quantity': trans.quantity,
                'notes': trans.notes,
                'created_by': trans.created_by.username,
                'created_at': trans.created_at.isoformat()
            })
        
        # Stats for this product
        trans_stats = transactions.aggregate(
            total_transactions=Count('id'),
            total_in=Sum('quantity', filter=Q(transaction_type='IN')),
            total_out=Sum('quantity', filter=Q(transaction_type='OUT')),
        )
        
        result = {
            'product': {
                'id': product.id,
                'sku': product.sku,
                'name': product.name,
                'current_stock': product.stock_quantity
            },
            'stats': {
                'total_transactions': trans_stats['total_transactions'],
                'total_in': trans_stats['total_in'] or 0,
                'total_out': trans_stats['total_out'] or 0,
            },
            'transactions': transaction_list
        }
        
        return JsonResponse(result, safe=False)
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)


# ============= SEARCH & FILTER (API) =============

def api_search_products(request):
    """Search products by name or SKU (JSON)"""
    query = request.GET.get('q', '')
    
    if not query:
        return JsonResponse({'error': 'No search query provided'}, status=400)
    
    products = Product.objects.filter(
        Q(name__icontains=query) | Q(sku__icontains=query)
    ).select_related('category', 'supplier')
    
    product_list = []
    for product in products:
        product_list.append({
            'id': product.id,
            'sku': product.sku,
            'name': product.name,
            'category': product.category.name,
            'supplier': product.supplier.name,
            'stock_quantity': product.stock_quantity,
            'selling_price': float(product.selling_price),
        })
    
    return JsonResponse({
        'query': query,
        'result_count': len(product_list),
        'products': product_list
    }, safe=False)


# ============= TESTING =============

def testing(request):
    """Testing endpoint (JSON)"""
    products_count = Product.objects.count()
    categories_count = Category.objects.count()
    suppliers_count = Supplier.objects.count()
    transactions_count = StockTransaction.objects.count()
    
    return JsonResponse({
        'status': 'ok',
        'counts': {
            'products': products_count,
            'categories': categories_count,
            'suppliers': suppliers_count,
            'transactions': transactions_count
        }
    })

def dashboard_stats_html(request):
    """Dashboard statistik lengkap (HTML)"""
    from decimal import Decimal
    from django.utils import timezone
    from datetime import timedelta
    
    # === OVERVIEW STATISTICS ===
    total_products = Product.objects.count()
    total_categories = Category.objects.count()
    total_suppliers = Supplier.objects.count()
    
    # Total nilai stok
    total_stock_value = Product.objects.aggregate(
        total=Sum(F('stock_quantity') * F('purchase_price'))
    )['total'] or 0
    
    # Produk stok rendah
    low_stock_products = Product.objects.filter(
        stock_quantity__lte=F('minimum_stock')
    )
    low_stock_count = low_stock_products.count()
    
    # Total transaksi
    total_transactions = StockTransaction.objects.count()
    
    # === PRODUCT STATISTICS ===
    # Produk dengan stok tertinggi
    top_stock_products = Product.objects.select_related(
        'category', 'supplier'
    ).order_by('-stock_quantity')[:5]
    
    # Produk dengan nilai stok tertinggi
    products_with_value = Product.objects.select_related('category', 'supplier').all()
    top_value_products = []
    for product in products_with_value:
        product.stock_value = product.stock_quantity * product.purchase_price
        top_value_products.append(product)
    top_value_products = sorted(top_value_products, key=lambda x: x.stock_value, reverse=True)[:5]
    
    # Produk dengan margin tertinggi
    products_with_margin = []
    for product in products_with_value:
        if product.purchase_price > 0:
            margin = ((product.selling_price - product.purchase_price) / product.purchase_price) * 100
            product.profit_margin = margin
            products_with_margin.append(product)
    top_margin_products = sorted(products_with_margin, key=lambda x: x.profit_margin, reverse=True)[:5]
    
    # === CATEGORY STATISTICS ===
    category_stats = Category.objects.annotate(
        product_count=Count('products'),
        total_stock=Sum('products__stock_quantity'),
        total_value=Sum(F('products__stock_quantity') * F('products__purchase_price'))
    ).order_by('-total_value')
    
    # === SUPPLIER STATISTICS ===
    supplier_stats = Supplier.objects.annotate(
        product_count=Count('products'),
        total_stock=Sum('products__stock_quantity'),
        total_value=Sum(F('products__stock_quantity') * F('products__purchase_price'))
    ).order_by('-total_value')
    
    # === TRANSACTION STATISTICS ===
    transaction_stats = StockTransaction.objects.aggregate(
        total_in=Sum('quantity', filter=Q(transaction_type='IN')),
        total_out=Sum('quantity', filter=Q(transaction_type='OUT')),
    )
    
    # Transaksi terbaru
    recent_transactions = StockTransaction.objects.select_related(
        'product', 'created_by'
    ).order_by('-created_at')[:10]
    
    # Transaksi per hari (7 hari terakhir)
    today = timezone.now().date()
    last_7_days = [today - timedelta(days=i) for i in range(6, -1, -1)]
    
    daily_transactions = []
    for day in last_7_days:
        day_trans = StockTransaction.objects.filter(
            created_at__date=day
        ).aggregate(
            stock_in=Sum('quantity', filter=Q(transaction_type='IN')),
            stock_out=Sum('quantity', filter=Q(transaction_type='OUT')),
            count=Count('id')
        )
        daily_transactions.append({
            'date': day,
            'stock_in': day_trans['stock_in'] or 0,
            'stock_out': day_trans['stock_out'] or 0,
            'count': day_trans['count']
        })
    
    # === PRICE STATISTICS ===
    price_stats = Product.objects.aggregate(
        avg_purchase=Avg('purchase_price'),
        avg_selling=Avg('selling_price'),
        min_price=Min('selling_price'),
        max_price=Max('selling_price'),
    )
    
    context = {
        # Overview
        'total_products': total_products,
        'total_categories': total_categories,
        'total_suppliers': total_suppliers,
        'total_stock_value': total_stock_value,
        'low_stock_count': low_stock_count,
        'total_transactions': total_transactions,
        
        # Products
        'top_stock_products': top_stock_products,
        'top_value_products': top_value_products,
        'top_margin_products': top_margin_products,
        'low_stock_products': low_stock_products[:5],
        
        # Categories & Suppliers
        'category_stats': category_stats,
        'supplier_stats': supplier_stats,
        
        # Transactions
        'transaction_stats': transaction_stats,
        'recent_transactions': recent_transactions,
        'daily_transactions': daily_transactions,
        
        # Price
        'price_stats': price_stats,
    }
    
    return render(request, 'inventory/dashboard_stats.html', context)