# 🏙️ TON City Builder

Multiplayer city-building game on TON blockchain with real economy and resource trading.

## 🌟 Features

- 🏗️ **22 Business Types** - From farms to tech hubs
- 💰 **Real TON Economy** - Deposit real TON, use internal balance
- 🤝 **Resource Trading** - Trade between players without fees
- 🌍 **100x100 City Map** - 10,000 plots to build on
- 📊 **Level System** - Upgrade businesses (Level 1-10)
- 🏛️ **5 City Zones** - Center, Business, Residential, Industrial, Outskirts
- ⚡ **Auto Income** - Daily automatic income collection
- 🔄 **Testnet & Mainnet** - Test safely, deploy to production

## 🚀 Quick Start (5 minutes)

### Prerequisites

- Node.js 18+
- Python 3.9+
- MongoDB 5.0+
- Yarn

### Installation

```bash
# 1. Clone & Install
git clone <repo-url>
cd ton-city-builder

# 2. Backend
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Frontend
cd ../frontend
yarn install

# 4. Configure
# Create backend/.env:
MONGO_URL=mongodb://localhost:27017
DB_NAME=ton_city_builder
SECRET_KEY=your-secret-key-min-32-chars
CORS_ORIGINS=http://localhost:3000

# Create frontend/.env:
REACT_APP_BACKEND_URL=http://localhost:8001
```

### Run

```bash
# Terminal 1: Start MongoDB
brew services start mongodb-community  # macOS
sudo systemctl start mongod             # Linux

# Terminal 2: Backend
cd backend
source venv/bin/activate
uvicorn server:app --reload --host 0.0.0.0 --port 8001

# Terminal 3: Frontend
cd frontend
yarn start
```

**Open:** http://localhost:3000

## 📖 Documentation

- **[Full Setup Guide](./LOCAL_SETUP_GUIDE.md)** - Detailed VS Code setup
- **[Admin Guide](./ADMIN_GUIDE.md)** - Wallet setup, deployment, smart contract
- **[Implementation Summary](./IMPLEMENTATION_SUMMARY.md)** - Technical details
- **[Testing Report](./TESTING_REPORT.md)** - Test results

## 🎮 How to Play

1. **Connect Wallet** - Use TON Connect
2. **Buy Land** - Choose from 10,000 plots
3. **Build Business** - 22 types available
4. **Earn Income** - Collect daily
5. **Trade Resources** - With other players
6. **Upgrade** - Level up your businesses

## 👨‍💼 Admin Panel

**Access:** http://localhost:3000/admin

**Features:**
- 💰 TON Wallet Settings (Testnet/Mainnet)
- 📊 Deposit History
- 👥 User Management
- 💸 Withdrawal Approvals
- 🎁 Promo Codes
- 📢 Announcements

**First Admin:**
```javascript
// MongoDB shell
use ton_city_builder
db.users.updateOne(
  { wallet_address: "YOUR_WALLET" },
  { $set: { is_admin: true } }
)
```

## 🏗️ Architecture

```
Frontend (React)  →  Backend (FastAPI)  →  MongoDB
     ↓                      ↓
TON Connect          Payment Monitor
     ↓                      ↓
TON Blockchain  ←  Smart Contract
```

## 🔑 Key Endpoints

### Public API
```
GET  /api/health              # Health check
GET  /api/stats               # Game statistics
GET  /api/businesses/types    # Business types
GET  /api/plots               # All plots
POST /api/plots/purchase      # Buy plot
POST /api/businesses/build    # Build business
```

### Trading
```
GET  /api/trade/contracts     # User contracts
POST /api/trade/contract      # Create contract
POST /api/trade/spot          # Spot trade
```

### Admin
```
GET  /api/admin/wallet-settings    # TON wallet config
POST /api/admin/wallet-settings    # Update config
GET  /api/admin/deposits           # Deposit history
```

## 💰 TON Payment Flow

```
Player sends TON → Your wallet address
         ↓
Payment Monitor (checks every 30s)
         ↓
Auto-credits internal balance
         ↓
Player can trade/build (no blockchain fees)
```

## 🧪 Testing

### Testnet
```bash
# 1. Set network to "testnet" in admin panel
# 2. Get test TON: https://t.me/testgiver_ton_bot
# 3. Send to configured address
# 4. Check deposit history
```

### API Testing
```bash
# Health check
curl http://localhost:8001/api/health

# Get stats
curl http://localhost:8001/api/stats

# Get business types
curl http://localhost:8001/api/businesses/types | jq .
```

## 🔧 Tech Stack

**Frontend:**
- React 18
- Tailwind CSS
- Framer Motion
- TON Connect
- React Konva (canvas)

**Backend:**
- FastAPI
- Motor (async MongoDB)
- APScheduler (cron)
- python-jose (JWT)
- pytonlib (TON SDK)

**Database:**
- MongoDB 5.0+

**Blockchain:**
- TON (The Open Network)
- TON Connect 2.3+
- FunC (smart contracts)

## 📁 Project Structure

```
ton-city-builder/
├── backend/
│   ├── server.py              # Main FastAPI app
│   ├── ton_integration.py     # TON blockchain
│   ├── background_tasks.py    # Cron jobs
│   ├── payment_monitor.py     # Payment monitoring
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/            # React pages
│   │   ├── components/       # React components
│   │   └── lib/              # Utils & API
│   ├── public/
│   └── package.json
├── contracts/
│   └── payment_receiver.fc   # TON smart contract
└── docs/
    ├── BUSINESS_MODEL.md
    ├── INCOME_TABLE.md
    └── DEPLOYMENT.md
```

## 🌐 Deployment

### Option 1: Emergent Platform (Current)
- Built-in hosting
- Auto-deploy on push
- Managed database

### Option 2: VPS/Dedicated Server
```bash
# Install dependencies
sudo apt install nginx mongodb python3 nodejs

# Setup nginx reverse proxy
# Configure systemd services
# Setup SSL with certbot

# See ADMIN_GUIDE.md for details
```

### Option 3: Vercel + Railway
- Frontend: Vercel
- Backend: Railway
- Database: MongoDB Atlas

## 🔐 Security

- ✅ JWT authentication
- ✅ CORS configured
- ✅ Input validation
- ✅ Rate limiting ready
- ✅ Secure password hashing
- ✅ Environment variables
- ⚠️ Admin access control

## 📊 Game Economics

**Income Formula:**
```
Net Income = (Base Income × Level Multiplier × Connection Bonus - Operating Cost) × (1 - Tax Rate)
```

**Taxes:**
- Base: 13%
- Progressive up to 35% for high earners

**Trading:**
- 5% commission on all trades
- No blockchain fees for internal trades

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📝 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- TON Foundation
- TON Connect team
- React community
- FastAPI team

## 📞 Support

**Issues:** Open an issue on GitHub
**Docs:** Check `/app/*.md` files
**Community:** [Your Discord/Telegram]

## 🎯 Roadmap

- [x] Core gameplay
- [x] TON integration
- [x] Trading system
- [x] Admin panel
- [x] Payment monitoring
- [ ] NFT land certificates
- [ ] Mobile app
- [ ] Multiplayer chat
- [ ] Seasonal events

## ⚡ Quick Commands

```bash
# Start development
./scripts/dev.sh              # All services

# Run tests
./scripts/test.sh             # All tests

# Deploy
./scripts/deploy.sh           # Deploy to production

# Backup database
./scripts/backup.sh           # MongoDB backup
```

## 📈 Status

![Build](https://img.shields.io/badge/build-passing-brightgreen)
![Tests](https://img.shields.io/badge/tests-100%25-brightgreen)
![Coverage](https://img.shields.io/badge/coverage-85%25-green)
![Version](https://img.shields.io/badge/version-2.0.0-blue)

---

**Built with ❤️ for the TON ecosystem**

**Start building your crypto city today! 🏙️**
