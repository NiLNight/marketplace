"""
Скрипт для генерации безопасного SECRET_KEY для Django.

Генерирует криптографически стойкий ключ и предоставляет инструкции
по его добавлению в файлы переменных окружения.
"""

import os
import sys
import secrets
import string
from pathlib import Path
from typing import Optional


def generate_secret_key(length: int = 50) -> str:
    """
    Генерирует криптографически стойкий SECRET_KEY.
    
    Args:
        length (int): Длина ключа. По умолчанию 50 символов.
    
    Returns:
        str: Сгенерированный SECRET_KEY.
    """
    # Используем безопасные символы для Django SECRET_KEY
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*(-_=+)"

    # Генерируем ключ с использованием secrets для криптографической стойкости
    secret_key = ''.join(secrets.choice(alphabet) for _ in range(length))

    return secret_key


def check_existing_secret_key() -> Optional[str]:
    """
    Проверяет существующий SECRET_KEY в переменных окружения.
    
    Returns:
        Optional[str]: Существующий ключ или None.
    """
    # Проверяем переменную окружения
    existing_key = os.getenv('SECRET_KEY')
    if existing_key and existing_key != 'your-secret-key-here':
        return existing_key

    # Проверяем .env файлы
    env_files = ['.env', '.env.prod']

    for env_file in env_files:
        env_path = Path(env_file)
        if env_path.exists():
            try:
                with open(env_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith('SECRET_KEY='):
                            key = line.split('=', 1)[1].strip('"\'')
                            if key and key != 'your-secret-key-here':
                                return key
            except Exception as e:
                print(f"⚠️  Ошибка чтения {env_file}: {e}")

    return None


def update_env_file(env_file: str, new_key: str) -> bool:
    """
    Обновляет SECRET_KEY в файле переменных окружения.
    
    Args:
        env_file (str): Путь к файлу переменных окружения.
        new_key (str): Новый SECRET_KEY.
    
    Returns:
        bool: True если обновление прошло успешно.
    """
    env_path = Path(env_file)

    if not env_path.exists():
        print(f"❌ Файл {env_file} не существует")
        return False

    try:
        # Читаем содержимое файла
        with open(env_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Ищем строку с SECRET_KEY
        secret_key_found = False
        for i, line in enumerate(lines):
            if line.strip().startswith('SECRET_KEY='):
                lines[i] = f'SECRET_KEY="{new_key}"\n'
                secret_key_found = True
                break

        # Если SECRET_KEY не найден, добавляем его в конец
        if not secret_key_found:
            lines.append(f'\n# Django Secret Key\nSECRET_KEY="{new_key}"\n')

        # Записываем обновленный файл
        with open(env_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ SECRET_KEY обновлен в {env_file}")
        return True

    except Exception as e:
        print(f"❌ Ошибка обновления {env_file}: {e}")
        return False


def create_env_file(env_file: str, new_key: str) -> bool:
    """
    Создает новый файл переменных окружения с SECRET_KEY.
    
    Args:
        env_file (str): Путь к файлу переменных окружения.
        new_key (str): Новый SECRET_KEY.
    
    Returns:
        bool: True если создание прошло успешно.
    """
    env_path = Path(env_file)

    if env_path.exists():
        print(f"⚠️  Файл {env_file} уже существует")
        return False

    try:
        # Создаем базовый .env файл
        env_content = f"""# Django Settings
SECRET_KEY="{new_key}"
DEBUG=True
ENVIRONMENT=development

# Database Settings
DB_ENGINE=django.db.backends.postgresql
DB_HOST=localhost
DB_PORT=5432
DB_NAME=marketplace_dev
DB_USER=marketplace_user
DB_PASS=your-password

# Redis Settings
REDIS_HOST=localhost
REDIS_PORT=6379

# RabbitMQ Settings
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672

# Elasticsearch Settings
ELASTICSEARCH_HOSTS=localhost:9200

# Email Settings
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-email-password

# Frontend URL
FRONTEND_URL=http://localhost:3000

# Grafana Password (для продакшена)
GRAFANA_PASSWORD=admin123
"""

        with open(env_path, 'w', encoding='utf-8') as f:
            f.write(env_content)

        print(f"✅ Создан новый файл {env_file}")
        return True

    except Exception as e:
        print(f"❌ Ошибка создания {env_file}: {e}")
        return False


def main():
    """Основная функция."""
    print("🔐 Генератор SECRET_KEY для Django")
    print("=" * 50)

    # Проверяем существующий ключ
    existing_key = check_existing_secret_key()
    if existing_key:
        print(f"📝 Найден существующий SECRET_KEY: {existing_key[:20]}...")
        response = input("Хотите сгенерировать новый ключ? (y/N): ").lower()
        if response != 'y':
            print("✅ Используется существующий ключ")
            return 0

    # Генерируем новый ключ
    print("\n🔑 Генерация нового SECRET_KEY...")
    new_key = generate_secret_key()

    print(f"📝 Новый SECRET_KEY: {new_key}")
    print(f"📏 Длина: {len(new_key)} символов")
    print(f"🔒 Криптографическая стойкость: ✅")

    # Проверяем файлы переменных окружения
    env_files = []
    if Path('.env').exists():
        env_files.append('.env')
    if Path('.env.prod').exists():
        env_files.append('.env.prod')

    if env_files:
        print(f"\n📁 Найдены файлы переменных окружения: {', '.join(env_files)}")

        for env_file in env_files:
            response = input(f"Обновить SECRET_KEY в {env_file}? (y/N): ").lower()
            if response == 'y':
                if update_env_file(env_file, new_key):
                    print(f"✅ {env_file} обновлен")
                else:
                    print(f"❌ Ошибка обновления {env_file}")
    else:
        print("\n📁 Файлы переменных окружения не найдены")
        print("Создать новый .env файл?")
        response = input("Выберите файл для создания (.env/.env.prod): ").strip()

        if response in ['.env', '.env.prod']:
            if create_env_file(response, new_key):
                print(f"✅ Создан {response}")
            else:
                print(f"❌ Ошибка создания {response}")
        else:
            print("❌ Неверный выбор файла")

    print("\n📋 Инструкции:")
    print("1. Скопируйте SECRET_KEY в ваш .env файл")
    print("2. Убедитесь, что .env файл добавлен в .gitignore")
    print("3. Перезапустите приложение после изменения SECRET_KEY")
    print("4. В продакшене используйте .env.prod файл")

    print("\n🔒 Рекомендации безопасности:")
    print("- Никогда не коммитьте SECRET_KEY в git")
    print("- Используйте разные ключи для разработки и продакшена")
    print("- Регулярно обновляйте SECRET_KEY")
    print("- Храните резервные копии .env файлов в безопасном месте")

    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n❌ Операция прервана пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {e}")
        sys.exit(1)
