#!/bin/bash

# 🚀 Автоматический скрипт деплоя Marketplace
# Включает проверки безопасности и мониторинг

set -e  # Остановка при ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Функции для вывода
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

log_debug() {
    echo -e "${CYAN}[DEBUG]${NC} $1"
}

# Определяем пути
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DEPLOYMENT_DIR="$PROJECT_ROOT/deployment"

# Проверка наличия необходимых файлов
check_prerequisites() {
    log_step "Проверка предварительных требований..."
    
    # Проверка наличия .env файлов
    if [ ! -f "$PROJECT_ROOT/.env" ] && [ ! -f "$PROJECT_ROOT/.env.prod" ]; then
        log_error "Файлы .env или .env.prod не найдены!"
        log_info "Создайте один из файлов:"
        log_info "  - .env для разработки"
        log_info "  - .env.prod для продакшена"
        log_info ""
        log_info "Пример структуры .env файла:"
        log_info "SECRET_KEY=your-secret-key"
        log_info "DEBUG=True"
        log_info "ENVIRONMENT=development"
        log_info "DB_HOST=localhost"
        log_info "DB_NAME=marketplace_dev"
        log_info "DB_USER=marketplace_user"
        log_info "DB_PASS=your-password"
        log_info "REDIS_HOST=localhost"
        log_info "RABBITMQ_HOST=localhost"
        log_info "ELASTICSEARCH_HOSTS=localhost:9200"
        exit 1
    fi
    
    # Проверка наличия docker-compose файлов
    if [ ! -f "$PROJECT_ROOT/docker-compose.yml" ]; then
        log_error "docker-compose.yml не найден!"
        exit 1
    fi
    
    # Проверка Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker не установлен!"
        exit 1
    fi
    
    # Проверка Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose не установлен!"
        exit 1
    fi
    
    # Проверка SSL сертификатов для продакшена
    if [ "$ENVIRONMENT" = "production" ]; then
        if [ ! -f "$DEPLOYMENT_DIR/ssl/marketplace.crt" ] || [ ! -f "$DEPLOYMENT_DIR/ssl/marketplace.key" ]; then
            log_warning "SSL сертификаты не найдены. Создайте их или используйте самоподписанные для тестирования."
        fi
    fi
    
    log_success "Предварительные требования выполнены"
}

# Создание резервной копии
create_backup() {
    log_step "Создание резервной копии..."
    
    BACKUP_DIR="$PROJECT_ROOT/backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # Резервное копирование базы данных
    if docker-compose ps | grep -q "db"; then
        log_info "Создание резервной копии базы данных..."
        docker-compose exec -T db pg_dump -U $DB_USER $DB_NAME > "$BACKUP_DIR/database.sql" 2>/dev/null || log_warning "Не удалось создать резервную копию БД"
    fi
    
    # Резервное копирование медиа файлов
    if [ -d "$PROJECT_ROOT/media" ]; then
        log_info "Создание резервной копии медиа файлов..."
        tar -czf "$BACKUP_DIR/media.tar.gz" -C "$PROJECT_ROOT" media/ 2>/dev/null || log_warning "Не удалось создать резервную копию медиа файлов"
    fi
    
    # Резервное копирование статических файлов
    if [ -d "$PROJECT_ROOT/static" ]; then
        log_info "Создание резервной копии статических файлов..."
        tar -czf "$BACKUP_DIR/static.tar.gz" -C "$PROJECT_ROOT" static/ 2>/dev/null || log_warning "Не удалось создать резервную копию статических файлов"
    fi
    
    # Резервное копирование .env файлов
    if [ -f "$PROJECT_ROOT/.env" ]; then
        cp "$PROJECT_ROOT/.env" "$BACKUP_DIR/.env.backup"
    fi
    if [ -f "$PROJECT_ROOT/.env.prod" ]; then
        cp "$PROJECT_ROOT/.env.prod" "$BACKUP_DIR/.env.prod.backup"
    fi
    
    log_success "Резервная копия создана в $BACKUP_DIR"
}

# Остановка существующих контейнеров
stop_containers() {
    log_step "Остановка существующих контейнеров..."
    
    docker-compose down --remove-orphans
    
    log_success "Контейнеры остановлены"
}

# Сборка образов
build_images() {
    log_step "Сборка Docker образов..."
    
    # Определяем docker-compose файл
    COMPOSE_FILE="docker-compose.yml"
    if [ "$ENVIRONMENT" = "production" ]; then
        COMPOSE_FILE="docker-compose.prod.yml"
    fi
    
    docker-compose -f "$COMPOSE_FILE" build --no-cache
    
    log_success "Образы собраны"
}

# Запуск сервисов
start_services() {
    log_step "Запуск сервисов..."
    
    # Определяем docker-compose файл
    COMPOSE_FILE="docker-compose.yml"
    if [ "$ENVIRONMENT" = "production" ]; then
        COMPOSE_FILE="docker-compose.prod.yml"
    fi
    
    docker-compose -f "$COMPOSE_FILE" up -d
    
    log_success "Сервисы запущены"
}

# Ожидание готовности сервисов
wait_for_services() {
    log_step "Ожидание готовности сервисов..."
    
    # Ожидание базы данных
    log_info "Ожидание базы данных..."
    timeout=60
    while [ $timeout -gt 0 ]; do
        if docker-compose exec -T db pg_isready -U $DB_USER -d $DB_NAME &>/dev/null; then
            break
        fi
        sleep 1
        timeout=$((timeout - 1))
    done
    
    if [ $timeout -eq 0 ]; then
        log_error "База данных не готова!"
        exit 1
    fi
    
    # Ожидание Redis
    log_info "Ожидание Redis..."
    timeout=30
    while [ $timeout -gt 0 ]; do
        if docker-compose exec -T redis redis-cli ping &>/dev/null; then
            break
        fi
        sleep 1
        timeout=$((timeout - 1))
    done
    
    if [ $timeout -eq 0 ]; then
        log_error "Redis не готов!"
        exit 1
    fi
    
    # Ожидание Elasticsearch
    log_info "Ожидание Elasticsearch..."
    timeout=60
    while [ $timeout -gt 0 ]; do
        if curl -f http://localhost:9200/_cluster/health &>/dev/null; then
            break
        fi
        sleep 2
        timeout=$((timeout - 2))
    done
    
    if [ $timeout -eq 0 ]; then
        log_warning "Elasticsearch не готов, но продолжаем..."
    fi
    
    log_success "Сервисы готовы"
}

# Выполнение миграций
run_migrations() {
    log_step "Выполнение миграций..."
    
    docker-compose exec -T backend python manage.py migrate --noinput
    
    log_success "Миграции выполнены"
}

# Сборка статических файлов
collect_static() {
    log_step "Сборка статических файлов..."
    
    docker-compose exec -T backend python manage.py collectstatic --noinput --clear
    
    log_success "Статические файлы собраны"
}

# Проверка безопасности
security_check() {
    log_step "Проверка безопасности..."
    
    if [ -f "$DEPLOYMENT_DIR/scripts/security_check.py" ]; then
        if python "$DEPLOYMENT_DIR/scripts/security_check.py"; then
            log_success "Проверка безопасности пройдена"
        else
            log_warning "Проверка безопасности не пройдена, но продолжаем..."
        fi
    else
        log_warning "Скрипт проверки безопасности не найден"
    fi
}

# Проверка работоспособности
health_check() {
    log_step "Проверка работоспособности..."
    
    # Ожидание готовности приложения
    timeout=60
    while [ $timeout -gt 0 ]; do
        if curl -f http://localhost:8000/health/ &>/dev/null; then
            break
        fi
        sleep 2
        timeout=$((timeout - 2))
    done
    
    if [ $timeout -eq 0 ]; then
        log_error "Приложение не отвечает!"
        exit 1
    fi
    
    log_success "Приложение работает"
}

# Проверка статуса контейнеров
check_container_status() {
    log_step "Проверка статуса контейнеров..."
    
    if docker-compose ps | grep -q "Up"; then
        log_success "Все контейнеры запущены"
    else
        log_error "Не все контейнеры запущены!"
        docker-compose ps
        exit 1
    fi
}

# Очистка старых образов
cleanup_images() {
    log_step "Очистка старых образов..."
    
    docker image prune -f
    
    log_success "Очистка завершена"
}

# Вывод информации о деплое
show_deployment_info() {
    log_info "Информация о деплое:"
    echo ""
    echo "🌐 Доступные сервисы:"
    echo "   - Приложение: http://localhost:8000"
    echo "   - Nginx: http://localhost:80, https://localhost:443"
    echo "   - Prometheus: http://localhost:9090"
    echo "   - Grafana: http://localhost:3000"
    echo "   - Flower: http://localhost:5555"
    echo ""
    echo "📊 Команды для мониторинга:"
    echo "   - Логи: docker-compose logs"
    echo "   - Статус: docker-compose ps"
    echo "   - Ресурсы: docker stats"
    echo ""
    echo "🔒 Проверка безопасности:"
    echo "   - python deployment/scripts/security_check.py"
    echo ""
    echo "🔄 Обновление:"
    echo "   - ./deployment/scripts/deploy.sh"
    echo ""
}

# Проверка переменных окружения
check_environment() {
    log_step "Проверка переменных окружения..."
    
    # Загружаем переменные из .env файла
    if [ -f "$PROJECT_ROOT/.env" ]; then
        export $(cat "$PROJECT_ROOT/.env" | grep -v '^#' | xargs)
        log_info "Загружены переменные из .env"
    elif [ -f "$PROJECT_ROOT/.env.prod" ]; then
        export $(cat "$PROJECT_ROOT/.env.prod" | grep -v '^#' | xargs)
        log_info "Загружены переменные из .env.prod"
    fi
    
    # Проверяем обязательные переменные
    required_vars=("SECRET_KEY" "DB_HOST" "DB_NAME" "DB_USER" "DB_PASS")
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            log_error "Переменная $var не установлена!"
            exit 1
        fi
    done
    
    log_success "Переменные окружения проверены"
}

# Основная функция
main() {
    echo "🚀 Запуск автоматического деплоя Marketplace"
    echo "=========================================="
    
    # Проверяем окружение
    check_environment
    
    # Выполнение этапов деплоя
    check_prerequisites
    create_backup
    stop_containers
    build_images
    start_services
    wait_for_services
    run_migrations
    collect_static
    security_check
    health_check
    check_container_status
    cleanup_images
    
    echo ""
    echo "🎉 Деплой завершен успешно!"
    echo "=========================================="
    
    show_deployment_info
}

# Обработка аргументов командной строки
case "${1:-}" in
    "backup")
        create_backup
        ;;
    "security")
        security_check
        ;;
    "status")
        docker-compose ps
        ;;
    "logs")
        docker-compose logs "${2:-}"
        ;;
    "restart")
        docker-compose restart
        ;;
    "stop")
        docker-compose down
        ;;
    "build")
        build_images
        ;;
    "migrate")
        run_migrations
        ;;
    "static")
        collect_static
        ;;
    "health")
        health_check
        ;;
    "help"|"-h"|"--help")
        echo "Использование: $0 [команда]"
        echo ""
        echo "Команды:"
        echo "  backup   - Создать резервную копию"
        echo "  security - Запустить проверку безопасности"
        echo "  status   - Показать статус контейнеров"
        echo "  logs     - Показать логи (опционально: имя сервиса)"
        echo "  restart  - Перезапустить все сервисы"
        echo "  stop     - Остановить все сервисы"
        echo "  build    - Собрать образы"
        echo "  migrate  - Выполнить миграции"
        echo "  static   - Собрать статические файлы"
        echo "  health   - Проверить работоспособность"
        echo "  help     - Показать эту справку"
        echo ""
        echo "Без аргументов выполняется полный деплой"
        ;;
    *)
        main
        ;;
esac 