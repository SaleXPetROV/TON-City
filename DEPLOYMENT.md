# 🚀 TON City Builder - Инструкция по установке на боевой сервер

## 📋 Требования

- Node.js 18+
- Python 3.11+
- MongoDB 6+
- Nginx (опционально)
- SSL сертификат (Let's Encrypt)

---

## 🔐 1. Google OAuth настройка

### Шаг 1: Создайте проект в Google Cloud Console

1. Перейдите на [console.cloud.google.com](https://console.cloud.google.com)
2. Создайте новый проект или выберите существующий
3. В боковом меню выберите **APIs & Services → Credentials**

### Шаг 2: Настройте OAuth consent screen

1. Выберите **OAuth consent screen** в левом меню
2. Выберите **External** (для публичного доступа)
3. Заполните обязательные поля:
   - **App name**: TON City Builder
   - **User support email**: ваш email
   - **Developer contact email**: ваш email
4. Добавьте скоупы: `email`, `profile`, `openid`
5. Если нужно - добавьте тестовых пользователей
6. Опубликуйте приложение (или оставьте в тестовом режиме)

### Шаг 3: Создайте OAuth credentials

1. Перейдите в **Credentials**
2. Нажмите **Create Credentials → OAuth Client ID**
3. Выберите **Web application**
4. Укажите:
   - **Name**: TON City Builder Web
   - **Authorized JavaScript origins**:
     ```
     https://yourdomain.com
     http://localhost:3000 (для разработки)
     ```
   - **Authorized redirect URIs**:
     ```
     https://yourdomain.com/auth
     http://localhost:3000/auth (для разработки)
     ```
5. Нажмите **Create**
6. Скопируйте **Client ID** и **Client Secret**

### Шаг 4: Добавьте в .env

```env
# Backend .env
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret

# Frontend .env
REACT_APP_GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
```

---

## 📧 2. SMTP для email (восстановление пароля)

### Вариант A: Gmail SMTP

1. Войдите в Google аккаунт
2. Включите 2FA: [myaccount.google.com/security](https://myaccount.google.com/security)
3. Создайте App Password:
   - Перейдите в **Security → App passwords**
   - Выберите **Mail** и **Other (Custom name)**
   - Введите "TON City Builder"
   - Скопируйте 16-значный пароль

```env
# Backend .env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=xxxx-xxxx-xxxx-xxxx  # App Password
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_FROM_NAME=TON City Builder
```

### Вариант B: Другие SMTP провайдеры

- **SendGrid**: smtp.sendgrid.net, port 587
- **Mailgun**: smtp.mailgun.org, port 587
- **Amazon SES**: email-smtp.region.amazonaws.com, port 587

---

## 💰 3. TON кошелёк для выплат

### Создание кошелька

1. Установите TON Keeper или другой кошелёк
2. Создайте новый кошелёк
3. Сохраните мнемоник-фразу (24 слова)

```env
# Backend .env
TON_WALLET_MNEMONIC=word1 word2 word3 ... word24
TON_DEPOSIT_ADDRESS=EQxxx... # Адрес для приёма депозитов
```

⚠️ **ВАЖНО**: Никогда не делитесь мнемоник-фразой! Храните в безопасном месте.

---

## 🖼️ 4. AI генерация спрайтов (опционально)

Для AI-генерации изометрических спрайтов зданий используется Emergent LLM Key.

```env
# Backend .env
EMERGENT_LLM_KEY=sk-emergent-xxx
```

Без этого ключа будут использоваться placeholder спрайты (SVG).

---

## 🛠️ 5. Установка на сервер

### Клонирование и настройка

```bash
# Клонируем репозиторий
git clone https://github.com/your-repo/ton-city-builder.git
cd ton-city-builder

# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Копируем и настраиваем .env
cp .env.example .env
nano .env  # Заполняем все переменные

# Frontend
cd ../frontend
yarn install
cp .env.example .env
nano .env
```

### Запуск через systemd

Создайте файлы сервисов:

**Backend** (`/etc/systemd/system/ton-city-backend.service`):
```ini
[Unit]
Description=TON City Builder Backend
After=network.target mongodb.service

[Service]
User=www-data
WorkingDirectory=/var/www/ton-city-builder/backend
Environment="PATH=/var/www/ton-city-builder/backend/venv/bin"
ExecStart=/var/www/ton-city-builder/backend/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

**Frontend** (`/etc/systemd/system/ton-city-frontend.service`):
```ini
[Unit]
Description=TON City Builder Frontend
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/ton-city-builder/frontend
ExecStart=/usr/bin/yarn start
Restart=always
RestartSec=5
Environment=NODE_ENV=production
Environment=PORT=3000

[Install]
WantedBy=multi-user.target
```

```bash
# Активация сервисов
sudo systemctl daemon-reload
sudo systemctl enable ton-city-backend ton-city-frontend
sudo systemctl start ton-city-backend ton-city-frontend
```

### Nginx конфигурация

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # Frontend
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
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

---

## 📊 6. Переменные окружения (полный список)

### Backend (.env)

```env
# Database
MONGO_URL=mongodb://localhost:27017
DB_NAME=ton_city_production

# Security
JWT_SECRET=your-super-secret-jwt-key-min-32-chars
CORS_ORIGINS=https://yourdomain.com

# Google OAuth
GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=xxx

# SMTP
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_FROM_NAME=TON City Builder

# TON Blockchain
TON_WALLET_MNEMONIC=word1 word2 ... word24
TON_DEPOSIT_ADDRESS=EQxxx...

# AI (optional)
EMERGENT_LLM_KEY=sk-emergent-xxx
```

### Frontend (.env)

```env
REACT_APP_BACKEND_URL=https://yourdomain.com
REACT_APP_GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
```

---

## ✅ Чеклист перед запуском

- [ ] MongoDB установлен и запущен
- [ ] Все .env переменные заполнены
- [ ] SSL сертификат настроен
- [ ] Google OAuth настроен и протестирован
- [ ] SMTP работает (отправьте тестовое письмо)
- [ ] TON кошелёк настроен
- [ ] Firewall открыт для портов 80, 443
- [ ] Бэкапы MongoDB настроены

---

## 🆘 Поддержка

При возникновении проблем проверьте логи:

```bash
# Backend logs
journalctl -u ton-city-backend -f

# Frontend logs  
journalctl -u ton-city-frontend -f

# MongoDB logs
journalctl -u mongodb -f
```
