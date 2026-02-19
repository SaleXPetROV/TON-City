# TON City Builder - Product Requirements Document

## Original Problem Statement
Пользователь запросил:
1. Адаптировать полностью под мобильное устройство (hamburger меню в стиле The Sandbox)
2. Кнопка отображения зданий на карте (красная/зелёная, "В разработке")
3. Технические работы в админке с dropdown меню
4. Навигация админ ↔ пользовательский интерфейс
5. Переписать README.md
6. **ДОБАВЛЕНО**: Email верификация при регистрации
7. **ИСПРАВЛЕНО**: JSON ошибки при wallet авторизации

## What's Been Implemented

### 2026-02-19 - Auth System Fixes
- ✅ Email Verification при регистрации
  - Новые endpoints: `/api/auth/register/initiate` и `/api/auth/register/verify`
  - 6-цифровой код на email (15 минут валидность)
  - Fallback: если SMTP не настроен - регистрация сразу
  
- ✅ JSON Error Handling
  - Безопасный парсинг JSON ответов
  - Понятные сообщения об ошибках на русском
  - Обработка network ошибок

### 2026-02-19 - Mobile & Admin Features
- ✅ Hamburger меню в стиле The Sandbox (MobileNav.jsx)
- ✅ Кнопка зданий на карте (красная с "В процессе разработки")
- ✅ Maintenance mode в админке с dropdown
- ✅ Кнопка "На сайт" в админке
- ✅ README.md переписан

## Testing Results
- Backend Auth: 100% (9/9 tests)
- Frontend Auth: 100%
- Mobile UI: 100%
- Overall: 100%

## Configuration

### Для включения Email верификации:
Добавьте в /app/backend/.env:
```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@toncity.com
SMTP_FROM_NAME=TON City Builder
```

## Backlog
- [ ] Настроить SMTP для production
- [ ] Реализовать 3D здания на карте
- [ ] Telegram уведомления
