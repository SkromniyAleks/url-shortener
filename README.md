# 🔗 URL Shortener с аналитикой

Высоконагруженный сервис сокращения ссылок с трекингом кликов, детальной аналитикой переходов и веб-интерфейсом с JWT-авторизацией.

## 📋 Описание

Сервис позволяет сократить длинную ссылку до короткого кода (6 символов), отслеживать каждый переход и собирать аналитику: IP-адрес, User-Agent, реферер и время клика. Управление ссылками доступно через веб-интерфейс с обязательной авторизацией и ролями.

**Сценарий использования:** маркетолог создаёт короткую ссылку для рекламной кампании → сервис редиректит пользователей и записывает каждый клик → маркетолог получает статистику по кампании.

**Сценарий управления:** пользователь регистрируется в веб-интерфейсе → создаёт ссылки и видит только свои → администратор видит все ссылки с авторами, управляет пользователями и может сбросить забытый пароль.

## 🏗️ Архитектура

```
                    ┌──────────────┐
                    │  Пользователь│
                    └──────┬───────┘
                           │ HTTP :80
                           ▼
                    ┌──────────────┐
                    │    Nginx     │  reverse proxy + статика
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │   FastAPI    │  бизнес-логика + JWT :8000
                    │   (Uvicorn)  │
                    └──┬───────┬───┘
                       │       │
              ┌────────▼──┐ ┌──▼─────────┐
              │ PostgreSQL│ │   Redis    │
              │  (данные) │ │   (кэш)    │
              └───────────┘ └────────────┘
```

**Поток запроса при редиректе:**
1. Nginx принимает запрос на порту 80 и проксирует в FastAPI
2. FastAPI проверяет Redis-кэш (горячие ссылки)
3. При промахе — запрос в PostgreSQL + запись в кэш
4. Клик логируется в таблицу `clicks` (IP, User-Agent, реферер)
5. Возвращается 307-редирект на оригинальную ссылку

**Поток авторизованного запроса:**
1. Клиент получает JWT на `/api/v1/auth/login`
2. Токен передаётся в заголовке `Authorization: Bearer ...`
3. Зависимость FastAPI проверяет подпись и загружает пользователя из БД
4. Проверка прав: владелец ссылки / администратор (иначе 403)

## ⚡ Ключевые особенности

- **Redis-кэширование редиректов** — горячие ссылки отдаются за ~10мс вместо ~150мс (ускорение ~15x)
- **Инвалидация кэша при удалении** — удалённая ссылка не продолжает жить из Redis
- **JWT-авторизация и роли** — пользователь видит только свои ссылки, админ — все и управляет пользователями
- **Веб-интерфейс** — создание ссылок, аналитика кликов, админ-панель (vanilla JS + Fetch API)
- **Индексы PostgreSQL** по `short_code` и `link_id` — быстрые выборки при высокой нагрузке
- **Полная аналитика кликов** — IP, User-Agent, реферер, время перехода
- **Запуск в один клик** — `start.bat`: сборка, health-check, открытие браузера; остановка клавишей или закрытием окна (фоновый watchdog)
- **Docker Compose** — весь стек поднимается одной командой
- **Swagger-документация** из коробки (`/docs`)
- **CI/CD** — линтеры и тесты прогоняются автоматически на каждый push

## 🛠️ Технологический стек

| Слой | Технологии |
|---|---|
| Backend | Python 3.14, FastAPI, Uvicorn |
| ORM / БД | SQLAlchemy 2.0 (async), PostgreSQL 15 |
| Кэш | Redis 7 |
| Web server | Nginx (reverse proxy) |
| Аутентификация | PyJWT, PBKDF2 (hashlib), HTTPBearer |
| Frontend | vanilla JS, Fetch API, CSS |
| Валидация | Pydantic v2, pydantic-settings |
| Контейнеризация | Docker, Docker Compose |
| Тесты | pytest, pytest-asyncio, httpx |
| CI/CD | GitHub Actions |
| Раннер (Windows) | start.bat + watchdog (VBScript/WMI) |
| Администрирование БД | pgAdmin 4 |

## 🚀 Быстрый старт

### Требования
- Docker + Docker Compose
- Windows (для `start.bat`; на других ОС — ручной запуск через `docker compose`)

### Запуск в один клик (Windows)

```bash
.\start.bat
```

Скрипт соберёт образ, поднимет стек, дождётся health-check и откроет браузер. Остановка: любая клавиша в окне раннера или просто закрыть окно — фоновый watchdog сам опустит стек.

### Запуск вручную

```bash
# 1. Клонируй репозиторий
git clone https://github.com/SkromniyAleks/url-shortener.git
cd url-shortener

# 2. Создай файл окружения
cp .env.example .env

# 3. Подними весь стек
docker compose up --build
```

Сервис доступен:

| Сервис | Адрес |
|---|---|
| Веб-интерфейс | http://localhost |
| Swagger UI | http://localhost/docs |
| Health check | http://localhost/health |
| pgAdmin | http://localhost:5050 (admin@admin.com / admin) |

Администратор приложения создаётся автоматически при первом старте (учётка — `ADMIN_USERNAME` / `ADMIN_PASSWORD` из `.env`).

## 📡 API

| Метод | Путь | Доступ | Описание |
|---|---|---|---|
| POST | `/api/v1/auth/register` | публично | Регистрация |
| POST | `/api/v1/auth/login` | публично | Вход, выдаёт JWT |
| GET | `/health` | публично | Health check |
| GET | `/{short_code}` | публично | Редирект + запись клика |
| GET | `/api/v1/auth/me` | user | Текущий пользователь |
| POST | `/api/v1/links` | user | Создать короткую ссылку |
| GET | `/api/v1/links` | user / admin | Свои ссылки / все ссылки с автором |
| GET | `/api/v1/links/{id}/stats` | владелец / админ | Аналитика по ссылке |
| GET | `/api/v1/links/{id}/clicks` | владелец / админ | Детали кликов |
| DELETE | `/api/v1/links/{id}` | владелец / админ | Удалить ссылку + инвалидация кэша |
| DELETE | `/api/v1/links` | admin | Очистить БД ссылок |
| GET | `/api/v1/admin/users` | admin | Список пользователей |
| POST | `/api/v1/admin/users/{id}/reset-password` | admin | Сбросить пароль пользователя |
| PATCH | `/api/v1/admin/users/{id}/role` | admin | Изменить роль |
| DELETE | `/api/v1/admin/users/{id}` | admin | Удалить аккаунт |

### Пример: вход и создание ссылки

```bash
# вход
curl -X POST http://localhost/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "alex", "password": "secret123"}'

# создание ссылки с токеном
curl -X POST http://localhost/api/v1/links \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"original_url": "https://example.com"}'
```

Ответ:

```json
{
  "id": 1,
  "short_code": "BwXJ89",
  "original_url": "https://example.com/",
  "short_url": "http://localhost/BwXJ89",
  "created_at": "2026-09-08T19:29:46.925068",
  "click_count": 0,
  "owner_id": 2,
  "owner_username": "alex"
}
```

### Пример: редирект

```bash
curl -I http://localhost/BwXJ89
# HTTP/1.1 307 Temporary Redirect
# location: https://example.com/
```

### Пример: аналитика

```bash
curl http://localhost/api/v1/links/1/stats \
  -H "Authorization: Bearer <token>"
```

```json
{
  "id": 1,
  "short_code": "BwXJ89",
  "original_url": "https://example.com/",
  "click_count": 1,
  "total_clicks": 1,
  "created_at": "2026-09-08T19:29:46.925068"
}
```
## 🧪 Тесты

```bash
# Установи зависимости
pip install -r requirements.txt

# Запусти тесты
pytest tests/ -v
```

## 📁 Структура проекта

```
url-shortener/
├── app/
│   ├── routers/          # эндпоинты API
│   │   ├── links.py      # создание ссылок + аналитика + удаление
│   │   ├── redirect.py   # редирект с записью клика
│   │   ├── auth.py       # регистрация, вход, текущий пользователь
│   │   └── admin.py      # управление пользователями (admin)
│   ├── services/         # бизнес-логика
│   │   ├── link_service.py
│   │   └── user_service.py
│   ├── static/           # веб-интерфейс (vanilla JS + CSS)
│   ├── config.py         # настройки (pydantic-settings)
│   ├── database.py       # async-движок SQLAlchemy
│   ├── dependencies.py   # JWT-зависимости (текущий пользователь, админ)
│   ├── security.py       # хэширование паролей (PBKDF2) и JWT
│   ├── models.py         # ORM-модели (users, links, clicks)
│   ├── schemas.py        # Pydantic-схемы
│   ├── redis_client.py   # клиент Redis + кэш-хелперы
│   └── main.py           # точка входа FastAPI
├── tests/                # pytest-тесты (20)
├── .github/workflows/    # CI/CD (GitHub Actions)
├── docker-compose.yml    # 5 сервисов: app, postgres, redis, nginx, pgadmin
├── Dockerfile
├── nginx.conf            # конфиг reverse proxy
├── start.bat             # раннер в один клик (Windows)
├── watchdogs.vbs         # скрытый процесс остановки стека при закрытии окна
└── requirements.txt
```

## 🔄 CI/CD

На каждый push в `main` GitHub Actions прогоняет:
1. Линтеры (ruff, mypy)
2. Тесты (pytest)

## 👤 Автор

**Борисов Алексей** — Junior Python Developer
- GitHub: @SkromniyAleks
- Telegram: @SkromniyAleks