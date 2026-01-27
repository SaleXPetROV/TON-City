# TON City Builder - Product Requirements Document

## Original Problem Statement
Пользователь запросил реализацию комплексной системы аутентификации и изменения в пользовательском интерфейсе для игры TON City Builder на блокчейне TON.

## Core Requirements

### 1. Аутентификация
- [x] Регистрация через Email + password + username
- [x] Вход через Email/username + password
- [x] Регистрация/вход через TonConnect
- [ ] Регистрация/вход через Google OAuth (ОТЛОЖЕНО - требуются ключи от пользователя)

### 2. Интерфейс после аутентификации
- [x] После входа/регистрации перенаправление на главную страницу
- [x] Кнопки "Вход" и "Регистрация" заменяются на кнопку с аватаром и никнеймом
- [x] Sidebar отображается после авторизации

### 3. Поведение Sidebar
- [x] На главной странице всегда открыт (после авторизации)
- [x] Содержит пункты: CITY, MAP, MARKET, TRADING, SETTINGS

### 4. Настройки пользователя (P2)
- [ ] Смена никнейма (эндпоинт готов, UI - заглушка)
- [ ] Смена почты и пароля (эндпоинты готовы, UI - заглушка)
- [ ] Привязка кошелька (эндпоинт готов, UI - заглушка)
- [ ] Загрузка аватара (эндпоинт-заглушка)

### 5. Интернационализация
- [x] Переводы на 8 языков (включая русский)

## Architecture

```
/app/
├── backend/
│   ├── server.py          # FastAPI, модели, роуты, игровые константы
│   ├── auth_handler.py    # Логика аутентификации
│   ├── ton_integration.py # TON блокчейн интеграция
│   └── .env               # MONGO_URL, JWT_SECRET, GOOGLE_CLIENT_ID
├── frontend/
│   ├── src/
│   │   ├── App.js         # Централизованное состояние пользователя
│   │   ├── pages/
│   │   │   ├── AuthPage.jsx
│   │   │   ├── LandingPage.jsx
│   │   │   ├── GamePage.jsx
│   │   │   └── SettingsPage.jsx (заглушка)
│   │   ├── components/
│   │   │   └── Sidebar.jsx
│   │   └── lib/
│   │       └── translations.js
│   └── .env               # REACT_APP_BACKEND_URL
└── test_reports/
    └── iteration_1.json
```

## Key API Endpoints
- `POST /api/auth/register` - Регистрация
- `POST /api/auth/login` - Вход (email или username)
- `GET /api/auth/me` - Данные текущего пользователя
- `POST /api/auth/verify-wallet` - Аутентификация через TonConnect
- `POST /api/auth/google` - Google OAuth (требует настройки)

## Database Schema (MongoDB)
```javascript
users: {
  id: string,
  username: string (unique),
  email: string,
  hashed_password: string,
  wallet_address: string,
  raw_address: string,
  avatar: string (base64 SVG или URL),
  level: Union[str, int],
  xp: int,
  balance_ton: float,
  balance_game: float,
  is_admin: bool
}
```

## Testing Status
- Backend: 100% (12/12 тестов)
- Frontend: 100% (5/5 UI тестов)
- Test credentials: test_p0_fix@example.com / test123

## What's Working
- Регистрация и вход через email/password
- Вход по username
- Обновление UI после авторизации (sidebar, avatar)
- Корректные сообщения об ошибках при неверных данных
- TonConnect интеграция
- Интернационализация (8 языков)

## Backlog (P2)
1. **Google OAuth** - требуются GOOGLE_CLIENT_ID/SECRET от пользователя
2. **Страница настроек** - реализовать UI для смены данных
3. **Загрузка аватара** - реализовать загрузку на бэкенде
4. **UI страницы /game** - убрать кнопку "Домой", переместить логотип
5. **payment_monitor.py** - восстановить логику обработки платежей

## Technical Notes
- Frontend состояние аутентификации централизовано в App.js
- Token хранится в localStorage
- Hot reload включен для backend и frontend
- Supervisor управляет сервисами

## Last Updated
2026-01-27
