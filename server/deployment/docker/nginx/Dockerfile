# deployment/docker/nginx/Dockerfile
# Используем легковесный образ Nginx на основе Alpine Linux.
FROM nginx:1.25-alpine

# Удаляем стандартную конфигурацию Nginx, чтобы избежать конфликтов.
RUN rm /etc/nginx/conf.d/default.conf

# Копируем нашу собственную конфигурацию в нужное место.
# Nginx автоматически подхватит все .conf файлы из этой директории.
COPY nginx.conf /etc/nginx/conf.d/default.conf