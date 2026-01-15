# ⚡ Localhost - Шпаргалка (1 страница)

## 🚀 ЗАПУСК ЗА 3 МИНУТЫ

### ✅ Требования
- Node.js 18+
- Python 3.9+
- MongoDB 5.0+
- Yarn

---

## 📝 КОМАНДЫ

### 1️⃣ MongoDB
```bash
brew services start mongodb-community  # macOS
sudo systemctl start mongod            # Linux
# Windows: Службы → MongoDB → Запустить
```

### 2️⃣ Backend (Терминал 1)
```bash
cd backend
python3 -m venv venv
source venv/bin/activate    # macOS/Linux
# venv\Scripts\activate     # Windows

pip install -r requirements.txt
uvicorn server:app --reload --host 0.0.0.0 --port 8001
```

### 3️⃣ Frontend (Терминал 2)
```bash
cd frontend
yarn install
yarn start
```

### 4️⃣ Открыть
```
http://localhost:3000
```

---

## 📄 .ENV файлы

### backend/.env
```env
MONGO_URL=mongodb://localhost:27017
DB_NAME=ton_city_builder
SECRET_KEY=your-secret-key-min-32-chars
CORS_ORIGINS=http://localhost:3000
```

### frontend/.env
```env
REACT_APP_BACKEND_URL=http://localhost:8001
```

---

## ✅ Проверка

```bash
# Backend
curl http://localhost:8001/api/health

# Frontend
http://localhost:3000

# MongoDB
mongosh
> use ton_city_builder
> show collections
```

---

## 🛑 Остановка

```bash
# Backend/Frontend: Ctrl + C
# MongoDB:
brew services stop mongodb-community  # macOS
sudo systemctl stop mongod            # Linux
```

---

## 🔧 Частые проблемы

```bash
# Port занят
lsof -i :8001
kill -9 <PID>

# ModuleNotFoundError
cd backend && source venv/bin/activate && pip install -r requirements.txt

# React ошибки
cd frontend && rm -rf node_modules && yarn install

# MongoDB не работает
brew services restart mongodb-community
```

---

## 👨‍💼 Админка

```bash
# 1. Создать админа
mongosh
> use ton_city_builder
> db.users.updateOne(
    { wallet_address: "YOUR_ADDRESS" },
    { $set: { is_admin: true } }
  )

# 2. Открыть
http://localhost:3000/admin
```

---

## 🎯 Итог

**3 терминала:**
1. MongoDB (фон или отдельный терминал)
2. Backend → http://localhost:8001
3. Frontend → http://localhost:3000

**Готово! 🎉**
