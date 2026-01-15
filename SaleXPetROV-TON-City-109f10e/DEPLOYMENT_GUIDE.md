# Руководство по развертыванию TON City Builder

## Содержание
1. [Локальное тестирование с Testnet](#локальное-тестирование-с-testnet)
2. [Развертывание на VPS](#развертывание-на-vps)
3. [Настройка MongoDB](#настройка-mongodb)
4. [Настройка Nginx](#настройка-nginx)
5. [Supervisor и автозапуск](#supervisor-и-автозапуск)

---

## Локальное тестирование с Testnet

### Шаг 1: Создайте тестовый TON кошелёк

1. Установите расширение [TON Wallet](https://chrome.google.com/webstore/detail/ton-wallet/nphplpgoakhhjchkkhmiggakijnkhfnd) или [Tonkeeper](https://tonkeeper.com/)
2. Создайте новый кошелёк
3. **Важно:** Переключите кошелёк на **Testnet**:
   - В Tonkeeper: Настройки → Dev Menu → Testnet
   - В TON Wallet: Настройки → Network → Testnet

### Шаг 2: Получите тестовые TON

1. Перейдите на [TON Testnet Faucet](https://t.me/testgiver_ton_bot)
2. Отправьте боту ваш тестовый адрес кошелька
3. Получите 5 тестовых TON (можно повторять каждые 24 часа)

### Шаг 3: Настройте проект для Testnet

Измените `backend/.env`:
```env
MONGO_URL="mongodb://localhost:27017"
DB_NAME="ton_city_testnet"
CORS_ORIGINS="*"
ADMIN_WALLET="ваш_тестовый_адрес_кошелька"
TON_NETWORK="testnet"
```

Измените манифест TonConnect в `frontend/public/tonconnect-manifest.json`:
```json
{
  "url": "http://localhost:3000",
  "name": "TON City Builder (Testnet)",
  "iconUrl": "http://localhost:3000/logo192.png"
}
```

### Шаг 4: Запустите проект локально

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 8001 --reload

# Frontend (новый терминал)
cd frontend
yarn install
yarn start
```

### Шаг 5: Тестирование транзакций

1. Откройте http://localhost:3000
2. Подключите тестовый кошелёк
3. Войдите в игру
4. Попробуйте пополнить баланс (депозит)
5. Попробуйте купить участок
6. Проверьте вывод средств

**Все транзакции будут в тестовой сети — реальные средства не затрагиваются!**

---

## Развертывание на VPS

### Требования к серверу
- Ubuntu 20.04+ или Debian 11+
- Минимум 2 ГБ RAM
- 20 ГБ диска
- Открытые порты: 22 (SSH), 80 (HTTP), 443 (HTTPS)

### Шаг 1: Подготовка сервера

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка необходимых пакетов
sudo apt install -y python3 python3-pip python3-venv nodejs npm nginx supervisor git certbot python3-certbot-nginx

# Установка MongoDB
wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list
sudo apt update
sudo apt install -y mongodb-org
sudo systemctl start mongod
sudo systemctl enable mongod

# Установка yarn
sudo npm install -g yarn
```

### Шаг 2: Клонирование проекта

```bash
cd /var/www
sudo git clone https://github.com/your-repo/ton-city-builder.git
sudo chown -R $USER:$USER ton-city-builder
cd ton-city-builder
```

### Шаг 3: Настройка Backend

```bash
cd /var/www/ton-city-builder/backend

# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt

# Настройка .env
cat > .env << EOF
MONGO_URL="mongodb://localhost:27017"
DB_NAME="ton_city_production"
CORS_ORIGINS="https://yourdomain.com"
ADMIN_WALLET="ваш_mainnet_адрес_кошелька"
TON_NETWORK="mainnet"
JWT_SECRET_KEY="$(openssl rand -hex 32)"
EOF
```

### Шаг 4: Настройка Frontend

```bash
cd /var/www/ton-city-builder/frontend

# Установка зависимостей
yarn install

# Настройка .env
cat > .env << EOF
REACT_APP_BACKEND_URL=https://yourdomain.com
EOF

# Обновление TonConnect манифеста
cat > public/tonconnect-manifest.json << EOF
{
  "url": "https://yourdomain.com",
  "name": "TON City Builder",
  "iconUrl": "https://yourdomain.com/logo192.png"
}
EOF

# Сборка для продакшена
yarn build
```

### Шаг 5: Настройка Nginx

```bash
sudo nano /etc/nginx/sites-available/ton-city
```

Содержимое:
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    # Frontend
    root /var/www/ton-city-builder/frontend/build;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # Backend API
    location /api {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
    
    # WebSocket
    location /ws {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/ton-city /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# SSL сертификат
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

### Шаг 6: Настройка Supervisor

```bash
sudo nano /etc/supervisor/conf.d/ton-city.conf
```

Содержимое:
```ini
[program:ton-city-backend]
directory=/var/www/ton-city-builder/backend
command=/var/www/ton-city-builder/backend/venv/bin/uvicorn server:app --host 127.0.0.1 --port 8001
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/supervisor/ton-city-backend.err.log
stdout_logfile=/var/log/supervisor/ton-city-backend.out.log
environment=PATH="/var/www/ton-city-builder/backend/venv/bin"
```

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start ton-city-backend
```

---

## Проверка работоспособности

```bash
# Проверка MongoDB
mongo --eval "db.adminCommand('ping')"

# Проверка Backend
curl http://localhost:8001/api/health

# Проверка через домен
curl https://yourdomain.com/api/health
```

---

## Обновление проекта

```bash
cd /var/www/ton-city-builder
git pull

# Backend
cd backend
source venv/bin/activate
pip install -r requirements.txt
sudo supervisorctl restart ton-city-backend

# Frontend
cd ../frontend
yarn install
yarn build
```

---

## Бэкап базы данных

```bash
# Создание бэкапа
mongodump --db ton_city_production --out /backup/$(date +%Y%m%d)

# Восстановление
mongorestore --db ton_city_production /backup/20250114/ton_city_production
```

---

## Мониторинг

Рекомендуемые инструменты:
- **UptimeRobot** — мониторинг доступности
- **Grafana + Prometheus** — метрики
- **Logwatch** — анализ логов

```bash
# Просмотр логов
sudo tail -f /var/log/supervisor/ton-city-backend.err.log
sudo tail -f /var/log/nginx/error.log
```
