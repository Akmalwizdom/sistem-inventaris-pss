# core/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Homepage (Katalog Produk)
    path('', views.home, name='home'),
    
    # Product Detail
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    
    # Reports
    path('reports/stock/', views.stock_report, name='stock_report'),
    path('reports/low-stock/', views.low_stock_report, name='low_stock_report'),
    path('reports/transactions/', views.transaction_report, name='transaction_report'),
]