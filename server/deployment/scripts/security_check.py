#!/usr/bin/env python3
"""
Скрипт для проверки безопасности и готовности Django-приложения к продакшену.
"""
import os
import sys
from pathlib import Path

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
    print(f"КРИТИЧЕСКАЯ ОШИБКА: Не удалось настроить Django. {e}")
    sys.exit(1)


class Color:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    NC = '\033[0m'


class SecurityChecker:
    def __init__(self):
        self.errors = 0
        self.warnings = 0
        print("=" * 60)
        print("Запуск проверки безопасности и конфигурации Marketplace")
        print("=" * 60)

    def run_check(self, title, check_function):
        print(f"\n{title}")
        try:
            check_function()
        except Exception as e:
            self._log('error', f"Во время проверки произошла ошибка: {e}")

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
        if settings.DEBUG:
            self._log('error', "DEBUG включен! Это небезопасно для продакшена!")
        else:
            self._log('success', "DEBUG отключен.")

        if len(settings.SECRET_KEY) < 30 or 'insecure' in settings.SECRET_KEY:
            self._log('error', "SECRET_KEY слабый или используется значение по умолчанию.")
        else:
            self._log('success', "SECRET_KEY выглядит надежным.")

        if '*' in settings.ALLOWED_HOSTS:
            self._log('error', "ALLOWED_HOSTS содержит '*', что разрешает любые хосты.")
        elif not settings.ALLOWED_HOSTS:
            self._log('warning', "ALLOWED_HOSTS пуст.")
        else:
            self._log('success', f"ALLOWED_HOSTS настроен: {settings.ALLOWED_HOSTS}")

    def check_database(self):
        try:
            connection.ensure_connection()
            self._log('success', "Подключение к базе данных PostgreSQL успешно.")
        except Exception as e:
            self._log('error', f"Не удалось подключиться к БД: {e}")

    def check_prod_security_headers(self):
        if not settings.DEBUG:
            if not getattr(settings, 'SESSION_COOKIE_SECURE', False):
                self._log('warning', "SESSION_COOKIE_SECURE не равен True.")
            else:
                self._log('success', "SESSION_COOKIE_SECURE=True.")

            if not getattr(settings, 'CSRF_COOKIE_SECURE', False):
                self._log('warning', "CSRF_COOKIE_SECURE не равен True.")
            else:
                self._log('success', "CSRF_COOKIE_SECURE=True.")

    def run_django_system_check(self):
        try:
            call_command('check', '--deploy')
            self._log('success', "Встроенная проверка Django (`check --deploy`) прошла без ошибок.")
        except CommandError as e:
            self._log('warning', f"Встроенная проверка Django нашла замечания:\n{e}")

    def generate_report(self):
        print("\n" + "=" * 60)
        print("Итоги проверки безопасности")
        print("=" * 60)
        print(f"  {Color.RED}Ошибок: {self.errors}{Color.NC}")
        print(f"  {Color.YELLOW}Предупреждений: {self.warnings}{Color.NC}")

        if self.errors > 0:
            print(f"{Color.RED}РЕЗУЛЬТАТ: Проверка НЕ пройдена. Исправьте ошибки!{Color.NC}")
            return False
        else:
            print(f"{Color.GREEN}РЕЗУЛЬТАТ: Отлично! Все ключевые проверки безопасности пройдены.{Color.NC}")
            return True


def main():
    checker = SecurityChecker()
    checker.run_check("Основные настройки Django", checker.check_django_settings)
    checker.run_check("Подключение к PostgreSQL", checker.check_database)
    checker.run_check("Заголовки безопасности HTTPS/Cookies", checker.check_prod_security_headers)
    checker.run_check("Встроенная проверка Django", checker.run_django_system_check)

    if not checker.generate_report():
        sys.exit(1)


if __name__ == '__main__':
    main()