# vibes-sdk-python · Официальный Python SDK

> Python-клиент для API платформы [vibes.su](https://vibes.su)

[![Python ≥3.9](https://img.shields.io/badge/python-%3E%3D3.9-blue)](https://python.org)
[![Лицензия: MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![Платформа: vibes.su](https://img.shields.io/badge/platform-vibes.su-orange)](https://vibes.su)

---

## Что такое vibes.su?

**vibes.su** — профессиональная платформа управления ссылками для маркетологов, веб-мастеров и арбитражников трафика:

- 🔗 **Умные короткие ссылки** — ГЕО-таргетинг, таргетинг по устройствам, клоакинг, UTM-метки, лимиты кликов, расписание
- 🔲 **Динамические QR-коды** — меняйте целевой URL без перепечати
- 📊 **Глубокая аналитика** — по стране, городу, устройству, браузеру, источнику, UTM, часам
- 🎯 **Splash-страницы** — промежуточные страницы перед редиректом
- 🌐 **Кастомные домены** — собственный брендированный короткий домен
- 🔔 **Уведомления** — Telegram, email, Slack, Discord, WhatsApp
- 👥 **Команды** — многопользовательский доступ с ролевыми правами

### Тарифы и оплата

Все планы можно оплатить: **USDT (TRC-20 / ERC-20)**, **BTC**, **ETH**, **банковской картой**.

👉 [Посмотреть тарифы](https://vibes.su/pricing)

---

## Требования

- Python **3.9+**
- [`httpx`](https://www.python-httpx.org/) ≥ 0.27.0
- Аккаунт vibes.su с доступом к API (платный план)

---

## Установка

```bash
pip install httpx
# затем скопируйте vibes_client.py в свой проект, или клонируйте репо:
git clone https://github.com/vibes-su/vibes-sdk-python.git
cd vibes-sdk-python
pip install -r requirements.txt
```

---

## Получение API-ключа

1. Войдите на [vibes.su](https://vibes.su)
2. Перейдите в **Аккаунт → API** (`https://vibes.su/account/api`)
3. Скопируйте Bearer-токен (32 hex-символа)

> Держите ключ в тайне. Никогда не коммитьте его в репозиторий.

---

## Быстрый старт

### Синхронный режим

```python
from vibes_client import VibesAPI, VibesAPIError

api = VibesAPI("YOUR_API_KEY_HERE")

# Профиль пользователя
user = api.get_user()
print("Привет,", user["name"])

# Создать короткую ссылку
link = api.create_link("https://ваш-длинный-url.com/страница", url="мой-алиас")
print("Короткая ссылка:", f"https://vibes.su/{link['url']}")

api.close()  # или используйте как контекстный менеджер
```

### Контекстный менеджер (рекомендуется)

```python
with VibesAPI("YOUR_API_KEY_HERE") as api:
    user = api.get_user()
    link = api.create_link("https://example.com")
```

### Асинхронный режим

```python
import asyncio
from vibes_client import AsyncVibesAPI

async def main():
    async with AsyncVibesAPI("YOUR_API_KEY_HERE") as api:
        user = await api.get_user()
        link = await api.create_link("https://example.com")
        print(link["url"])

asyncio.run(main())
```

---

## Обработка ошибок

```python
from vibes_client import VibesAPIError

try:
    link = api.create_link("https://example.com")
except VibesAPIError as e:
    print(f"[{e.status}] {e}")
    # e.body — сырой словарь ответа
```

`VibesAPIError` выбрасывается при HTTP 4xx / 5xx.
Статус `429` — превышен лимит **60 запросов в минуту**.

---

## Справочник API

### Конструктор

```python
VibesAPI(api_key, base_url="https://vibes.su", timeout=30.0)
AsyncVibesAPI(api_key, base_url="https://vibes.su", timeout=30.0)
```

Синхронно выбрасывает `TypeError` если ключ пустой или содержит не-ASCII символы (кириллица и т.п.).

---

### Методы

#### Пользователь
| Метод | Описание |
|-------|----------|
| `get_user()` | Профиль и настройки плана |

#### Ссылки
| Метод | Описание |
|-------|----------|
| `get_links(**params)` | Список ссылок (пагинация) |
| `get_link(link_id)` | Одна ссылка |
| `create_link(location_url, **kwargs)` | Создать ссылку |
| `update_link(link_id, **kwargs)` | Обновить ссылку |
| `delete_link(link_id)` | Удалить ссылку |

**Основные kwargs для `create_link`:**

| Kwarg | Тип | Описание |
|-------|-----|----------|
| `url` | str | Кастомный алиас (генерируется автоматически) |
| `targeting_type` | str | `country_code` · `device_type` · `os_name` · `rotation` · ... |
| `targeting_country_code_key` | list | Коды стран для ГЕО-таргетинга |
| `targeting_country_code_value` | list | URL для каждой страны |
| `cloaking_is_enabled` | 0\|1 | Клоакинг URL |
| `http_status_code` | int | 301 / 302 / 307 / 308 |
| `password` | str | Защита паролем |
| `clicks_limit` | int | Лимит кликов |
| `start_date` / `end_date` | str | Расписание `YYYY-MM-DD HH:MM:SS` |
| `is_bulk` | 0\|1 | Массовый режим |
| `location_urls` | str | URL через `\n` для массового режима |

**Пример ГЕО-таргетинга:**

```python
link = api.create_link(
    "https://default-offer.com",
    targeting_type="country_code",
    targeting_country_code_key=["RU", "US", "DE"],
    targeting_country_code_value=[
        "https://ru-offer.com",
        "https://us-offer.com",
        "https://de-offer.com",
    ],
)
```

#### QR-коды
| Метод | Описание |
|-------|----------|
| `get_qr_codes(**params)` | Список QR-кодов |
| `get_qr_code(id)` | Один QR-код |
| `create_qr_code(type, name, **kwargs)` | Создать QR-код |
| `update_qr_code(id, **kwargs)` | Обновить QR-код |
| `delete_qr_code(id)` | Удалить QR-код |

**Поддерживаемые типы:** `text` · `url` · `phone` · `sms` · `email` · `whatsapp` · `facetime` · `location` · `wifi` · `event` · `crypto` · `vcard` · `paypal` · `upi` · `epc` · `pix`

```python
# Динамический QR-код
qr = api.create_qr_code("url", "Мой QR", url="https://example.com", url_dynamic=1)
print(qr["qr_code"])  # URL к SVG-файлу
```

#### Статистика
| Метод | Описание |
|-------|----------|
| `get_link_statistics(link_id, type, **params)` | Статистика по ссылке |
| `get_all_statistics(type, **params)` | Агрегированная статистика |

**Типы:** `overview` · `country_code` · `city_name` · `continent_code` · `os_name` · `browser_name` · `device_type` · `browser_language` · `referrer_host` · `referrer_path` · `utm_source` · `utm_medium` · `utm_campaign` · `hour`

#### Остальные ресурсы

| Группа | Методы |
|--------|--------|
| Проекты | `get_projects` · `get_project` · `create_project` · `update_project` · `delete_project` |
| Пиксели | `get_pixels` · `get_pixel` · `create_pixel` · `update_pixel` · `delete_pixel` |
| Домены | `get_domains` · `get_domain` · `get_available_domains` · `create_domain` · `update_domain` · `delete_domain` |
| Splash-страницы | `get_splash_pages` · `get_splash_page` · `create_splash_page` · `update_splash_page` · `delete_splash_page` |
| Уведомления | `get_notification_handlers` · `get_notification_handler` · `create_notification_handler` · `update_notification_handler` · `delete_notification_handler` |
| Команды (владелец) | `get_teams` · `get_team` · `create_team` · `update_team` · `delete_team` |
| Участники команды | `get_team_members` · `create_team_member` · `update_team_member` · `delete_team_member` |
| Членство в командах | `get_team_memberships` · `get_team_membership` · `update_team_membership` · `delete_team_membership` |
| Платежи | `get_payments` · `get_payment` |
| Данные форм | `get_data` · `get_datum` · `delete_data` |
| Логи | `get_logs` |
| Email-подписи | `get_signatures` · `get_signature` · `create_signature` · `update_signature` · `delete_signature` |

---

## Готовые решения

### 🌍 ГЕО-ротатор трафика — `solution_geo_rotator.py`

Одна умная ссылка перенаправляет посетителей на нужный оффер по стране.
Отредактируйте `GEO_CONFIG` и `DEFAULT_URL`, затем:

```bash
python solution_geo_rotator.py
```

**Применение:** арбитраж, партнёрские программы с региональными офферами, мультиязычные лендинги.

### 🔲 Массовый генератор QR-кодов — `solution_bulk_qr_generator.py`

Генерирует динамические QR-коды SVG пакетом. Отредактируйте `ITEMS`, затем:

```bash
python solution_bulk_qr_generator.py
# Вывод: ./qr_output/<название>.svg
```

**Применение:** меню ресторанов, ценники, визитки, стенды на выставках.

### 📊 Экспорт аналитики в CSV — `solution_stats_exporter.py`

Экспортирует статистику кликов в CSV с UTF-8 BOM (кириллица в Excel отображается корректно).
Укажите `LINK_ID`, `START_DATE`, `END_DATE`, затем:

```bash
python solution_stats_exporter.py
# Вывод: ./reports/report_<тип>_<время>.csv
```

**Применение:** еженедельные отчёты для клиентов, анализ источников трафика, мониторинг аудитории.

---

## Лимиты запросов

**60 запросов в минуту** на один API-ключ.
SDK выбрасывает `VibesAPIError` со `status=429` при превышении.

---

## Лицензия

MIT © vibes.su

---

## Поддержка

- 📖 Документация API: [vibes.su/api-documentation](https://vibes.su/api-documentation)
- 📧 Контакты: [vibes.su/contact](https://vibes.su/contact)
- 💬 Telegram: [@vibes_su](https://t.me/vibes_su)
