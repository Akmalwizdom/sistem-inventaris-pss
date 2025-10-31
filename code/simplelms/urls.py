# simplelms/urls.py
"""
URL configuration for simplelms project - Inventory Management System
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    # ✅ Admin Panel
    path('admin/', admin.site.urls),
    
    # ✅ Silk Profiler (Query Analysis)
    path('silk/', include('silk.urls', namespace='silk')),
    
    # ✅ UPDATED: Authentication URLs
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # ✅ UPDATED: Core Inventory App (Main Routes)
    path('', include('core.urls')),  # Changed from 'api/' to root
]

# ✅ ADDED: Static & Media files serving (Development only)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# ✅ ADDED: Admin site customization
admin.site.site_header = "InventoryPro Administration"
admin.site.site_title = "InventoryPro Admin Panel"
admin.site.index_title = "Welcome to InventoryPro Management System"