# core/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # ============= HTML VIEWS =============
    # Homepage & Product Pages
    path('', views.home, name='home'),
    path('product/<int:pk>/', views.product_detail_html, name='product_detail'),
    
    # Dashboard Statistik 
    path('dashboard/', views.dashboard_stats_html, name='dashboard_stats'),

    # Reports (HTML)
    path('reports/stock/', views.stock_report_html, name='stock_report'),
    path('reports/low-stock/', views.low_stock_report_html, name='low_stock_report'),
    path('reports/transactions/', views.transaction_report_html, name='transaction_report'),
    
    # ============= API JSON ENDPOINTS =============
    # Testing & Helper
    path('api/testing/', views.testing, name='api_testing'),
    path('api/create-test-product/', views.create_test_product, name='api_create_test_product'),
    
    # Categories API
    path('api/categories/', views.api_all_categories, name='api_all_categories'),
    path('api/categories/<int:category_id>/', views.api_category_detail, name='api_category_detail'),
    path('api/categories/<int:category_id>/delete/', views.api_delete_category, name='api_delete_category'),
    
    # Suppliers API
    path('api/suppliers/', views.api_all_suppliers, name='api_all_suppliers'),
    path('api/suppliers/<int:supplier_id>/', views.api_supplier_detail, name='api_supplier_detail'),
    path('api/suppliers/<int:supplier_id>/delete/', views.api_delete_supplier, name='api_delete_supplier'),
    
    # Products API
    path('api/products/', views.api_all_products, name='api_all_products'),
    path('api/products/<int:product_id>/', views.api_product_detail, name='api_product_detail'),
    path('api/products/<int:product_id>/update/', views.api_update_product_stock, name='api_update_product_stock'),
    path('api/products/<int:product_id>/delete/', views.api_delete_product, name='api_delete_product'),
    path('api/products/delete-all/', views.api_delete_all_products, name='api_delete_all_products'),
    path('api/products/by-category/<int:category_id>/', views.api_products_by_category, name='api_products_by_category'),
    path('api/products/by-supplier/<int:supplier_id>/', views.api_products_by_supplier, name='api_products_by_supplier'),
    path('api/products/search/', views.api_search_products, name='api_search_products'),
    
    # Statistics & Reports API
    path('api/stats/inventory/', views.api_inventory_stats, name='api_inventory_stats'),
    path('api/stats/low-stock/', views.api_low_stock_products, name='api_low_stock_products'),
    path('api/stats/stock-value/', views.api_stock_value_report, name='api_stock_value_report'),
    path('api/stats/transactions/', views.api_transaction_stats, name='api_transaction_stats'),
    path('api/stats/product/<int:product_id>/transactions/', views.api_product_transaction_history, name='api_product_transaction_history'),
]