#!/bin/bash

# 🚀 Автоматический скрипт деплоя Marketplace (Production VPS Edition)
set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${PURPLE}[STEP]${NC} $1"; }

# Пути проекта
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
SERVER_DIR="$PROJECT_ROOT/server"

# Команда Docker Compose для нашего Продакшена
DC="docker compose -p server_prod --env-file .env.prod -f docker-compose.prod.yml"

check_environment() {
    log_step "Проверка переменных окружения .env.prod..."
    cd "$SERVER_DIR"

    if [ ! -f ".env.prod" ]; then
        log_error "Файл .env.prod не найден в $SERVER_DIR!"
        exit 1
    fi

    log_success "Переменные окружения найдены"
}

create_backup() {
    log_step "Создание резервной копии базы данных..."
    BACKUP_DIR="$SERVER_DIR/backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"

    if $DC ps | grep -q "db"; then
        log_info "Создание дампа PostgreSQL..."
        $DC exec -T db pg_dump -U marketplace_user marketplace_prod > "$BACKUP_DIR/database.sql" 2>/dev/null || log_warning "БД еще не была создана, пропускаем дамп"
    fi
    log_success "Резервная копия сохранена в $BACKUP_DIR"
}

stop_containers() {
    log_step "Остановка контейнеров..."
    $DC down --remove-orphans
    log_success "Контейнеры остановлены"
}

build_images() {
    log_step "Сборка Docker образов (с использованием кеша для экономии диска)..."
    # Собираем С ИСПОЛЬЗОВАНИЕМ кеша, чтобы не заполнять 10 ГБ диск
    $DC build
    log_success "Образы успешно собраны"
}

start_services() {
    log_step "Запуск продакшен-сервисов..."
    $DC up -d
    log_success "Сервисы запущены"
}

wait_for_services() {
    log_step "Ожидание готовности PostgreSQL, Redis и Elasticsearch..."

    log_info "Ожидание базы данных..."
    timeout=60
    while [ $timeout -gt 0 ]; do
        if $DC exec -T db pg_isready -U marketplace_user -d marketplace_prod &>/dev/null; then
            break
        fi
        sleep 1
        timeout=$((timeout - 1))
    done

    log_info "Ожидание Redis..."
    timeout=30
    while [ $timeout -gt 0 ]; do
        if $DC exec -T redis redis-cli ping &>/dev/null; then
            break
        fi
        sleep 1
        timeout=$((timeout - 1))
    done

    log_success "Основные сервисы готовы"
}

run_migrations() {
    log_step "Применение миграций Django..."
    $DC exec -T backend python manage.py migrate --noinput
    log_success "Миграции применены"
}

collect_static() {
    log_step "Сборка статических файлов..."
    $DC exec -T backend python manage.py collectstatic --noinput --clear
    log_success "Статика собрана"
}

health_check() {
    log_step "Проверка работоспособности приложения (Healthcheck)..."
    timeout=30
    while [ $timeout -gt 0 ]; do
        if curl -f -k https://localhost/core/health/ &>/dev/null || curl -f http://localhost:8000/core/health/ &>/dev/null; then
            break
        fi
        sleep 2
        timeout=$((timeout - 2))
    done

    if [ $timeout -eq 0 ]; then
        log_error "Приложение не отвечает на /core/health/!"
        exit 1
    fi
    log_success "Приложение работает отлично!"
}

cleanup_disk() {
    log_step "Очистка временного кеша Docker для сохранения свободного места..."
    docker system prune -f
    journalctl --vacuum-time=1d &>/dev/null || true
    log_success "Очистка диска завершена"
}

show_status() {
    log_info "Текущий статус контейнеров:"
    $DC ps
}

main() {
    echo "🚀 Запуск продакшен-деплоя Marketplace"
    echo "========================================"

    cd "$SERVER_DIR"
    check_environment
    create_backup
    stop_containers
    build_images
    start_services
    wait_for_services
    run_migrations
    collect_static
    health_check
    cleanup_disk
    show_status

    echo ""
    echo "🎉 Деплой успешно завершен!"
    echo "Сайт доступен: https://nilplace.space"
    echo "========================================"
}

case "${1:-}" in
    "status") $DC ps ;;
    "logs") $DC logs -f "${2:-}" ;;
    "restart") $DC restart ;;
    "stop") $DC down ;;
    "build") $DC build ;;
    "migrate") run_migrations ;;
    "clean") cleanup_disk ;;
    *) main ;;
esac