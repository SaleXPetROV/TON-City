# TON City - Product Requirements Document

## Original Problem Statement
TON City - блокчейн игра-стратегия на TON Blockchain. Задача - довести проект до 100% работоспособности и исправить баги.

## Architecture
- **Backend**: FastAPI (Python) + MongoDB + APScheduler
- **Frontend**: React.js + Tailwind CSS
- **Blockchain**: TON (The Open Network)
- **Auth**: JWT + TON Connect

## What's Been Implemented ✅

### Session 1 (Initial Setup)
- Проект склонирован и настроен из GitHub
- Все backend endpoints работают (100%)
- Admin panel функционален
- Promo codes "once per user" работает

### Session 2 (Bug Fixes) - 06.03.2026
1. ✅ **Налог при продаже** - теперь берётся из админки (land_business_sale_tax)
2. ✅ **TON CIRCULATION** - показывает сумму положительных балансов пользователей
3. ✅ **Telegram Mini App** - добавлена поддержка SDK и защита от конфликтов расширений
4. ✅ **Promo activation** - возвращает new_balance для мгновенного обновления
5. ✅ **История операций** - убрана общая статистика, исправлено форматирование (+/- знаки, 2 знака после запятой, цвета)
6. ✅ **Мои бизнесы** - убрана кнопка сбора дохода и карточка "Доход"
7. ✅ **Рекомендации** - скрываются при клике на карту, данные поля скрываются при клике на рекомендацию
8. ✅ **Улучшение бизнеса** - показывает требуемые ресурсы
9. ✅ **Статус бизнеса** - меняется на "on_sale" при выставлении на продажу
10. ✅ **Структура бизнеса в БД** - добавлены поля: tier, tier_name, produces, production_rate, consumes, status, zone

### Backend Test Results
- Session 1: 86.7% → 100%
- Session 2: 100% (13/13 tests passed)

## User Personas
1. **Players** - Покупают землю, строят бизнесы, торгуют, зарабатывают TON
2. **Admin** - Управляет экономикой игры, кредитами, промокодами

## Test Credentials
- Admin: admin@toncity.com / Admin123!
- Test Player: testplayer@toncity.com / Test123!

## Production/Economic Tick System
- Economic tick: каждый час
- Midnight decay: 21:00 UTC (00:00 MSK)
- Durability wear: каждые 6 часов
- Credit processing: 22:00 UTC daily
- Warehouse spoilage: 21:30 UTC daily

## Next Action Items
- [ ] Проверить производство ресурсов после следующего economic tick
- [ ] Настроить TON receiver wallet в админке
- [ ] Тестирование Telegram Mini App в реальном боте

## Backlog
- P1: Настройка mainnet deployment
- P2: Advanced analytics dashboard
- P2: Push notifications через Telegram bot
