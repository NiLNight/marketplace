#!/usr/bin/env python3
"""
Скрипт для проверки безопасности Django приложения.

Проверяет:
- Настройки Django
- Зависимости
- Middleware
- База данных
- Статические файлы
- Логирование
- SSL/TLS
- Rate limiting
- CORS настройки
"""

import os
import sys
import subprocess
import importlib
from pathlib import Path
from typing import List, Tuple, Dict, Any

# Добавляем путь к проекту
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Настройки Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

try:
import django
django.setup()
from django.conf import settings
from django.core.management import execute_from_command_line
    from django.core.management.base import CommandError
except ImportError as e:
    print(f"❌ Ошибка: Django не установлен или не настроен: {e}")
    sys.exit(1)

class SecurityChecker:
    """Класс для проверки безопасности Django приложения."""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.success = []
        
    def log_error(self, message: str):
        """Добавляет ошибку."""
        self.errors.append(message)
        print(f"❌ {message}")
    
    def log_warning(self, message: str):
        """Добавляет предупреждение."""
        self.warnings.append(message)
        print(f"⚠️  {message}")
    
    def log_success(self, message: str):
        """Добавляет успешную проверку."""
        self.success.append(message)
        print(f"✅ {message}")
    
    def check_django_settings(self) -> None:
        """Проверяет настройки Django."""
        print("\n🔒 Проверка настроек Django:")
        
        # Проверка DEBUG
        if settings.DEBUG:
            self.log_warning("DEBUG=True - отключите в продакшене")
    else:
            self.log_success("DEBUG=False - правильно для продакшена")
        
        # Проверка SECRET_KEY
        if len(settings.SECRET_KEY) < 50:
            self.log_error("SECRET_KEY слишком короткий")
        elif 'django-insecure' in settings.SECRET_KEY:
            self.log_error("SECRET_KEY содержит небезопасный префикс")
        else:
            self.log_success("SECRET_KEY соответствует требованиям")
        
        # Проверка ALLOWED_HOSTS
        if not settings.ALLOWED_HOSTS:
            self.log_error("ALLOWED_HOSTS не настроен")
        elif '*' in settings.ALLOWED_HOSTS:
            self.log_warning("ALLOWED_HOSTS содержит '*' - небезопасно")
        else:
            self.log_success("ALLOWED_HOSTS настроен правильно")
        
        # Проверка HTTPS настроек
        if hasattr(settings, 'SECURE_SSL_REDIRECT') and settings.SECURE_SSL_REDIRECT:
            self.log_success("HTTPS редирект включен")
        else:
            self.log_warning("HTTPS редирект не включен")
        
        # Проверка HSTS
        if hasattr(settings, 'SECURE_HSTS_SECONDS') and settings.SECURE_HSTS_SECONDS > 0:
            self.log_success("HSTS настроен")
    else:
            self.log_warning("HSTS не настроен")
        
        # Проверка безопасных cookies
        if hasattr(settings, 'SESSION_COOKIE_SECURE') and settings.SESSION_COOKIE_SECURE:
            self.log_success("Безопасные сессионные cookies")
        else:
            self.log_warning("Сессионные cookies не защищены")
        
        if hasattr(settings, 'CSRF_COOKIE_SECURE') and settings.CSRF_COOKIE_SECURE:
            self.log_success("Безопасные CSRF cookies")
    else:
            self.log_warning("CSRF cookies не защищены")

    def check_middleware(self) -> None:
        """Проверяет middleware."""
        print("\n🛡️  Проверка Middleware:")
        
        middleware = getattr(settings, 'MIDDLEWARE', [])
        
        # Проверка SecurityMiddleware
        if 'django.middleware.security.SecurityMiddleware' in middleware:
            self.log_success("SecurityMiddleware включен")
        else:
            self.log_error("SecurityMiddleware не включен")
        
        # Проверка CSRF
        if 'django.middleware.csrf.CsrfViewMiddleware' in middleware:
            self.log_success("CSRF middleware включен")
        else:
            self.log_error("CSRF middleware не включен")
        
        # Проверка XSS
        if 'django.middleware.security.SecurityMiddleware' in middleware:
            self.log_success("XSS защита включена")
    else:
            self.log_warning("XSS защита не настроена")
        
        # Проверка Clickjacking
        if 'django.middleware.clickjacking.XFrameOptionsMiddleware' in middleware:
            self.log_success("Clickjacking защита включена")
        else:
            self.log_warning("Clickjacking защита не настроена")
    
    def check_dependencies(self) -> None:
        """Проверяет зависимости на уязвимости."""
        print("\n📦 Проверка зависимостей:")
        
        try:
            # Проверяем наличие safety
            result = subprocess.run(['safety', 'check'], capture_output=True, text=True)
            if result.returncode == 0:
                self.log_success("Зависимости не содержат известных уязвимостей")
            else:
                self.log_warning("Обнаружены потенциальные уязвимости в зависимостях")
                print(result.stdout)
        except FileNotFoundError:
            self.log_warning("safety не установлен. Установите: pip install safety")
        
        # Проверяем критические зависимости
        critical_deps = [
            'django',
            'psycopg2-binary',
            'redis',
            'celery',
            'elasticsearch-dsl',
            'gunicorn'
        ]
        
        for dep in critical_deps:
            try:
                importlib.import_module(dep.replace('-', '_'))
                self.log_success(f"{dep} установлен")
            except ImportError:
                self.log_error(f"{dep} не установлен")
    
    def check_database(self) -> None:
        """Проверяет настройки базы данных."""
        print("\n🗄️  Проверка базы данных:")
        
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT version();")
                version = cursor.fetchone()[0]
                self.log_success(f"База данных доступна: {version}")
        except Exception as e:
            self.log_error(f"Ошибка подключения к БД: {e}")
        
        # Проверка SSL для БД
        db_settings = settings.DATABASES['default']
        if 'OPTIONS' in db_settings and 'sslmode' in db_settings['OPTIONS']:
            if db_settings['OPTIONS']['sslmode'] == 'require':
                self.log_success("SSL для БД включен")
            else:
                self.log_warning("SSL для БД не настроен")
        else:
            self.log_warning("SSL для БД не настроен")
    
    def check_static_files(self) -> None:
        """Проверяет статические файлы."""
        print("\n📁 Проверка статических файлов:")
        
        static_root = getattr(settings, 'STATIC_ROOT', None)
        if static_root and os.path.exists(static_root):
            self.log_success("STATIC_ROOT настроен и существует")
    else:
            self.log_warning("STATIC_ROOT не настроен или не существует")
        
        # Проверяем наличие collectstatic
        try:
            from django.core.management import call_command
            call_command('collectstatic', '--dry-run', verbosity=0)
            self.log_success("collectstatic работает")
        except Exception as e:
            self.log_error(f"Ошибка collectstatic: {e}")
    
    def check_logging(self) -> None:
        """Проверяет настройки логирования."""
        print("\n📝 Проверка логирования:")
        
        if hasattr(settings, 'LOGGING') and settings.LOGGING:
            self.log_success("Логирование настроено")
        else:
            self.log_warning("Логирование не настроено")
        
        # Проверяем файлы логов
        log_dir = Path('logs')
        if log_dir.exists():
            self.log_success("Директория логов существует")
        else:
            self.log_warning("Директория логов не существует")

    def check_rate_limiting(self) -> None:
        """Проверяет rate limiting."""
        print("\n🚦 Проверка Rate Limiting:")
        
        # Проверяем Django REST Framework throttling
        if 'rest_framework' in settings.INSTALLED_APPS:
            drf_settings = getattr(settings, 'REST_FRAMEWORK', {})
            if 'DEFAULT_THROTTLE_CLASSES' in drf_settings:
                self.log_success("DRF throttling настроен")
            else:
                self.log_warning("DRF throttling не настроен")
        else:
            self.log_warning("Django REST Framework не установлен")
    
    def check_cors(self) -> None:
        """Проверяет CORS настройки."""
        print("\n🌐 Проверка CORS:")
        
        if 'corsheaders' in settings.INSTALLED_APPS:
            cors_settings = getattr(settings, 'CORS_ALLOWED_ORIGINS', [])
            if cors_settings:
                self.log_success("CORS origins настроены")
            else:
                self.log_warning("CORS origins не настроены")
        else:
            self.log_warning("django-cors-headers не установлен")
    
    def check_ssl_certificates(self) -> None:
        """Проверяет SSL сертификаты."""
        print("\n🔐 Проверка SSL сертификатов:")
        
        ssl_dir = Path('deployment/ssl')
        if ssl_dir.exists():
            cert_file = ssl_dir / 'marketplace.crt'
            key_file = ssl_dir / 'marketplace.key'
            
            if cert_file.exists() and key_file.exists():
                self.log_success("SSL сертификаты найдены")
            else:
                self.log_warning("SSL сертификаты не найдены")
        else:
            self.log_warning("Директория SSL не существует")
    
    def run_django_check(self) -> None:
        """Запускает Django check --deploy."""
        print("\n🔍 Запуск Django check --deploy:")
        
        try:
            from django.core.management import call_command
            call_command('check', '--deploy')
            self.log_success("Django check --deploy пройден")
        except Exception as e:
            self.log_error(f"Django check --deploy не пройден: {e}")
    
    def check_environment_variables(self) -> None:
        """Проверяет переменные окружения."""
        print("\n🌍 Проверка переменных окружения:")
        
        required_vars = [
            'SECRET_KEY',
            'DB_HOST',
            'DB_NAME',
            'DB_USER',
            'DB_PASS',
            'REDIS_HOST',
            'RABBITMQ_HOST'
        ]
        
        for var in required_vars:
            if os.getenv(var):
                self.log_success(f"{var} установлен")
            else:
                self.log_error(f"{var} не установлен")
        
        # Проверяем наличие .env файлов
        env_files = []
        if Path('.env').exists():
            env_files.append('.env')
        if Path('.env.prod').exists():
            env_files.append('.env.prod')
        
        if env_files:
            self.log_success(f"Найдены файлы переменных окружения: {', '.join(env_files)}")
        else:
            self.log_error("Файлы .env или .env.prod не найдены")
    
    def generate_report(self) -> None:
        """Генерирует отчет о проверке."""
        print("\n" + "="*60)
        print("📊 ОТЧЕТ О ПРОВЕРКЕ БЕЗОПАСНОСТИ")
        print("="*60)
        
        print(f"\n✅ Успешных проверок: {len(self.success)}")
        print(f"⚠️  Предупреждений: {len(self.warnings)}")
        print(f"❌ Ошибок: {len(self.errors)}")
        
        if self.errors:
            print("\n❌ КРИТИЧЕСКИЕ ОШИБКИ:")
            for error in self.errors:
                print(f"  - {error}")
        
        if self.warnings:
            print("\n⚠️  ПРЕДУПРЕЖДЕНИЯ:")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        if self.success:
            print("\n✅ УСПЕШНЫЕ ПРОВЕРКИ:")
            for success in self.success[:10]:  # Показываем первые 10
                print(f"  - {success}")
            if len(self.success) > 10:
                print(f"  ... и еще {len(self.success) - 10} проверок")
        
        print("\n" + "="*60)
        
        if self.errors:
            print("❌ Проверка безопасности НЕ ПРОЙДЕНА!")
            return False
        elif self.warnings:
            print("⚠️  Проверка безопасности пройдена с предупреждениями")
            return True
        else:
            print("✅ Проверка безопасности пройдена успешно!")
            return True
    
    def run_all_checks(self) -> bool:
        """Запускает все проверки."""
        print("🔒 Запуск проверки безопасности Django приложения")
        print("="*60)
        
        self.check_environment_variables()
        self.check_django_settings()
        self.check_middleware()
        self.check_dependencies()
        self.check_database()
        self.check_static_files()
        self.check_logging()
        self.check_rate_limiting()
        self.check_cors()
        self.check_ssl_certificates()
        self.run_django_check()
        
        return self.generate_report()

def main():
    """Основная функция."""
    checker = SecurityChecker()
    success = checker.run_all_checks()
    
    if success:
        print("\n🎯 Рекомендации:")
        print("- Исправьте все критические ошибки")
        print("- Рассмотрите предупреждения")
        print("- Регулярно обновляйте зависимости")
        print("- Мониторьте логи на предмет подозрительной активности")
        print("- Настройте автоматические резервные копии")
        print("- Используйте HTTPS в продакшене")
        print("- Настройте мониторинг безопасности")
    
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main()) 