# TON City Builder - Product Requirements Document

## Original Problem Statement
Игра-стратегия на блокчейне TON, где игроки покупают землю, строят бизнесы и зарабатывают криптовалюту.

## Core Architecture (Updated 2026-01-29)

### City System
- **Коллекция `cities`**: Хранит "скелет" города
  - `grid`: 2D массив (1 = земля, 0 = вода)
  - `style`: cyber/tropical/industrial/neon
  - `base_price`: базовая цена участка
  - `stats`: кэшированная статистика

- **Коллекция `plots`**: Участки привязаны к городу
  - `city_id`: ID города
  - `x`, `y`: координаты в grid
  - `owner`: ID владельца

### Демо-города (5 штук)
1. **TON Island** — форма диаманта TON (480 клеток)
2. **Nebula Bay** — форма полумесяца (460 клеток)
3. **Nova Archipelago** — архипелаг из 4 островов (470 клеток)
4. **Genesis Plains** — органическая форма (450 клеток)
5. **Crystal Reef** — органическая форма (480 клеток)

## Technical Stack
- **Backend**: FastAPI + MongoDB + PixiJS
- **Frontend**: React + Tailwind + PixiJS (WebGL)
- **Blockchain**: TON (TonConnect)

## Pages Structure
```
/                   - Landing (информация о проекте)
/auth               - Аутентификация (email/TonConnect/Google)
/map                - Выбор города (список с превью)
/game/:cityId       - Игра в городе (изометрический вид)
/settings           - Настройки пользователя
/trading            - Торговля ресурсами
```

## API Endpoints
- `GET /api/cities` - Список всех городов
- `GET /api/cities/{city_id}` - Детали города
- `GET /api/cities/{city_id}/plots` - Все участки города
- `POST /api/cities/{city_id}/plots/{x}/{y}/buy` - Покупка участка

## What's Implemented ✅
- [x] Система городов с уникальными формами
- [x] Изометрический вид (PixiJS WebGL)
- [x] Страница выбора городов (Map)
- [x] Аутентификация (Email/TonConnect)
- [x] Мобильная адаптация (нижняя навигация)
- [x] Настройки пользователя (выход, смена данных)
- [x] Интернационализация (8 языков)

## Backlog
- [ ] AI-генерация спрайтов зданий
- [ ] Google OAuth (требуются ключи)
- [ ] Строительство бизнесов в городах
- [ ] Торговля ресурсами между игроками
- [ ] Загрузка пользовательских аватаров

## Last Updated
2026-01-29
