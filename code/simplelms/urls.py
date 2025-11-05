from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin Panel
    path('admin/', admin.site.urls),
    
    # Silk Profiler
    path('silk/', include('silk.urls', namespace='silk')),
    
    # Main App
    path('', include('core.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Admin customization
admin.site.site_header = "InventoryPro Administration"
admin.site.site_title = "InventoryPro Admin Panel"
admin.site.index_title = "Welcome to InventoryPro Management System"