# 🐳 Docker Setup

## Быстрый старт

```bash
# Собрать и запустить все сервисы
docker-compose build
docker-compose up -d

# Применить миграции и собрать статику
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py collectstatic --noinput

# Создать суперпользователя
docker-compose exec web python manage.py createsuperuser
```

Или используйте Makefile:
```bash
make dev          # Полная настройка
make superuser    # Создать админа
```

## Доступ к сервисам

- **Веб-приложение**: http://localhost:8000
- **Flower (Celery)**: http://localhost:5555
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

## Основные команды

```bash
# Управление
docker-compose up -d          # Запустить
docker-compose down           # Остановить
docker-compose ps             # Статус
docker-compose logs -f        # Логи

# Django
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py shell
docker-compose exec web python manage.py createsuperuser

# Проверка
docker-compose exec web python scripts/check_celery_redis.py
```

## Структура сервисов

- `web` - Django приложение (Gunicorn)
- `celery` - Celery worker
- `celery-beat` - Celery beat scheduler
- `flower` - Мониторинг Celery
- `db` - PostgreSQL
- `redis` - Redis

## Переменные окружения

Создайте файл `.env` (можно скопировать из `env.sample`) **без дублей DB_ переменных**:
```env
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,web

DB_ENGINE=django.db.backends.postgresql
DB_NAME=django_fullstack
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432

CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

STRIPE_PUBLIC_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

## Устранение проблем

**Сервисы не запускаются:**
```bash
docker-compose down -v
docker-compose build
docker-compose up -d
```

**Проблемы с подключением:**
```bash
docker-compose restart redis celery db
docker-compose exec web python scripts/check_celery_redis.py
```
