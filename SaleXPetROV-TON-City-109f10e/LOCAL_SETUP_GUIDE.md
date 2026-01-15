# 🚀 Локальный запуск TON City Builder через VS Code

## 📋 Содержание
1. [Требования](#требования)
2. [Установка зависимостей](#установка-зависимостей)
3. [Настройка проекта](#настройка-проекта)
4. [Запуск через VS Code](#запуск-через-vs-code)
5. [Альтернативный запуск (терминалы)](#альтернативный-запуск)
6. [Проверка работы](#проверка-работы)
7. [Troubleshooting](#troubleshooting)

---

## ✅ Требования

Перед началом установите:

### 1. Node.js (v18+)
```bash
# Проверить версию
node --version  # Должно быть >= 18.0.0
npm --version
```

**Установка (если нет):**
- macOS: `brew install node`
- Windows: https://nodejs.org/
- Linux: `sudo apt install nodejs npm`

### 2. Python (v3.9+)
```bash
# Проверить версию
python3 --version  # Должно быть >= 3.9.0
pip3 --version
```

**Установка (если нет):**
- macOS: `brew install python@3.9`
- Windows: https://www.python.org/downloads/
- Linux: `sudo apt install python3 python3-pip`

### 3. MongoDB (v5.0+)
```bash
# Проверить статус
mongosh --version
```

**Установка:**
- macOS: `brew tap mongodb/brew && brew install mongodb-community`
- Windows: https://www.mongodb.com/try/download/community
- Linux: https://www.mongodb.com/docs/manual/tutorial/install-mongodb-on-ubuntu/

### 4. Yarn (package manager)
```bash
# Установить глобально
npm install -g yarn

# Проверить
yarn --version
```

### 5. VS Code
Скачать: https://code.visualstudio.com/

**Рекомендуемые расширения:**
- Python (Microsoft)
- ESLint
- Prettier
- MongoDB for VS Code
- GitLens
- Thunder Client (для тестирования API)

---

## 📦 Установка зависимостей

### Шаг 1: Клонировать проект

```bash
# Если проект на GitHub
git clone <repository-url>
cd ton-city-builder

# Или распаковать ZIP
unzip Cryptoland-main.zip
cd Cryptoland-main
```

### Шаг 2: Открыть в VS Code

```bash
code .
```

Или через VS Code:
- File → Open Folder → Выберите папку проекта

### Шаг 3: Установить Backend зависимости

**Терминал в VS Code (Terminal → New Terminal):**

```bash
# Перейти в папку backend
cd backend

# Создать виртуальное окружение
python3 -m venv venv

# Активировать venv
# macOS/Linux:
source venv/bin/activate

# Windows:
venv\Scripts\activate

# Установить зависимости
pip install -r requirements.txt
```

**Ожидаемый результат:**
```
Successfully installed fastapi uvicorn motor pymongo python-jose ...
```

### Шаг 4: Установить Frontend зависимости

**Новый терминал (Terminal → New Terminal):**

```bash
# Перейти в папку frontend
cd frontend

# Установить зависимости
yarn install

# Или если yarn не работает
npm install
```

**Ожидаемый результат:**
```
✓ Installed 1234 packages in 45s
```

---

## ⚙️ Настройка проекта

### 1. Запустить MongoDB

**macOS/Linux:**
```bash
# Запустить MongoDB
brew services start mongodb-community

# Или напрямую
mongod --config /usr/local/etc/mongod.conf

# Проверить
mongosh
> show dbs
> exit
```

**Windows:**
```bash
# Запустить как службу
net start MongoDB

# Или запустить mongod.exe напрямую
"C:\Program Files\MongoDB\Server\5.0\bin\mongod.exe"
```

**Проверка подключения:**
```bash
mongosh
> use test_database
> db.test.insertOne({ test: "Hello" })
> db.test.find()
> exit
```

### 2. Настроить Backend .env

**Создать файл `/backend/.env`:**

```bash
cd backend
```

**Содержимое файла `.env`:**

```env
# MongoDB
MONGO_URL=mongodb://localhost:27017
DB_NAME=ton_city_builder

# JWT
SECRET_KEY=your-super-secret-key-change-this-in-production-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# CORS (для локальной разработки)
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Game settings
GAME_WALLET_ADDRESS=EQxxxxxxxxxxxxxxxxxxxxxxxx
```

**В VS Code:**
1. Кликните правой кнопкой на папку `backend`
2. New File → `.env`
3. Скопируйте содержимое выше
4. Сохраните (Ctrl+S / Cmd+S)

### 3. Настроить Frontend .env

**Создать файл `/frontend/.env`:**

```bash
cd frontend
```

**Содержимое файла `.env`:**

```env
REACT_APP_BACKEND_URL=http://localhost:8001
```

**В VS Code:**
1. Кликните правой кнопкой на папку `frontend`
2. New File → `.env`
3. Добавьте строку выше
4. Сохраните

---

## 🚀 Запуск через VS Code

### Вариант 1: Использовать VS Code Tasks (Рекомендуется)

#### Создать файл `.vscode/tasks.json`:

1. В корне проекта создайте папку `.vscode`
2. Создайте файл `tasks.json`

**Содержимое `.vscode/tasks.json`:**

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Start Backend",
      "type": "shell",
      "command": "cd backend && source venv/bin/activate && uvicorn server:app --reload --host 0.0.0.0 --port 8001",
      "windows": {
        "command": "cd backend && venv\\Scripts\\activate && uvicorn server:app --reload --host 0.0.0.0 --port 8001"
      },
      "isBackground": true,
      "problemMatcher": {
        "pattern": {
          "regexp": "^(.*)$",
          "line": 1
        },
        "background": {
          "activeOnStart": true,
          "beginsPattern": ".*",
          "endsPattern": "Application startup complete"
        }
      },
      "presentation": {
        "reveal": "always",
        "panel": "dedicated",
        "group": "servers"
      }
    },
    {
      "label": "Start Frontend",
      "type": "shell",
      "command": "cd frontend && yarn start",
      "isBackground": true,
      "problemMatcher": {
        "pattern": {
          "regexp": "^(.*)$",
          "line": 1
        },
        "background": {
          "activeOnStart": true,
          "beginsPattern": ".*",
          "endsPattern": "webpack compiled|Compiled successfully"
        }
      },
      "presentation": {
        "reveal": "always",
        "panel": "dedicated",
        "group": "servers"
      }
    },
    {
      "label": "Start All",
      "dependsOn": ["Start Backend", "Start Frontend"],
      "problemMatcher": []
    }
  ]
}
```

#### Запустить проект:

1. **Нажмите:** `Ctrl+Shift+P` (Windows/Linux) или `Cmd+Shift+P` (macOS)
2. **Введите:** `Tasks: Run Task`
3. **Выберите:** `Start All`

**Или через меню:**
- Terminal → Run Task → Start All

**Результат:**
- Откроются 2 терминала
- Backend запустится на порту 8001
- Frontend запустится на порту 3000
- Браузер автоматически откроет http://localhost:3000

---

### Вариант 2: Создать Launch Configuration

#### Создать файл `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Backend",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "server:app",
        "--reload",
        "--host",
        "0.0.0.0",
        "--port",
        "8001"
      ],
      "cwd": "${workspaceFolder}/backend",
      "env": {
        "PYTHONPATH": "${workspaceFolder}/backend"
      },
      "console": "integratedTerminal"
    }
  ],
  "compounds": []
}
```

**Запуск:**
1. Нажмите F5 или Run → Start Debugging
2. Выберите "Python: Backend"

**Для Frontend:**
- Используйте отдельный терминал (см. ниже)

---

## 💻 Альтернативный запуск (Терминалы)

### Способ 1: Три отдельных терминала

#### Терминал 1: MongoDB
```bash
# Если не запущен как служба
mongod --dbpath ~/data/db
```

#### Терминал 2: Backend
```bash
# Активировать venv
cd backend
source venv/bin/activate  # macOS/Linux
# или venv\Scripts\activate  # Windows

# Запустить
uvicorn server:app --reload --host 0.0.0.0 --port 8001
```

**Ожидаемый вывод:**
```
INFO:     Uvicorn running on http://0.0.0.0:8001
INFO:     Application startup complete.
✅ TON Mainnet client initialized
✅ Background task scheduler started
✅ TON Payment Monitor started
```

#### Терминал 3: Frontend
```bash
cd frontend
yarn start
```

**Ожидаемый вывод:**
```
Compiled successfully!

You can now view ton-city-builder in the browser.

  Local:            http://localhost:3000
  On Your Network:  http://192.168.1.xxx:3000
```

### Способ 2: Tmux (для продвинутых)

```bash
# Создать сессию
tmux new -s ton-city

# Окно 1: Backend
cd backend && source venv/bin/activate && uvicorn server:app --reload --host 0.0.0.0 --port 8001

# Ctrl+B, C (создать новое окно)
# Окно 2: Frontend
cd frontend && yarn start

# Переключение между окнами: Ctrl+B, N
# Отключиться: Ctrl+B, D
# Подключиться: tmux attach -t ton-city
```

---

## ✅ Проверка работы

### 1. Проверить Backend

**Открыть в браузере:**
```
http://localhost:8001/api/health
```

**Ожидаемый ответ:**
```json
{
  "status": "healthy",
  "websocket": true
}
```

**Или через curl:**
```bash
curl http://localhost:8001/api/health
```

**Проверить другие endpoints:**
```bash
# Статистика игры
curl http://localhost:8001/api/stats

# Типы бизнесов
curl http://localhost:8001/api/businesses/types

# Список участков
curl http://localhost:8001/api/plots
```

### 2. Проверить Frontend

**Открыть в браузере:**
```
http://localhost:3000
```

**Должно отображаться:**
- ✅ Landing page
- ✅ "Connect Wallet" кнопка
- ✅ Селектор языка
- ✅ Статистика игры
- ✅ Логотип TON City

**Проверить консоль браузера (F12):**
- Не должно быть красных ошибок
- API запросы должны работать

### 3. Проверить MongoDB

```bash
mongosh

> use ton_city_builder
> show collections
> db.users.find().limit(1)
> exit
```

---

## 🔧 Troubleshooting

### Проблема 1: `ModuleNotFoundError: No module named 'fastapi'`

**Решение:**
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### Проблема 2: `Error: Cannot find module 'react'`

**Решение:**
```bash
cd frontend
rm -rf node_modules package-lock.json
yarn install
```

### Проблема 3: `MongoServerError: connect ECONNREFUSED 127.0.0.1:27017`

**Решение:**
```bash
# Проверить статус MongoDB
brew services list  # macOS
sudo systemctl status mongod  # Linux

# Запустить MongoDB
brew services start mongodb-community  # macOS
sudo systemctl start mongod  # Linux
```

### Проблема 4: Port already in use (8001 or 3000)

**Решение:**
```bash
# Найти процесс использующий порт
lsof -i :8001  # Backend
lsof -i :3000  # Frontend

# Убить процесс
kill -9 <PID>

# Или использовать другой порт
# Backend:
uvicorn server:app --reload --host 0.0.0.0 --port 8002

# Frontend:
PORT=3001 yarn start
```

### Проблема 5: CORS errors

**Решение:**

Проверьте `backend/.env`:
```env
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

И перезапустите backend.

### Проблема 6: Virtual environment not found

**Решение:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Проблема 7: Frontend не компилируется

**Решение:**
```bash
cd frontend

# Очистить кэш
rm -rf node_modules .cache build

# Переустановить
yarn install

# Запустить
yarn start
```

---

## 🎯 Quick Start (TL;DR)

```bash
# 1. Запустить MongoDB
brew services start mongodb-community  # macOS
sudo systemctl start mongod  # Linux

# 2. Backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn server:app --reload --host 0.0.0.0 --port 8001

# 3. Frontend (новый терминал)
cd frontend
yarn install
yarn start

# 4. Открыть
http://localhost:3000
```

---

## 📝 Полезные команды VS Code

### Терминалы:
- **Открыть терминал:** `` Ctrl+` `` или `Terminal → New Terminal`
- **Разделить терминал:** `Ctrl+Shift+5`
- **Переключение между терминалами:** `Alt+Up/Down`

### Отладка:
- **Запустить отладку:** `F5`
- **Остановить:** `Shift+F5`
- **Точка останова:** Кликнуть слева от номера строки

### Поиск:
- **Поиск в файлах:** `Ctrl+Shift+F`
- **Поиск в файле:** `Ctrl+F`

### Git:
- **Source Control:** `Ctrl+Shift+G`
- **Commit:** `Ctrl+Enter`

---

## 🚀 Готово к разработке!

Теперь у вас запущен полный стек:
- ✅ MongoDB на порту 27017
- ✅ Backend (FastAPI) на порту 8001
- ✅ Frontend (React) на порту 3000

**Разработка:**
- Backend: Изменения автоматически перезагружаются (`--reload`)
- Frontend: Hot reload включен по умолчанию
- MongoDB: Используйте MongoDB for VS Code для просмотра данных

**Полезные ссылки:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8001/api
- API Docs: http://localhost:8001/docs (Swagger)
- Admin Panel: http://localhost:3000/admin

**Happy coding! 🎉**
