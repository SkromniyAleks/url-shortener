# 🔗 URL Shortener с аналитикой

Высоконагруженный сервис сокращения ссылок с трекингом кликов и детальной аналитикой переходов.

![Python](https://img.shields.io/badge/Python-3.14-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7-DC382D?logo=redis&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![Nginx](https://img.shields.io/badge/Nginx-1.31-009639?logo=nginx&logoColor=white)

## 📋 Описание

Сервис позволяет сократить длинную ссылку до короткого кода (6 символов), отслеживать каждый переход и собирать аналитику: IP-адрес, User-Agent, реферер и время клика.

**Сценарий использования:** маркетолог создаёт короткую ссылку для рекламной кампании → сервис редиректит пользователей и записывает каждый клик → маркетолог получает статистику по кампании.

## 🏗️ Архитектура

```
                    ┌──────────────┐
                    │  Пользователь│
                    └──────┬───────┘
                           │ HTTP :80
                           ▼
                    ┌──────────────┐
                    │    Nginx     │  reverse proxy
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │   FastAPI    │  бизнес-логика :8000
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

## ⚡ Ключевые особенности

- **Redis-кэширование редиректов** — горячие ссылки отдаются за ~10мс вместо ~150мс (ускорение ~15x)
- **Индексы PostgreSQL** по `short_code` и `link_id` — быстрые выборки при высокой нагрузке
- **Полная аналитика кликов** — IP, User-Agent, реферер, время перехода
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
| Валидация | Pydantic v2, pydantic-settings |
| Контейнеризация | Docker, Docker Compose |
| Тесты | pytest, pytest-asyncio, httpx |
| CI/CD | GitHub Actions |
| Администрирование БД | pgAdmin 4 |

## 🚀 Быстрый старт

### Требования
- Docker + Docker Compose

### Запуск

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
| Swagger UI | http://localhost/docs |
| Health check | http://localhost/health |
| pgAdmin | http://localhost:5050 (admin@admin.com / admin) |

## 📡 API

| Метод | Путь | Описание |
|---|---|---|
| POST | `/api/v1/links` | Создать короткую ссылку |
| GET | `/{short_code}` | Редирект + запись клика |
| GET | `/api/v1/links/{id}/stats` | Аналитика по ссылке |
| GET | `/health` | Health check |

### Пример: создать ссылку

```bash
curl -X POST http://localhost/api/v1/links \
  -H "Content-Type: application/json" \
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
  "click_count": 0
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
curl http://localhost/api/v1/links/1/stats
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

## 🗄️ Схема базы данных

**links** — короткие ссылки:

| Поле | Тип | Описание |
|---|---|---|
| id | integer (PK) | идентификатор |
| short_code | varchar(10), unique, index | короткий код |
| original_url | text | исходная ссылка |
| created_at | timestamp | дата создания |
| expires_at | timestamp, nullable | срок действия |
| click_count | integer | счётчик кликов |

**clicks** — аналитика переходов:

| Поле | Тип | Описание |
|---|---|---|
| id | integer (PK) | идентификатор |
| link_id | integer (FK → links.id), index | ссылка |
| clicked_at | timestamp | время клика |
| ip_address | varchar(45) | IP пользователя |
| user_agent | text | браузер/устройство |
| referer | text | источник перехода |

## 🧪 Тесты

```bash
# Установи зависимости
pip install -r requirements.txt

# Запусти тесты
pytest tests/ -v
```

Покрытие: создание ссылок, редирект, 404, аналитика, health check (5 тестов).

## 📁 Структура проекта

```
url-shortener/
├── app/
│   ├── routers/          # эндпоинты API
│   │   ├── links.py      # создание ссылок + аналитика
│   │   └── redirect.py   # редирект с записью клика
│   ├── services/         # бизнес-логика
│   │   └── link_service.py
│   ├── config.py         # настройки (pydantic-settings)
│   ├── database.py       # async-движок SQLAlchemy
│   ├── models.py         # ORM-модели (links, clicks)
│   ├── schemas.py        # Pydantic-схемы
│   ├── redis_client.py   # клиент Redis + кэш-хелперы
│   └── main.py           # точка входа FastAPI
├── tests/                # pytest-тесты
├── .github/workflows/    # CI/CD (GitHub Actions)
├── docker-compose.yml    # 5 сервисов: app, postgres, redis, nginx, pgadmin
├── Dockerfile
├── nginx.conf            # конфиг reverse proxy
└── requirements.txt
```

## 🔄 CI/CD

На каждый push в `main` GitHub Actions прогоняет:
1. Линтеры (ruff, mypy)
2. Тесты (pytest)

## 📈 Планы развития

- [ ] Аутентификация пользователей (JWT)
- [ ] Rate limiting через Redis
- [ ] Кастомные короткие коды
- [ ] QR-коды для ссылок
- [ ] Графики аналитики по дням

## 👤 Автор

**Борисов Алексей** — Junior Python Developer
- GitHub: [@SkromniyAleks](https://github.com/SkromniyAleks)
- Telegram: [@SkromniyAleks](https://t.me/SkromniyAleks)