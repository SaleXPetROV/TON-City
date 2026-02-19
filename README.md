# TON City Builder

## Описание проекта

**TON City Builder** — это блокчейн-игра на базе TON (The Open Network), где игроки могут:
- 🏠 Покупать участки земли на изометрической карте острова
- 🏭 Строить различные бизнесы (фермы, заводы, магазины, банки и др.)
- 💰 Получать реальный доход в криптовалюте TON
- 📈 Торговать ресурсами и участками с другими игроками
- 🏆 Соревноваться в рейтинге лидеров

## Технологический стек

### Frontend
- **React 18** — основной фреймворк
- **Tailwind CSS** — стилизация
- **Framer Motion** — анимации
- **PixiJS** — изометрическая карта (2D WebGL рендеринг)
- **TON Connect** — интеграция кошельков TON

### Backend
- **FastAPI** — REST API
- **MongoDB** — база данных
- **WebSocket** — real-time чат и обновления
- **APScheduler** — фоновые задачи (автосбор дохода)

### Blockchain
- **TON SDK** — интеграция с блокчейном TON
- **TON Connect** — аутентификация через кошелёк

## Структура проекта

```
/app
├── backend/
│   ├── server.py           # Основной API сервер
│   ├── auth_handler.py     # Аутентификация (email, wallet, Google)
│   ├── business_config.py  # Конфигурация бизнесов и ресурсов
│   ├── game_systems.py     # Игровые системы (патронаж, склады, банки)
│   ├── ton_island.py       # Генерация карты острова
│   ├── ton_integration.py  # Интеграция с TON blockchain
│   ├── background_tasks.py # Фоновые задачи
│   └── chat_handler.py     # WebSocket чат
│
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── LandingPage.jsx     # Главная страница
│   │   │   ├── TonIslandPage.jsx   # Карта острова
│   │   │   ├── AdminPage.jsx       # Админ-панель
│   │   │   ├── AuthPage.jsx        # Авторизация
│   │   │   ├── SettingsPage.jsx    # Настройки профиля
│   │   │   ├── TradingPageNew.jsx  # Торговля ресурсами
│   │   │   ├── MarketplacePage.jsx # Маркетплейс
│   │   │   ├── LeaderboardPage.jsx # Рейтинг игроков
│   │   │   └── ...
│   │   │
│   │   ├── components/
│   │   │   ├── Sidebar.jsx         # Боковое меню (desktop)
│   │   │   ├── MobileNav.jsx       # Hamburger меню (mobile)
│   │   │   ├── MaintenanceOverlay.jsx # Экран техработ
│   │   │   └── ui/                 # shadcn/ui компоненты
│   │   │
│   │   ├── engine/
│   │   │   ├── IsometricMapEngine.js  # PixiJS движок карты
│   │   │   └── MapWebSocket.js        # WebSocket для карты
│   │   │
│   │   └── lib/
│   │       ├── api.js              # API клиент
│   │       ├── translations.js     # Мультиязычность
│   │       └── tonAddress.js       # Утилиты TON адресов
│   │
│   └── tailwind.config.js
│
└── scripts/                # Утилиты и скрипты
```

## Основные функции

### Для пользователей
- ✅ Регистрация через email/пароль или TON кошелёк
- ✅ Изометрическая карта острова с зонами
- ✅ Покупка участков земли
- ✅ Строительство бизнесов (12+ типов)
- ✅ Автоматический сбор дохода
- ✅ Торговля ресурсами между игроками
- ✅ Real-time чат
- ✅ Рейтинг лидеров
- ✅ Мультиязычный интерфейс (EN, RU, ZH)
- ✅ Адаптивный дизайн (desktop + mobile)

### Для администраторов
- ✅ Просмотр статистики
- ✅ Управление пользователями
- ✅ Одобрение/отклонение выводов
- ✅ Создание промокодов
- ✅ Объявления
- ✅ Настройка TON кошелька казны
- ✅ Режим технических работ

## Игровые механики

### Зоны острова
| Зона | Множитель цены | Разрешённые Tier |
|------|---------------|------------------|
| Core (Ядро) | x1.0 | 1, 2, 3 |
| Inner (Центр) | x0.7 | 1, 2, 3 |
| Middle (Средняя) | x0.5 | 1, 2 |
| Outer (Внешняя) | x0.25 | 1 |

### Типы бизнесов
- **Tier 1**: Гелиос Солар, Ферма, Электростанция
- **Tier 2**: Завод, Магазин, Ресторан
- **Tier 3**: Банк, Валидатор, DEX

### Система патронажа
Бизнесы могут иметь патрона (банк, валидатор), который даёт бонусы к доходу взамен на комиссию.

## Установка и запуск

### Требования
- Node.js 18+
- Python 3.11+
- MongoDB 6+

### Backend
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env  # Настроить переменные окружения
python -m uvicorn server:app --reload --port 8001
```

### Frontend
```bash
cd frontend
yarn install
yarn start
```

## Переменные окружения

### Backend (.env)
```
MONGO_URL=mongodb://localhost:27017
DB_NAME=ton_city
JWT_SECRET_KEY=your-secret-key
ADMIN_WALLET_ADDRESS=UQ...  # TON адрес админа
```

### Frontend (.env)
```
REACT_APP_BACKEND_URL=http://localhost:8001
```

## API Endpoints

### Аутентификация
- `POST /api/auth/register` — Регистрация
- `POST /api/auth/login` — Вход
- `POST /api/auth/verify-wallet` — Вход через TON кошелёк
- `GET /api/auth/me` — Текущий пользователь

### Карта
- `GET /api/island` — Данные карты острова
- `POST /api/island/buy/{x}/{y}` — Купить участок
- `POST /api/island/build/{x}/{y}` — Построить бизнес

### Бизнесы
- `GET /api/my/businesses` — Мои бизнесы
- `POST /api/business/{id}/collect` — Собрать доход
- `POST /api/business/{id}/upgrade` — Улучшить

### Админ
- `GET /api/admin/stats` — Статистика
- `POST /api/admin/maintenance` — Режим техработ

## Лицензия

MIT License

## Контакты

- Telegram: @support
- GitHub: https://github.com/SaleXPetROV/TON-City

---

**TON City Builder** © 2025 | Powered by TON Blockchain
