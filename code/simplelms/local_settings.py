# simplelms/local_settings.py
import os

# POSTGRESQL FOR DOCKER (konfigurasi sesuai docker-compose)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        # Menggunakan kredensial dari docker-compose.yml sebagai default
        'NAME': os.environ.get('POSTGRES_DB', 'simple_lms'),
        'USER': os.environ.get('POSTGRES_USER', 'simple_user'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'simple_password'),
        # Mengubah HOST agar sesuai dengan nama service
        'HOST': os.environ.get('DATABASE_HOST', 'postgres'),  # 'postgres' adalah nama service
        'PORT': '5432',
    }
}