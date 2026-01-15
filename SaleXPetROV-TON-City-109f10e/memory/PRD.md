# TON City Builder (Cryptoland) - PRD

## Overview
Full-stack city-building game on the TON blockchain.

## Tech Stack
- **Frontend**: React 18, TailwindCSS, Shadcn/UI, Framer Motion, Konva (map)
- **Backend**: FastAPI, Motor (MongoDB), APScheduler
- **Database**: MongoDB

## Current Status (Jan 15, 2025)

### Completed Today
- [x] **Fixed duplicate Tutorial buttons** - теперь только одна кнопка при подключённом кошельке
- [x] **User-friendly wallet addresses** - конвертация 0:abc... → UQabc... формат
- [x] **Extended Tutorial** - 9 шагов: депозит, покупка, строительство, связи, торговля, налоги, вывод, стратегия
- [x] **New Game Layout** - карта по центру, список участков справа с ценами

### Key Features
- TON wallet connection via TonConnect
- Internal balance system (deposit TON → play → withdraw)
- 100x100 grid map with 5 zones
- 22 business types
- Player trading market
- Admin panel with treasury warnings

### Backend Environment
```env
MONGO_URL="mongodb://localhost:27017"
DB_NAME="ton_city_production"
ADMIN_WALLET="your_wallet_here"  # Auto-admin
```

### APIs Working
- `/api/health`, `/api/stats`, `/api/stats/online`
- `/api/plots`, `/api/businesses/types`
- `/api/auth/verify-wallet`, `/api/admin/treasury-health`

### Pending Tasks (P1)
1. Admin withdrawal execution (send TON)
2. UI responsiveness for mobile

### Backlog
- FunC smart contract
- Testnet/Mainnet switch
- Code refactoring

### Documentation
- `/app/DEPLOYMENT_GUIDE.md` - VPS & testnet setup
- `/app/ECONOMY_MODEL.md` - Financial sustainability
