#!/usr/bin/env python3
"""
Скрипт для проверки безопасности и готовности Django-приложения к продакшену.
"""
import os
import sys
from pathlib import Path

# --- Настройка путей и Django ---
# Убедимся, что скрипт можно запускать из корня проекта
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

try:
    import django

    django.setup()
    from django.conf import settings
    from django.db import connection
    from django.core.management import call_command, CommandError
except ImportError as e:
    print(f"КРИТИЧЕСКАЯ ОШИБКА: Не удалось настроить Django. Убедитесь, что все зависимости установлены. {e}")
    sys.exit(1)


# --- Классы для форматирования вывода ---
class Color:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    NC = '\033[0m'  # No Color


# --- Основной класс проверки ---
class SecurityChecker:
    def __init__(self):
        self.errors = 0
        self.warnings = 0
        print("=" * 60)
        print("Запуск проверки безопасности и конфигурации")
        print("=" * 60)

    def run_check(self, title, check_function):
        print(f"\n{title}")
        try:
            check_function()
        except Exception as e:
            self._log('error', f"Во время проверки произошла непредвиденная ошибка: {e}")

    def _log(self, level, message):
        if level == 'error':
            print(f"  {Color.RED} ERROR:{Color.NC} {message}")
            self.errors += 1
        elif level == 'warning':
            print(f"  {Color.YELLOW} WARNING:{Color.NC} {message}")
            self.warnings += 1
        elif level == 'success':
            print(f"  {Color.GREEN} OK:{Color.NC} {message}")

    def check_django_settings(self):
        # Проверка DEBUG
        if settings.DEBUG:
            self._log('error', "DEBUG включен. Это КРИТИЧЕСКИ небезопасно для продакшена!")
        else:
            self._log('success', "DEBUG отключен.")

        # Проверка SECRET_KEY
        if len(settings.SECRET_KEY) < 50 or 'insecure' in settings.SECRET_KEY:
            self._log('error', "SECRET_KEY слабый или используется значение по умолчанию.")
        else:
            self._log('success', "SECRET_KEY выглядит надежным.")

        # Проверка ALLOWED_HOSTS
        if '*' in settings.ALLOWED_HOSTS:
            self._log('error', "ALLOWED_HOSTS содержит '*', что разрешает любые хосты.")
        elif not settings.ALLOWED_HOSTS:
            self._log('warning', "ALLOWED_HOSTS пуст. Укажите домен вашего сайта.")
        else:
            self._log('success', f"ALLOWED_HOSTS настроен: {settings.ALLOWED_HOSTS}")

    def check_database(self):
        try:
            connection.ensure_connection()
            self._log('success', "Подключение к базе данных успешно.")
        except Exception as e:
            self._log('error', f"Не удалось подключиться к базе данных: {e}")

    def check_static_files(self):
        if not settings.STATIC_ROOT:
            self._log('error', "Переменная STATIC_ROOT не определена в настройках.")
        else:
            self._log('success', f"STATIC_ROOT определен: {settings.STATIC_ROOT}")

    def check_prod_security_headers(self):
        if not settings.DEBUG:
            if not getattr(settings, 'SESSION_COOKIE_SECURE', False):
                self._log('warning', "SESSION_COOKIE_SECURE не установлен в True для продакшена.")
            else:
                self._log('success', "SESSION_COOKIE_SECURE=True.")

            if not getattr(settings, 'CSRF_COOKIE_SECURE', False):
                self._log('warning', "CSRF_COOKIE_SECURE не установлен в True для продакшена.")
            else:
                self._log('success', "CSRF_COOKIE_SECURE=True.")
        else:
            self._log('info', "Проверка security headers пропускается в DEBUG режиме.")

    def run_django_system_check(self):
        try:
            call_command('check', '--deploy')
            self._log('success', "Встроенная проверка Django (`check --deploy`) прошла без ошибок.")
        except CommandError as e:
            self._log('error', f"Встроенная проверка Django нашла проблемы:\n{e}")

    def generate_report(self):
        print("\n" + "=" * 60)
        print("Итоги проверки")
        print("=" * 60)
        print(f"  {Color.RED}Критических ошибок: {self.errors}{Color.NC}")
        print(f"  {Color.YELLOW}Предупреждений: {self.warnings}{Color.NC}")

        print("-" * 60)
        if self.errors > 0:
            print(f"{Color.RED}РЕЗУЛЬТАТ: Проверка НЕ пройдена. Исправьте ошибки перед деплоем!{Color.NC}")
            return False
        elif self.warnings > 0:
            print(
                f"{Color.YELLOW}РЕЗУЛЬТАТ: Проверка пройдена, но есть предупреждения. Рекомендуется их исправить.{Color.NC}")
            return True
        else:
            print(f"{Color.GREEN}РЕЗУЛЬТАТ: Отлично! Все основные проверки пройдены.{Color.NC}")
            return True


def main():
    checker = SecurityChecker()
    checker.run_check("Основные настройки Django (DEBUG, SECRET_KEY, ALLOWED_HOSTS)", checker.check_django_settings)
    checker.run_check("Подключение к базе данных", checker.check_database)
    checker.run_check("Настройки статических файлов", checker.check_static_files)
    checker.run_check("Заголовки безопасности для продакшена", checker.check_prod_security_headers)
    checker.run_check("Встроенная проверка Django", checker.run_django_system_check)

    is_ok = checker.generate_report()

    if not is_ok:
        sys.exit(1)  # Завершаем с кодом ошибки, если есть проблемы


if __name__ == '__main__':
    main()
