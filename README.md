# 🏙️ TON City Builder

Multiplayer city-building game on TON blockchain with real economy and resource trading.

## 🚀 Quick Start

```bash
# 1. Install dependencies
cd /app/backend && pip install -r requirements.txt
cd /app/frontend && yarn install

# 2. Start services
sudo supervisorctl restart all

# 3. Open in browser
# Frontend: http://localhost:3000
# Backend API: http://localhost:8001
# Admin Panel: http://localhost:3000/admin
```

## 📁 Project Structure

```
/app/
├── backend/              # FastAPI backend
│   ├── server.py        # Main application
│   ├── requirements.txt # Python dependencies
│   └── .env             # Environment variables
├── frontend/            # React frontend
│   ├── src/            # Source code
│   ├── public/         # Static assets
│   ├── package.json    # Dependencies
│   └── .env            # Environment variables
├── tests/              # Test files
└── TESTING_GUIDE_RU.md # Testing guide (Russian)
```

## 🎮 Features

- 🏗️ **100x100 City Map** - 10,000 plots to build on
- 💰 **Real TON Economy** - Deposit/withdraw real TON
- 🤝 **Resource Trading** - Trade between players
- 🏢 **Multiple Business Types** - Farms, factories, shops, banks
- 📊 **Level System** - Upgrade businesses (Level 1-10)
- 🏛️ **5 City Zones** - Different prices and income rates
- ⚡ **Auto Income** - Daily automatic collection
- 🌍 **Multilingual** - English, Russian, Chinese

## 🔧 Tech Stack

**Frontend:**
- React 18 + Tailwind CSS
- Konva (Canvas rendering)
- TON Connect
- Framer Motion

**Backend:**
- FastAPI + Motor (async MongoDB)
- APScheduler (cron jobs)
- JWT authentication
- TON SDK integration

**Database:**
- MongoDB 5.0+

## 📖 Documentation

- [Testing Guide (RU)](/app/TESTING_GUIDE_RU.md) - How to test admin, purchases, trading
- [Translations](/app/frontend/src/translations/translations.js) - i18n system

## 👨‍💼 Admin Panel

Access: http://localhost:3000/admin

**Become admin:**
```bash
mongosh test_database --eval "
  db.users.updateOne(
    {wallet_address: 'YOUR_WALLET'},
    {\$set: {is_admin: true}}
  )
"
```

## 🧪 Testing

See [TESTING_GUIDE_RU.md](./TESTING_GUIDE_RU.md) for:
- Database management scripts
- Admin panel testing
- Plot purchase testing
- Business building testing
- Trading system testing
- API testing with curl

## 🌐 Environment Variables

**Backend (.env):**
```env
MONGO_URL=mongodb://localhost:27017
DB_NAME=test_database
CORS_ORIGINS=*
```

**Frontend (.env):**
```env
REACT_APP_BACKEND_URL=https://your-domain.com
WDS_SOCKET_PORT=443
ENABLE_HEALTH_CHECK=false
```

## 🚢 Deployment

Currently deployed on Emergent platform with:
- Auto-deploy on git push
- Managed MongoDB
- Built-in supervisor for services
- HTTPS enabled

## 📊 Key Improvements Made

✅ Removed duplicate cross buttons in tutorial
✅ Added themed images for tutorial steps  
✅ Fixed wallet settings endpoint (public access)
✅ Fixed "Connection error" bug
✅ Implemented virtualization for map rendering (60 FPS)
✅ Color-coded zones on map
✅ Removed "Made with Emergent" badge
✅ Fixed input number arrows
✅ Improved center positioning
✅ Created comprehensive testing guide
✅ Built translation system (3 languages)

## 🤝 Contributing

1. Make changes to code
2. Test locally
3. Commit changes
4. Push to deploy automatically

## 📞 Support

- Issues: Create issue on GitHub
- Testing: See TESTING_GUIDE_RU.md
- Admin: Access /admin panel

---

**Built with ❤️ for the TON ecosystem**

