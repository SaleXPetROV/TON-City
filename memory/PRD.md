# TON City Builder - Product Requirements Document

## Original Problem Statement
Блокчейн-игра экономическая стратегия на TON. Игроки покупают землю на острове TON Island, строят бизнесы, зарабатывают криптовалюту через систему патронажа и экономику производства.

## Core Architecture

### TON Island System
- **Единая карта**: 528 участков с зонированием (core/inner/middle/outer)
- **21 тип бизнесов** в 3 тирах с 10 уровнями каждый
- **Спрайты**: 256x256 PNG, прозрачный фон, единый масштаб SPRITE_SCALE=0.25

### Sprite System (per TD v2)
- Единый canvas 256x256, anchor (0.5, 1.0), snapToGrid()
- Z-Index = (cell.q + cell.r)
- Ночной режим: tint 0x556688 + additive glow overlay

### Business Tiers & Tax
- Tier 1 (15% налог): Helios, Nano DC, Quartz Mine, Signal, Hydro, BioFood, Scrap
- Tier 2 (23% налог): Chips, NFT Studio, AI Lab, Logistics, Cyber Cafe, Repair, VR Club
- Tier 3 (30% налог): Validator, Gram Bank, DEX, Casino, Arena, Incubator, Bridge

## What's Implemented

### Phase 1 (2026-02-07) ✅
- [x] 210 спрайтов одного размера (Tier 2 стандарт), прозрачный фон, вписаны в ячейки
- [x] Все суммы с 2 знаками после точки (.toFixed(2))
- [x] "Доход" вместо "Доход/час" + кнопка "Собрать"
- [x] Маркетплейс: убрана "Торговля ресурсами", добавлены "Бизнесов на продаже"/"Стоимость земель"
- [x] Логотип TON CITY в сайдбаре → ведёт на главную
- [x] 8 языков: EN, RU, ES, CN, FR, DE, JP, KR
- [x] Удалён уровень пользователя из YOUR STATS
- [x] Ночной режим с additive glow overlay
- [x] Кнопка обновления рядом с ночным режимом

### Ранее реализовано
- [x] TON Island карта (PixiJS Canvas, 528 участков, 4 зоны)
- [x] Система патронажа
- [x] 10-уровневые апгрейды
- [x] P2P аренда складов
- [x] Двойная очередь вывода
- [x] Налоговая система
- [x] Аутентификация (Email/TonConnect)
- [x] Глобальный чат (без приватных/городских)
- [x] 100 тестовых пользователей

## Pending Tasks

### Phase 2 (Средние фичи)
- [ ] Система городов: список с 2D превью, 5 новых карт-заглушек
- [ ] Калькулятор под новую систему бизнесов/налогов
- [ ] Умные рекомендации на основе спроса/предложения

### Phase 3 (Крупные фичи)
- [ ] P2P торговля землёй: просмотр владельца, предложение купить, ЛС
- [ ] Полный перевод всех страниц на 8 языков (UI labels done, content pending)

### Backlog
- [ ] AI-генерация качественных спрайтов (бюджет исчерпан)
- [ ] Google OAuth
- [ ] Админ-панель

## Test Credentials
- Username: user_1, Password: password123
- Balance: 4033.00 TON, 1 бизнес (dex)

## Tech Stack
- Backend: FastAPI + MongoDB
- Frontend: React + PixiJS (WebGL) + TailwindCSS + Shadcn/UI
- AI: Emergent LLM Key (бюджет исчерпан)
