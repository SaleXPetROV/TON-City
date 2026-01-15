# 🚀 Запуск проекта на localhost - Пошаговая инструкция

## ✅ ШАГ 0: Проверка установленных программ

Откройте терминал и проверьте:

```bash
# Node.js (должно быть >= 18)
node --version

# Python (должно быть >= 3.9)
python3 --version

# MongoDB (должно быть >= 5.0)
mongosh --version

# Yarn
yarn --version
```

❌ **Если чего-то нет - установите:**

**Node.js:** https://nodejs.org/ (скачать и установить)

**Python:** https://www.python.org/downloads/ (скачать и установить)

**MongoDB:**
- macOS: `brew install mongodb-community`
- Windows: https://www.mongodb.com/try/download/community
- Linux: `sudo apt install mongodb`

**Yarn:**
```bash
npm install -g yarn
```

---

## 📁 ШАГ 1: Распаковать проект

```bash
# Если у вас ZIP файл
unzip Cryptoland-main.zip
cd Cryptoland-main

# Или если уже распакован
cd путь/к/проекту
```

---

## 🗄️ ШАГ 2: БАЗА ДАННЫХ (MongoDB)

### 2.1. Запустить MongoDB

**macOS:**
```bash
brew services start mongodb-community
```

**Linux:**
```bash
sudo systemctl start mongod
```

**Windows:**
- Откройте "Службы" (Services)
- Найдите "MongoDB Server"
- Нажмите "Запустить"

**Или запустить вручную:**
```bash
# Создать папку для данных
mkdir -p ~/mongodb-data

# Запустить MongoDB
mongod --dbpath ~/mongodb-data
```

### 2.2. Проверить что MongoDB работает

```bash
mongosh

# Должно подключиться. Увидите:
# Current Mongosh Log ID: ...
# Connecting to: mongodb://127.0.0.1:27017

# Выйти
exit
```

✅ **MongoDB запущена и работает!**

---

## 🐍 ШАГ 3: BACKEND (Python FastAPI)

### 3.1. Перейти в папку backend

```bash
cd backend
```

### 3.2. Создать виртуальное окружение

```bash
# Создать venv
python3 -m venv venv
```

### 3.3. Активировать виртуальное окружение

**macOS/Linux:**
```bash
source venv/bin/activate
```

**Windows (CMD):**
```bash
venv\Scripts\activate.bat
```

**Windows (PowerShell):**
```bash
venv\Scripts\Activate.ps1
```

После активации увидите `(venv)` в начале строки терминала.

### 3.4. Установить зависимости

```bash
pip install -r requirements.txt
```

Подождите 1-2 минуты. Должно установить все пакеты.

### 3.5. Создать файл .env

**Создайте файл `backend/.env` с содержимым:**

```env
MONGO_URL=mongodb://localhost:27017
DB_NAME=ton_city_builder
SECRET_KEY=super-secret-key-change-this-in-production-minimum-32-characters-long
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

**Как создать:**
- Создайте файл `.env` в папке `backend`
- Скопируйте текст выше
- Сохраните

### 3.6. Запустить Backend

```bash
uvicorn server:app --reload --host 0.0.0.0 --port 8001
```

**Должно появиться:**
```
INFO:     Uvicorn running on http://0.0.0.0:8001
INFO:     Application startup complete.
✅ TON Mainnet client initialized
✅ Background task scheduler started
✅ TON Payment Monitor started
```

✅ **Backend запущен на порту 8001!**

🔴 **НЕ ЗАКРЫВАЙТЕ это окно терминала!** Backend должен работать постоянно.

### 3.7. Проверить Backend (новый терминал)

Откройте **НОВЫЙ** терминал и выполните:

```bash
curl http://localhost:8001/api/health
```

**Должно вернуть:**
```json
{"status":"healthy","websocket":true}
```

✅ Или откройте в браузере: http://localhost:8001/api/health

---

## ⚛️ ШАГ 4: FRONTEND (React)

### 4.1. Открыть НОВЫЙ терминал

**НЕ закрывайте терминал с Backend!**

Откройте новое окно терминала.

### 4.2. Перейти в папку frontend

```bash
cd путь/к/проекту/frontend
```

### 4.3. Установить зависимости

```bash
yarn install
```

Подождите 2-3 минуты. Должно установить все пакеты.

**Если yarn не работает:**
```bash
npm install
```

### 4.4. Создать файл .env

**Создайте файл `frontend/.env` с содержимым:**

```env
REACT_APP_BACKEND_URL=http://localhost:8001
```

**Как создать:**
- Создайте файл `.env` в папке `frontend`
- Добавьте строку выше
- Сохраните

### 4.5. Запустить Frontend

```bash
yarn start
```

**Должно появиться:**
```
Compiled successfully!

You can now view the app in the browser.

  Local:            http://localhost:3000
  On Your Network:  http://192.168.x.x:3000
```

Браузер **автоматически откроется** на http://localhost:3000

✅ **Frontend запущен на порту 3000!**

🔴 **НЕ ЗАКРЫВАЙТЕ это окно терминала!** Frontend должен работать постоянно.

---

## 🎉 ШАГ 5: ПРОВЕРКА РАБОТЫ

### 5.1. Проверить Frontend

Откройте в браузере: **http://localhost:3000**

**Должно показать:**
- ✅ TON City Builder логотип
- ✅ "Connect Wallet" кнопка
- ✅ Селектор языка (EN/RU/ZH)
- ✅ Статистика игры

### 5.2. Проверить Backend API

Откройте в браузере: **http://localhost:8001/api/stats**

**Должно показать JSON:**
```json
{
  "total_plots": 10000,
  "owned_plots": 0,
  "available_plots": 10000,
  ...
}
```

### 5.3. Проверить MongoDB

```bash
mongosh

use ton_city_builder
show collections
db.users.countDocuments()

exit
```

---

## 📊 Итог: Что должно работать

У вас должно быть **3 открытых терминала:**

### Терминал 1: MongoDB
```
Либо как служба, либо:
mongod --dbpath ~/mongodb-data
```

### Терминал 2: Backend
```bash
cd backend
source venv/bin/activate
uvicorn server:app --reload --host 0.0.0.0 --port 8001
```

### Терминал 3: Frontend
```bash
cd frontend
yarn start
```

**Открыто в браузере:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8001/api

---

## 🎮 ТЕСТИРОВАНИЕ ФУНКЦИЙ

### 1. Подключить кошелек

1. Откройте http://localhost:3000
2. Нажмите "Connect Wallet"
3. Выберите TON кошелек (Tonkeeper, TON Space, etc.)
4. Подтвердите подключение

### 2. Зайти в админку

**Создать первого админа:**

```bash
mongosh

use ton_city_builder

# Замените YOUR_WALLET_ADDRESS на ваш адрес кошелька
db.users.updateOne(
  { wallet_address: "YOUR_WALLET_ADDRESS" },
  { $set: { is_admin: true } }
)

exit
```

**Открыть админку:**
http://localhost:3000/admin

### 3. Настроить TON кошелек (в админке)

1. Вкладка "TON Кошелек"
2. Выберите сеть: **Testnet**
3. Введите адрес кошелька для получения платежей
4. Сохранить

### 4. Получить тестовые TON

1. Telegram бот: https://t.me/testgiver_ton_bot
2. Отправьте команду: `/give YOUR_TESTNET_ADDRESS`
3. Получите тестовые TON

### 5. Протестировать игру

1. **Купить землю** - перейдите на страницу игры
2. **Построить бизнес** - выберите участок
3. **Просмотреть доход** - откройте Dashboard
4. **Торговля** - перейдите на Trading Market

---

## 🛑 КАК ОСТАНОВИТЬ

### Остановить Frontend
В терминале с Frontend нажмите: `Ctrl + C`

### Остановить Backend
В терминале с Backend нажмите: `Ctrl + C`

### Остановить MongoDB

**macOS:**
```bash
brew services stop mongodb-community
```

**Linux:**
```bash
sudo systemctl stop mongod
```

**Windows:**
- Службы → MongoDB Server → Остановить

---

## 🔄 КАК ПЕРЕЗАПУСТИТЬ

### Быстрый рестарт

**Терминал 1: Backend**
```bash
cd backend
source venv/bin/activate  # или venv\Scripts\activate
uvicorn server:app --reload --host 0.0.0.0 --port 8001
```

**Терминал 2: Frontend**
```bash
cd frontend
yarn start
```

MongoDB должна работать в фоне.

---

## ❗ ЧАСТЫЕ ПРОБЛЕМЫ

### Проблема 1: "Port 8001 already in use"

**Решение:**
```bash
# Найти процесс
lsof -i :8001

# Убить процесс
kill -9 <PID>
```

### Проблема 2: "Port 3000 already in use"

**Решение:**
```bash
# Найти процесс
lsof -i :3000

# Убить процесс
kill -9 <PID>
```

### Проблема 3: "ModuleNotFoundError"

**Решение:**
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### Проблема 4: "Cannot find module 'react'"

**Решение:**
```bash
cd frontend
rm -rf node_modules
yarn install
```

### Проблема 5: "MongoServerError: connect ECONNREFUSED"

**Решение:**
```bash
# Запустить MongoDB
brew services start mongodb-community  # macOS
sudo systemctl start mongod  # Linux
```

### Проблема 6: Frontend показывает пустую страницу

**Решение:**
1. Проверьте консоль браузера (F12)
2. Убедитесь что Backend запущен
3. Проверьте frontend/.env (должен быть REACT_APP_BACKEND_URL=http://localhost:8001)
4. Перезапустите Frontend

### Проблема 7: CORS ошибки

**Решение:**

В `backend/.env` должно быть:
```env
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

Перезапустите Backend.

---

## 📝 ЧЕКЛИСТ ЗАПУСКА

- [ ] MongoDB запущена (`mongosh` работает)
- [ ] Backend .env файл создан
- [ ] Backend venv активирован
- [ ] Backend зависимости установлены
- [ ] Backend запущен (порт 8001)
- [ ] Backend отвечает на http://localhost:8001/api/health
- [ ] Frontend .env файл создан
- [ ] Frontend зависимости установлены
- [ ] Frontend запущен (порт 3000)
- [ ] Frontend открывается в браузере
- [ ] Страница загружается без ошибок

---

## 🎯 КРАТКАЯ ПАМЯТКА

```bash
# 1. MongoDB
brew services start mongodb-community

# 2. Backend (терминал 1)
cd backend
source venv/bin/activate
uvicorn server:app --reload --host 0.0.0.0 --port 8001

# 3. Frontend (терминал 2)
cd frontend
yarn start

# 4. Открыть
# http://localhost:3000
```

---

## ✅ ВСЁ РАБОТАЕТ!

Теперь у вас:
- ✅ Backend работает на http://localhost:8001
- ✅ Frontend работает на http://localhost:3000
- ✅ MongoDB хранит данные
- ✅ Можно тестировать все функции

**Приятного тестирования! 🎉**
