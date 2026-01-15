# TON City Builder - PRD (Updated)

## Original Problem Statement
Создать игру города с полной финансовой моделью на криптовалюте TON и привязкой кошелька. Каждый игрок должен купить поле, построить на нём бизнес, каждый бизнес должен быть взаимосвязан между собой, в фин системе работают только средства игроков. На одном поле можно строить только 1 бизнес.

## User Requirements
- Игровое поле: 100x100 (10,000 участков)
- Цена участка: 10 TON (окраина) → 100 TON (центр)
- 1 бизнес на поле
- Доход от взаимодействия между бизнесами
- TON Connect для кошелька
- Комиссии: 100% первичная продажа, 15% перепродажа, 13% подоходный налог
- Мультиязычность (EN/RU/ZH)
- Админ-панель

## Architecture

### Tech Stack
- **Backend**: FastAPI + Python + WebSocket
- **Frontend**: React + Tailwind CSS + Framer Motion + react-konva
- **Database**: MongoDB
- **Blockchain**: TON (via TON Connect)

### Business Types (22 total)

#### Primary Sector (Resources)
| Type | Cost | Base Income | Zone |
|------|------|-------------|------|
| 🌾 Farm | 5 TON | 2.4 TON/day | Residential, Industrial, Outskirts |
| ⚡ Power Plant | 20 TON | 2.4 TON/day | Industrial, Outskirts |
| ⛏️ Quarry | 25 TON | 6.0 TON/day | Industrial, Outskirts |
| 🛢️ Oil Rig | 40 TON | 8.0 TON/day | Industrial, Outskirts |
| 🪨 Mine | 35 TON | 7.0 TON/day | Industrial, Outskirts |

#### Secondary Sector (Manufacturing)
| Type | Cost | Base Income | Zone |
|------|------|-------------|------|
| 🏭 Factory | 15 TON | 2.88 TON/day | Business, Industrial |
| 🏗️ Construction Co. | 30 TON | 5.0 TON/day | Business, Industrial |
| 🏭 Refinery | 50 TON | 10.0 TON/day | Industrial |
| 🔩 Steel Mill | 45 TON | 9.0 TON/day | Industrial |
| 🧵 Textile Factory | 20 TON | 4.0 TON/day | Business, Industrial |

#### Tertiary Sector (Services)
| Type | Cost | Base Income | Zone |
|------|------|-------------|------|
| 🏪 Shop | 10 TON | 4.8 TON/day | Center, Business, Residential |
| 🍽️ Restaurant | 12 TON | 5.4 TON/day | Center, Business, Residential |
| 🏨 Hotel | 35 TON | 8.0 TON/day | Center, Business |
| 🏥 Hospital | 60 TON | 12.0 TON/day | Center, Business, Residential |
| 🎓 University | 70 TON | 10.0 TON/day | Center, Business |
| 📦 Logistics | 25 TON | 6.0 TON/day | Business, Industrial |
| ⛽ Gas Station | 15 TON | 4.0 TON/day | All zones |

#### Quaternary Sector (Finance & Tech)
| Type | Cost | Base Income | Zone |
|------|------|-------------|------|
| 🏦 Bank | 50 TON | 4.5 TON/day | Center, Business |
| 📊 Exchange | 100 TON | 20.0 TON/day | Center only (max 5 total) |
| 💻 Tech Hub | 80 TON | 15.0 TON/day | Center, Business |
| 🖥️ Data Center | 90 TON | 18.0 TON/day | Business, Industrial |
| 🛡️ Insurance | 40 TON | 6.0 TON/day | Center, Business |

### Level System (1-10)
| Level | Income Mult | Speed Mult | XP Required |
|-------|-------------|------------|-------------|
| 1 | ×1.0 | ×1.0 | 0 |
| 5 | ×2.2 | ×1.5 | 1000 |
| 10 | ×6.5 | ×3.0 | 5500 |

### Tax & Commissions
- Primary plot sale: 100% → Admin
- Resale: 15% commission
- Income tax: 13% (progressive up to 35% for monopolists)
- Trade commission: 5%
- Rental: 10%
- Withdrawal: 3% + network fee (min 1 TON)

## What's Implemented (December 2025)

### Backend ✅
- [x] 22 business types with full configuration
- [x] Level system 1-10 with income multipliers
- [x] Zone restrictions (Center, Business, Residential, Industrial, Outskirts)
- [x] Progressive tax system (13-35%)
- [x] Anti-monopoly limits (max plots/businesses per player)
- [x] WebSocket for real-time updates
- [x] Resource trading & contracts API
- [x] Income calculator API
- [x] Multilingual API (EN/RU/ZH)
- [x] Admin panel API (users, transactions, promos, announcements)
- [x] Withdrawal system with min 1 TON

### Frontend ✅
- [x] Landing page with language selector
- [x] TON Connect integration
- [x] Interactive city map (Canvas 100x100)
- [x] Income Calculator page
- [x] Dashboard with stats
- [x] Admin panel (withdrawals, users, promos, announcements)
- [x] Multilingual UI (EN/RU/ZH)

### Documentation ✅
- [x] `/app/docs/BUSINESS_MODEL.md` - Full economic model
- [x] `/app/docs/INCOME_TABLE.md` - Complete income reference
- [x] `/app/docs/DEPLOYMENT.md` - Server deployment guide

## Prioritized Backlog

### P0 - Critical ✅ DONE
- All core features implemented

### P1 - High Priority
- [ ] Connect real TON mainnet wallet
- [ ] Implement automatic income collection (cron)
- [ ] Add construction progress tracking
- [ ] Complete resource trading UI

### P2 - Medium Priority
- [ ] NFT certificates for plots
- [ ] Player-to-player plot marketplace
- [ ] Chat between neighbors
- [ ] Push notifications

### P3 - Low Priority
- [ ] Mobile app version
- [ ] Seasonal events
- [ ] Referral program
- [ ] Achievement system

## Next Tasks
1. Configure real game wallet for TON mainnet
2. Implement cron job for automatic income calculation
3. Add WebSocket frontend integration
4. Complete trading UI for resource contracts
