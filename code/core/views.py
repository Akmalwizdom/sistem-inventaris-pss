from django.contrib.auth.models import User
from django.db.models import Q, F, Sum, Count, Avg, Max, Min
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from decimal import Decimal
from .models import Product, Category, Supplier, StockTransaction


# ============= UTILITIES =============

def _profit_margin(purchase_price, selling_price):
    return float(((selling_price - purchase_price) / purchase_price) * 100) if purchase_price > 0 else 0.0

def _is_low_stock(product):
    return product.stock_quantity <= product.minimum_stock

def _stock_value(product):
    return product.stock_quantity * product.purchase_price

def _annotate_counts(qs, rel='products'):
    return qs.annotate(product_count=Count(rel)).order_by('name')


# ============= HTML VIEWS =============

def home(request):
    """Homepage dengan katalog produk (HTML)"""
    stats = {
        'total_products': Product.objects.count(),
        'total_stock_value': Product.objects.aggregate(total=Sum(F('stock_quantity') * F('purchase_price')))['total'] or 0,
        'low_stock_count': Product.objects.filter(stock_quantity__lte=F('minimum_stock')).count(),
    }

    products = Product.objects.select_related('category', 'supplier')

    search = request.GET.get('search')
    if search:
        products = products.filter(Q(name__icontains=search) | Q(sku__icontains=search))

    if (category_id := request.GET.get('category')):
        products = products.filter(category_id=category_id)

    if (supplier_id := request.GET.get('supplier')):
        products = products.filter(supplier_id=supplier_id)

    if request.GET.get('low_stock') == 'true':
        products = products.filter(stock_quantity__lte=F('minimum_stock'))

    products = products.order_by('name')

    categories = _annotate_counts(Category.objects.all())
    suppliers = _annotate_counts(Supplier.objects.all())

    products_with_calcs = []
    for p in products:
        p.is_low_stock = _is_low_stock(p)
        p.stock_value = _stock_value(p)
        p.profit_margin = _profit_margin(p.purchase_price, p.selling_price)
        products_with_calcs.append(p)

    context = {
        'stats': stats,
        'products': products_with_calcs,
        'categories': categories,
        'suppliers': suppliers,
        'search': search or '',
        'selected_category': request.GET.get('category', ''),
        'selected_supplier': request.GET.get('supplier', ''),
        'low_stock_filter': request.GET.get('low_stock', ''),
    }
    return render(request, 'inventory/home.html', context)


def product_detail_html(request, pk):
    """Detail produk dengan riwayat transaksi (HTML)"""
    product = get_object_or_404(Product.objects.select_related('category', 'supplier'), pk=pk)

    product.stock_value = _stock_value(product)
    product.total_stock_value = product.stock_value
    product.profit_margin = _profit_margin(product.purchase_price, product.selling_price)
    product.is_low_stock = _is_low_stock(product)
    product.sell_price = product.selling_price  # alias untuk template

    transactions = (StockTransaction.objects
                    .select_related('created_by')
                    .filter(product=product)
                    .order_by('-created_at')[:20])

    return render(request, 'inventory/product_detail.html', {'product': product, 'transactions': transactions})


def stock_report_html(request):
    """Laporan stok produk (HTML)"""
    products = Product.objects.select_related('category', 'supplier')
    if (category_id := request.GET.get('category')):
        products = products.filter(category_id=category_id)

    products_with_calcs = []
    for p in products:
        p.stock_value = _stock_value(p)
        products_with_calcs.append(p)

    summary = {
        'total_items': len(products_with_calcs),
        'total_value': sum(p.stock_value for p in products_with_calcs)
    }

    categories = _annotate_counts(Category.objects.all())
    context = {
        'products': products_with_calcs,
        'summary': summary,
        'categories': categories,
        'selected_category': request.GET.get('category'),
    }
    return render(request, 'inventory/reports/stock_report.html', context)


def transaction_report_html(request):
    """Laporan transaksi stok (HTML)"""
    transactions = StockTransaction.objects.select_related('product', 'product__category', 'created_by').order_by('-created_at')

    start_date, end_date = request.GET.get('start_date', ''), request.GET.get('end_date', '')
    if start_date and end_date:
        transactions = transactions.filter(created_at__date__range=[start_date, end_date])
    elif start_date:
        transactions = transactions.filter(created_at__date__gte=start_date)
    elif end_date:
        transactions = transactions.filter(created_at__date__lte=end_date)

    summary = transactions.aggregate(
        total_in=Sum('quantity', filter=Q(transaction_type='IN')),
        total_out=Sum('quantity', filter=Q(transaction_type='OUT')),
        total_transactions=Count('id')
    )
    for k in ('total_in', 'total_out', 'total_transactions'):
        summary[k] = summary[k] or 0

    page_obj = Paginator(transactions, 20).get_page(request.GET.get('page'))
    context = {'transactions': page_obj, 'summary': summary, 'start_date': start_date, 'end_date': end_date}
    return render(request, 'inventory/reports/transaction_report.html', context)


def low_stock_report_html(request):
    """Laporan produk stok rendah (HTML)"""
    products = (Product.objects.select_related('category', 'supplier')
                .filter(stock_quantity__lte=F('minimum_stock'))
                .order_by('stock_quantity'))

    products_with_restock = []
    for p in products:
        p.restock_quantity = max(0, p.minimum_stock - p.stock_quantity)
        products_with_restock.append(p)

    page_obj = Paginator(products_with_restock, 20).get_page(request.GET.get('page'))
    context = {'products': page_obj, 'total_low_stock': products.count()}
    return render(request, 'inventory/reports/low_stock_report.html', context)


# ============= API JSON ENDPOINTS =============

def create_test_product(request):
    """Create test product from query parameters"""
    try:
        category, supplier = Category.objects.first(), Supplier.objects.first()
        if not category or not supplier:
            return JsonResponse({"status": "error", "message": "Please create at least one category and supplier first"}, status=400)

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
        return JsonResponse({"status": "success", "id": product.id, "sku": product.sku, "name": product.name})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)


# ============= CRUD OPERATIONS - CATEGORY (API) =============

def api_all_categories(request):
    """Get all categories (JSON)"""
    categories = _annotate_counts(Category.objects.all())
    data = [{'id': c.id, 'name': c.name, 'product_count': c.product_count} for c in categories]
    return JsonResponse({'categories': data}, safe=False)


def api_category_detail(request, category_id):
    """Get category detail with products (JSON)"""
    try:
        category = Category.objects.annotate(product_count=Count('products')).get(pk=category_id)
        products = list(Product.objects.filter(category=category).values(
            'id', 'sku', 'name', 'stock_quantity', 'purchase_price', 'selling_price'
        ))
        return JsonResponse({'id': category.id, 'name': category.name, 'product_count': category.product_count, 'products': products}, safe=False)
    except Category.DoesNotExist:
        return JsonResponse({'error': 'Category not found'}, status=404)


def api_delete_category(request, category_id):
    """Delete a category (JSON)"""
    try:
        category = Category.objects.get(pk=category_id)
        name = category.name
        category.delete()
        return JsonResponse({"status": "success", "message": f"Category '{name}' deleted"})
    except Category.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Category not found"}, status=404)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)


# ============= CRUD OPERATIONS - SUPPLIER (API) =============

def api_all_suppliers(request):
    """Get all suppliers (JSON)"""
    suppliers = _annotate_counts(Supplier.objects.all())
    data = [{'id': s.id, 'name': s.name, 'phone': s.phone, 'address': s.address, 'product_count': s.product_count} for s in suppliers]
    return JsonResponse({'suppliers': data}, safe=False)


def api_supplier_detail(request, supplier_id):
    """Get supplier detail with products (JSON)"""
    try:
        supplier = Supplier.objects.annotate(product_count=Count('products')).get(pk=supplier_id)
        products = list(Product.objects.filter(supplier=supplier).values(
            'id', 'sku', 'name', 'stock_quantity', 'purchase_price', 'selling_price'
        ))
        return JsonResponse({
            'id': supplier.id,
            'name': supplier.name,
            'phone': supplier.phone,
            'address': supplier.address,
            'product_count': supplier.product_count,
            'products': products
        }, safe=False)
    except Supplier.DoesNotExist:
        return JsonResponse({'error': 'Supplier not found'}, status=404)


def api_delete_supplier(request, supplier_id):
    """Delete a supplier (JSON)"""
    try:
        supplier = Supplier.objects.get(pk=supplier_id)
        name = supplier.name
        supplier.delete()
        return JsonResponse({"status": "success", "message": f"Supplier '{name}' deleted"})
    except Supplier.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Supplier not found"}, status=404)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)


# ============= CRUD OPERATIONS - PRODUCT (API) =============

def api_all_products(request):
    """Get all products (JSON)"""
    products = Product.objects.select_related('category', 'supplier')
    data = [{
        'id': p.id,
        'sku': p.sku,
        'name': p.name,
        'category': {'id': p.category.id, 'name': p.category.name},
        'supplier': {'id': p.supplier.id, 'name': p.supplier.name},
        'purchase_price': float(p.purchase_price),
        'selling_price': float(p.selling_price),
        'stock_quantity': p.stock_quantity,
        'minimum_stock': p.minimum_stock,
    } for p in products]
    return JsonResponse({'products': data}, safe=False)


def api_product_detail(request, product_id):
    """Get product detail with recent transactions (JSON)"""
    try:
        p = Product.objects.select_related('category', 'supplier').get(pk=product_id)
        transactions = (StockTransaction.objects.filter(product=p)
                        .select_related('created_by').order_by('-created_at')[:10])

        transaction_list = [{
            'id': t.id,
            'type': t.transaction_type,
            'type_display': t.get_transaction_type_display(),
            'quantity': t.quantity,
            'notes': t.notes,
            'created_by': t.created_by.username,
            'created_at': t.created_at.isoformat()
        } for t in transactions]

        result = {
            'id': p.id,
            'sku': p.sku,
            'name': p.name,
            'category': {'id': p.category.id, 'name': p.category.name},
            'supplier': {'id': p.supplier.id, 'name': p.supplier.name, 'phone': p.supplier.phone},
            'purchase_price': float(p.purchase_price),
            'selling_price': float(p.selling_price),
            'stock_quantity': p.stock_quantity,
            'minimum_stock': p.minimum_stock,
            'metrics': {
                'stock_value': float(_stock_value(p)),
                'profit_margin': _profit_margin(p.purchase_price, p.selling_price),
                'is_low_stock': _is_low_stock(p)
            },
            'recent_transactions': transaction_list
        }
        return JsonResponse(result, safe=False)
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)


def api_products_by_category(request, category_id):
    """Get all products in a category (JSON)"""
    products = Product.objects.filter(category_id=category_id).select_related('supplier')
    data = [{
        'id': p.id, 'sku': p.sku, 'name': p.name, 'supplier': p.supplier.name,
        'stock_quantity': p.stock_quantity, 'purchase_price': float(p.purchase_price),
        'selling_price': float(p.selling_price)
    } for p in products]
    return JsonResponse({'category_id': category_id, 'product_count': len(data), 'products': data}, safe=False)


def api_products_by_supplier(request, supplier_id):
    """Get all products from a supplier (JSON)"""
    products = Product.objects.filter(supplier_id=supplier_id).select_related('category')
    data = [{
        'id': p.id, 'sku': p.sku, 'name': p.name, 'category': p.category.name,
        'stock_quantity': p.stock_quantity, 'purchase_price': float(p.purchase_price),
        'selling_price': float(p.selling_price)
    } for p in products]
    return JsonResponse({'supplier_id': supplier_id, 'product_count': len(data), 'products': data}, safe=False)


def api_update_product_stock(request, product_id):
    """Update product stock quantity (JSON)"""
    try:
        product = Product.objects.get(pk=product_id)
        product.stock_quantity = int(request.POST.get("stock_quantity", product.stock_quantity))
        product.save()
        return JsonResponse({"status": "success", "product_id": product.id, "sku": product.sku, "new_stock": product.stock_quantity})
    except Product.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Product not found"}, status=404)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)


def api_delete_product(request, product_id):
    """Delete a product (JSON)"""
    try:
        product = Product.objects.get(pk=product_id)
        name = product.name
        product.delete()
        return JsonResponse({"status": "success", "message": f"Product '{name}' deleted"})
    except Product.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Product not found"}, status=404)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)


def api_delete_all_products(request):
    """Delete all products (JSON)"""
    count = Product.objects.count()
    Product.objects.all().delete()
    return JsonResponse({"status": "success", "message": f"{count} products deleted"})


# ============= STATISTICS & REPORTS (API) =============

def api_inventory_stats(request):
    """Get overall inventory statistics (JSON)"""
    products = Product.objects.select_related('category', 'supplier')
    total_products = products.count()
    low_stock_count = products.filter(stock_quantity__lte=F('minimum_stock')).count()

    stats = products.aggregate(
        total_stock_value=Sum(F('stock_quantity') * F('purchase_price')),
        avg_purchase_price=Avg('purchase_price'),
        avg_selling_price=Avg('selling_price'),
        max_stock=Max('stock_quantity'),
        min_stock=Min('stock_quantity'),
        total_items_in_stock=Sum('stock_quantity')
    )

    most_expensive = products.order_by('-selling_price').first()
    cheapest = products.order_by('selling_price').first()
    highest_stock = products.order_by('-stock_quantity').first()
    lowest_stock = products.order_by('stock_quantity').first()

    top_cats = Category.objects.annotate(product_count=Count('products'), total_stock=Sum('products__stock_quantity')).order_by('-product_count')[:5]
    top_sups = Supplier.objects.annotate(product_count=Count('products'), total_stock=Sum('products__stock_quantity')).order_by('-product_count')[:5]

    category_data = [{'name': c.name, 'product_count': c.product_count, 'total_stock': c.total_stock or 0} for c in top_cats]
    supplier_data = [{'name': s.name, 'product_count': s.product_count, 'total_stock': s.total_stock or 0} for s in top_sups]

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
        'stock_stats': {'max_stock': stats['max_stock'] or 0, 'min_stock': stats['min_stock'] or 0},
        'most_expensive': ({
            'id': most_expensive.id, 'name': most_expensive.name, 'price': float(most_expensive.selling_price)
        } if most_expensive else None),
        'cheapest': ({
            'id': cheapest.id, 'name': cheapest.name, 'price': float(cheapest.selling_price)
        } if cheapest else None),
        'highest_stock': ({
            'id': highest_stock.id, 'name': highest_stock.name, 'stock': highest_stock.stock_quantity
        } if highest_stock else None),
        'lowest_stock': ({
            'id': lowest_stock.id, 'name': lowest_stock.name, 'stock': lowest_stock.stock_quantity
        } if lowest_stock else None),
        'top_categories': category_data,
        'top_suppliers': supplier_data,
    }
    return JsonResponse(result, safe=False)


def api_low_stock_products(request):
    """Get products with low stock (JSON)"""
    products = (Product.objects.filter(stock_quantity__lte=F('minimum_stock'))
                .select_related('category', 'supplier').order_by('stock_quantity'))
    data = [{
        'id': p.id, 'sku': p.sku, 'name': p.name, 'category': p.category.name, 'supplier': p.supplier.name,
        'stock_quantity': p.stock_quantity, 'minimum_stock': p.minimum_stock, 'shortage': p.minimum_stock - p.stock_quantity
    } for p in products]
    return JsonResponse({'low_stock_count': len(data), 'products': data}, safe=False)


def api_stock_value_report(request):
    """Report of stock value by category and supplier (JSON)"""
    cat_values = Category.objects.annotate(
        product_count=Count('products'),
        total_stock=Sum('products__stock_quantity'),
        total_value=Sum(F('products__stock_quantity') * F('products__purchase_price'))
    ).order_by('-total_value')

    sup_values = Supplier.objects.annotate(
        product_count=Count('products'),
        total_stock=Sum('products__stock_quantity'),
        total_value=Sum(F('products__stock_quantity') * F('products__purchase_price'))
    ).order_by('-total_value')

    by_category = [{'name': c.name, 'product_count': c.product_count, 'total_stock': c.total_stock or 0, 'total_value': float(c.total_value or 0)} for c in cat_values]
    by_supplier = [{'name': s.name, 'product_count': s.product_count, 'total_stock': s.total_stock or 0, 'total_value': float(s.total_value or 0)} for s in sup_values]

    return JsonResponse({'by_category': by_category, 'by_supplier': by_supplier}, safe=False)


def api_transaction_stats(request):
    """Get transaction statistics (JSON)"""
    transactions = StockTransaction.objects.select_related('product', 'created_by')

    stats = transactions.aggregate(
        total_transactions=Count('id'),
        total_in=Sum('quantity', filter=Q(transaction_type='IN')),
        total_out=Sum('quantity', filter=Q(transaction_type='OUT')),
    )

    recent = transactions.order_by('-created_at')[:20]
    recent_list = [{
        'id': t.id,
        'product': {'id': t.product.id, 'sku': t.product.sku, 'name': t.product.name},
        'type': t.transaction_type,
        'type_display': t.get_transaction_type_display(),
        'quantity': t.quantity,
        'notes': t.notes,
        'created_by': t.created_by.username,
        'created_at': t.created_at.isoformat()
    } for t in recent]

    user_stats = (User.objects.annotate(transaction_count=Count('stock_transactions'))
                  .filter(transaction_count__gt=0).order_by('-transaction_count')[:10])
    top_users = [{'username': u.username, 'transaction_count': u.transaction_count} for u in user_stats]

    result = {
        'overview': {
            'total_transactions': stats['total_transactions'],
            'total_in': stats['total_in'] or 0,
            'total_out': stats['total_out'] or 0,
            'net_movement': (stats['total_in'] or 0) - (stats['total_out'] or 0)
        },
        'recent_transactions': recent_list,
        'top_users': top_users
    }
    return JsonResponse(result, safe=False)


def api_product_transaction_history(request, product_id):
    """Get transaction history for a specific product (JSON)"""
    try:
        product = Product.objects.get(pk=product_id)
        transactions = StockTransaction.objects.filter(product=product).select_related('created_by').order_by('-created_at')

        tx_list = [{
            'id': t.id,
            'type': t.transaction_type,
            'type_display': t.get_transaction_type_display(),
            'quantity': t.quantity,
            'notes': t.notes,
            'created_by': t.created_by.username,
            'created_at': t.created_at.isoformat()
        } for t in transactions]

        stats = transactions.aggregate(
            total_transactions=Count('id'),
            total_in=Sum('quantity', filter=Q(transaction_type='IN')),
            total_out=Sum('quantity', filter=Q(transaction_type='OUT')),
        )

        return JsonResponse({
            'product': {'id': product.id, 'sku': product.sku, 'name': product.name, 'current_stock': product.stock_quantity},
            'stats': {'total_transactions': stats['total_transactions'], 'total_in': stats['total_in'] or 0, 'total_out': stats['total_out'] or 0},
            'transactions': tx_list
        }, safe=False)
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)


# ============= SEARCH & FILTER (API) =============

def api_search_products(request):
    """Search products by name or SKU (JSON)"""
    query = request.GET.get('q', '')
    if not query:
        return JsonResponse({'error': 'No search query provided'}, status=400)

    products = Product.objects.filter(Q(name__icontains=query) | Q(sku__icontains=query)).select_related('category', 'supplier')
    data = [{'id': p.id, 'sku': p.sku, 'name': p.name, 'category': p.category.name, 'supplier': p.supplier.name,
             'stock_quantity': p.stock_quantity, 'selling_price': float(p.selling_price)} for p in products]
    return JsonResponse({'query': query, 'result_count': len(data), 'products': data}, safe=False)


# ============= TESTING =============

def testing(request):
    """Testing endpoint (JSON)"""
    counts = {
        'products': Product.objects.count(),
        'categories': Category.objects.count(),
        'suppliers': Supplier.objects.count(),
        'transactions': StockTransaction.objects.count()
    }
    return JsonResponse({'status': 'ok', 'counts': counts})


def dashboard_stats_html(request):
    """Dashboard statistik lengkap (HTML)"""
    from django.utils import timezone
    from datetime import timedelta

    total_products = Product.objects.count()
    total_categories = Category.objects.count()
    total_suppliers = Supplier.objects.count()

    total_stock_value = Product.objects.aggregate(total=Sum(F('stock_quantity') * F('purchase_price')))['total'] or 0
    low_stock_products = Product.objects.filter(stock_quantity__lte=F('minimum_stock'))
    low_stock_count = low_stock_products.count()
    total_transactions = StockTransaction.objects.count()

    top_stock_products = Product.objects.select_related('category', 'supplier').order_by('-stock_quantity')[:5]

    products_with_value = Product.objects.select_related('category', 'supplier')
    top_value_products = []
    products_with_margin = []
    for p in products_with_value:
        p.stock_value = _stock_value(p)
        top_value_products.append(p)
        margin = _profit_margin(p.purchase_price, p.selling_price)
        if margin:
            p.profit_margin = margin
            products_with_margin.append(p)

    top_value_products = sorted(top_value_products, key=lambda x: x.stock_value, reverse=True)[:5]
    top_margin_products = sorted(products_with_margin, key=lambda x: x.profit_margin, reverse=True)[:5]

    category_stats = Category.objects.annotate(
        product_count=Count('products'),
        total_stock=Sum('products__stock_quantity'),
        total_value=Sum(F('products__stock_quantity') * F('products__purchase_price'))
    ).order_by('-total_value')

    supplier_stats = Supplier.objects.annotate(
        product_count=Count('products'),
        total_stock=Sum('products__stock_quantity'),
        total_value=Sum(F('products__stock_quantity') * F('products__purchase_price'))
    ).order_by('-total_value')

    transaction_stats = StockTransaction.objects.aggregate(
        total_in=Sum('quantity', filter=Q(transaction_type='IN')),
        total_out=Sum('quantity', filter=Q(transaction_type='OUT')),
    )

    recent_transactions = StockTransaction.objects.select_related('product', 'created_by').order_by('-created_at')[:10]

    today = timezone.now().date()
    last_7_days = [today - timedelta(days=i) for i in range(6, -1, -1)]
    daily_transactions = []
    for day in last_7_days:
        agg = StockTransaction.objects.filter(created_at__date=day).aggregate(
            stock_in=Sum('quantity', filter=Q(transaction_type='IN')),
            stock_out=Sum('quantity', filter=Q(transaction_type='OUT')),
            count=Count('id')
        )
        daily_transactions.append({'date': day, 'stock_in': agg['stock_in'] or 0, 'stock_out': agg['stock_out'] or 0, 'count': agg['count']})

    price_stats = Product.objects.aggregate(
        avg_purchase=Avg('purchase_price'),
        avg_selling=Avg('selling_price'),
        min_price=Min('selling_price'),
        max_price=Max('selling_price'),
    )

    context = {
        'total_products': total_products,
        'total_categories': total_categories,
        'total_suppliers': total_suppliers,
        'total_stock_value': total_stock_value,
        'low_stock_count': low_stock_count,
        'total_transactions': total_transactions,
        'top_stock_products': top_stock_products,
        'top_value_products': top_value_products,
        'top_margin_products': top_margin_products,
        'low_stock_products': low_stock_products[:5],
        'category_stats': category_stats,
        'supplier_stats': supplier_stats,
        'transaction_stats': transaction_stats,
        'recent_transactions': recent_transactions,
        'daily_transactions': daily_transactions,
        'price_stats': price_stats,
    }
    return render(request, 'inventory/dashboard_stats.html', context)