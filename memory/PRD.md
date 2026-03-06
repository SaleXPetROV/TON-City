# TON City - Product Requirements Document

## Original Problem Statement
TON City - блокчейн игра-стратегия на TON Blockchain. Нужно довести проект до 100% работоспособности.

Исходный отчёт показал:
- Backend 88.9% success rate (40/45 тестов)
- Minor issues: network switch endpoint, business model endpoint, wallet display format

## Architecture

### Tech Stack
- **Backend**: FastAPI (Python) + MongoDB
- **Frontend**: React.js + Tailwind CSS
- **Blockchain**: TON (The Open Network)
- **Auth**: JWT + TON Connect

### Key Components
- Game economy with businesses, credits, trading
- Admin panel with separate tabs (Credits, Promos, Users, etc.)
- TON wallet integration for payments
- Real-time features via WebSocket

## What's Been Implemented ✅

### Backend (100% Working)
- All admin endpoints returning 200:
  - `/api/admin/stats`
  - `/api/admin/credits` - with seized_building info
  - `/api/admin/promos`
  - `/api/admin/users`
  - `/api/admin/transactions`
  - `/api/admin/wallet-settings` - network switch
  - `/api/admin/treasury-health`
  - `/api/admin/announcements`
  - `/api/admin/withdrawals`
- `/api/public/business/financial-model` endpoint
- Promo codes "once per user" restriction
- Wallet address display in user-friendly format (UQ/EQ)

### Frontend
- Landing page with stats
- Admin panel with tabs: Credits, Promos, Users, etc.
- TON wallet connect integration
- Multi-language support (EN/RU)

## User Personas
1. **Players** - Buy land, build businesses, trade, earn TON
2. **Admin** - Manage game economy, credits, promos

## Core Requirements ✅
1. ✅ Credits tab separate from Promos
2. ✅ Promo codes can only be used once per user
3. ✅ Admin credits endpoint returns seized_building info
4. ✅ Admin wallet settings network switch works
5. ✅ All admin API endpoints return 200

## Next Action Items
- Configure TON receiver wallet address in admin panel
- Add more test users for load testing
- Implement mobile responsiveness improvements

## Backlog
- P0: None (all core features working)
- P1: TON mainnet deployment configuration
- P2: Advanced analytics dashboard
- P2: Push notifications via Telegram bot

## Test Credentials
- Admin: admin@toncity.com / Admin123!
- Test Player: testplayer@toncity.com / Test123!
