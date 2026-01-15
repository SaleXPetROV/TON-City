# TON City Builder - Deployment Guide

## 📋 Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Environment Variables](#environment-variables)
4. [Docker Deployment](#docker-deployment)
5. [Manual Deployment](#manual-deployment)
6. [WebSocket Configuration](#websocket-configuration)
7. [Nginx Configuration](#nginx-configuration)
8. [SSL/TLS Setup](#ssltls-setup)
9. [Database Setup](#database-setup)
10. [Monitoring](#monitoring)
11. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         LOAD BALANCER                            │
│                     (Nginx / CloudFlare)                         │
└─────────────────────┬───────────────────┬───────────────────────┘
                      │                   │
          ┌───────────┴───────┐   ┌───────┴───────────┐
          │   Frontend (3000)  │   │  Backend (8001)   │
          │   React + Nginx    │   │  FastAPI + Uvicorn│
          └───────────────────┘   └─────────┬─────────┘
                                            │
                                  ┌─────────┴─────────┐
                                  │  MongoDB (27017)  │
                                  └───────────────────┘
```

### Key Features
- **WebSocket Support**: Yes ✅ (via `/ws/{user_id}` endpoint)
- **Real-time Updates**: Plot purchases, business builds, announcements
- **Horizontal Scaling**: Supported with sticky sessions for WebSocket

---

## Prerequisites

### System Requirements
- **OS**: Ubuntu 20.04+ / Debian 11+ / CentOS 8+
- **RAM**: Minimum 2GB (4GB recommended)
- **CPU**: 2+ cores
- **Storage**: 20GB SSD minimum

### Software Requirements
```bash
# Node.js 18+
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Python 3.11+
sudo apt-get install python3.11 python3.11-venv python3-pip

# MongoDB 6.0+
# Follow: https://www.mongodb.com/docs/manual/installation/

# Nginx
sudo apt-get install nginx

# Certbot (for SSL)
sudo apt-get install certbot python3-certbot-nginx
```

---

## Environment Variables

### Backend (`/app/backend/.env`)
```env
# Database
MONGO_URL=mongodb://localhost:27017
DB_NAME=ton_city_builder

# Security
JWT_SECRET_KEY=your-super-secret-jwt-key-min-32-chars
ADMIN_SECRET=your-admin-secret-key-min-32-chars

# TON Configuration
GAME_WALLET_ADDRESS=UQYourGameWalletAddressHere
TON_API_KEY=your-toncenter-api-key

# CORS (comma-separated)
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Optional
LOG_LEVEL=INFO
```

### Frontend (`/app/frontend/.env`)
```env
# API URL (must be accessible from browser)
REACT_APP_BACKEND_URL=https://api.yourdomain.com

# Optional
REACT_APP_WS_URL=wss://api.yourdomain.com/ws
```

---

## Docker Deployment

### docker-compose.yml
```yaml
version: '3.8'

services:
  mongodb:
    image: mongo:6.0
    container_name: ton_city_mongo
    restart: always
    volumes:
      - mongo_data:/data/db
    environment:
      MONGO_INITDB_DATABASE: ton_city_builder
    ports:
      - "27017:27017"
    networks:
      - ton_city_network

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: ton_city_backend
    restart: always
    depends_on:
      - mongodb
    environment:
      - MONGO_URL=mongodb://mongodb:27017
      - DB_NAME=ton_city_builder
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - ADMIN_SECRET=${ADMIN_SECRET}
      - GAME_WALLET_ADDRESS=${GAME_WALLET_ADDRESS}
      - CORS_ORIGINS=${CORS_ORIGINS}
    ports:
      - "8001:8001"
    networks:
      - ton_city_network

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: ton_city_frontend
    restart: always
    depends_on:
      - backend
    environment:
      - REACT_APP_BACKEND_URL=${REACT_APP_BACKEND_URL}
    ports:
      - "3000:80"
    networks:
      - ton_city_network

volumes:
  mongo_data:

networks:
  ton_city_network:
    driver: bridge
```

### Backend Dockerfile
```dockerfile
# /app/backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8001

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "4"]
```

### Frontend Dockerfile
```dockerfile
# /app/frontend/Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app

COPY package.json yarn.lock ./
RUN yarn install --frozen-lockfile

COPY . .
RUN yarn build

FROM nginx:alpine
COPY --from=builder /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Deploy Commands
```bash
# Build and start
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop
docker-compose down

# Update single service
docker-compose up -d --build backend
```

---

## Manual Deployment

### Backend Setup
```bash
cd /app/backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run with gunicorn (production)
gunicorn server:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8001

# Or with uvicorn directly
uvicorn server:app --host 0.0.0.0 --port 8001 --workers 4
```

### Frontend Setup
```bash
cd /app/frontend

# Install dependencies
yarn install

# Build for production
yarn build

# The build folder is ready to be served by nginx
```

### Systemd Service (Backend)
```ini
# /etc/systemd/system/ton-city-backend.service
[Unit]
Description=TON City Builder Backend
After=network.target mongodb.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/app/backend
Environment="PATH=/app/backend/venv/bin"
EnvironmentFile=/app/backend/.env
ExecStart=/app/backend/venv/bin/gunicorn server:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8001
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start
sudo systemctl enable ton-city-backend
sudo systemctl start ton-city-backend
sudo systemctl status ton-city-backend
```

---

## WebSocket Configuration

### WebSocket Endpoint
```
ws://your-server:8001/ws/{user_id}
wss://api.yourdomain.com/ws/{user_id}  (with SSL)
```

### Features
- **Real-time plot updates**: When someone buys a plot
- **Business events**: Construction completed, income collected
- **Announcements**: Admin broadcasts
- **Ping/Pong**: Keep-alive mechanism

### Client Usage
```javascript
const ws = new WebSocket(`wss://api.yourdomain.com/ws/${userId}`);

ws.onopen = () => {
  console.log('Connected to WebSocket');
  // Start ping interval
  setInterval(() => ws.send(JSON.stringify({ type: 'ping' })), 30000);
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  switch (data.type) {
    case 'pong':
      // Keep-alive response
      break;
    case 'plot_sold':
      // Update map
      break;
    case 'business_built':
      // Update UI
      break;
    case 'announcement':
      // Show notification
      break;
  }
};

ws.onclose = () => {
  console.log('Disconnected, reconnecting...');
  // Implement reconnection logic
};
```

### Nginx WebSocket Proxy
```nginx
location /ws/ {
    proxy_pass http://localhost:8001;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_read_timeout 86400;
}
```

---

## Nginx Configuration

### Full Configuration
```nginx
# /etc/nginx/sites-available/ton-city

# API Backend
server {
    listen 80;
    server_name api.yourdomain.com;
    
    location / {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /ws/ {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
        proxy_send_timeout 86400;
    }
}

# Frontend
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    root /app/frontend/build;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    location /static/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
}
```

### Enable Configuration
```bash
sudo ln -s /etc/nginx/sites-available/ton-city /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## SSL/TLS Setup

### Using Certbot (Let's Encrypt)
```bash
# Install
sudo apt-get install certbot python3-certbot-nginx

# Get certificates
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com -d api.yourdomain.com

# Auto-renewal (already set up by certbot, verify with)
sudo certbot renew --dry-run
```

### Manual SSL with Custom Certificate
```nginx
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;
    
    ssl_certificate /etc/ssl/certs/yourdomain.crt;
    ssl_certificate_key /etc/ssl/private/yourdomain.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    
    # ... rest of config
}
```

---

## Database Setup

### MongoDB Initial Setup
```bash
# Connect to MongoDB
mongosh

# Create database and user
use ton_city_builder

db.createUser({
  user: "ton_city_user",
  pwd: "secure_password_here",
  roles: [{ role: "readWrite", db: "ton_city_builder" }]
})

# Create indexes for performance
db.plots.createIndex({ "x": 1, "y": 1 }, { unique: true })
db.plots.createIndex({ "owner": 1 })
db.plots.createIndex({ "zone": 1 })
db.businesses.createIndex({ "owner": 1 })
db.businesses.createIndex({ "plot_id": 1 })
db.transactions.createIndex({ "from_address": 1 })
db.transactions.createIndex({ "status": 1 })
db.transactions.createIndex({ "created_at": -1 })
db.users.createIndex({ "wallet_address": 1 }, { unique: true })
```

### Backup Script
```bash
#!/bin/bash
# /app/scripts/backup.sh

BACKUP_DIR="/backups/mongodb"
DATE=$(date +%Y%m%d_%H%M%S)

mongodump --db ton_city_builder --out "$BACKUP_DIR/$DATE"

# Keep only last 7 days
find $BACKUP_DIR -type d -mtime +7 -exec rm -rf {} +

echo "Backup completed: $BACKUP_DIR/$DATE"
```

---

## Monitoring

### Health Check Endpoints
```bash
# Backend health
curl https://api.yourdomain.com/api/health
# Expected: {"status":"healthy","websocket":true}

# Frontend
curl https://yourdomain.com
```

### Log Locations
```
Backend:  /var/log/ton-city/backend.log (if using systemd)
          docker logs ton_city_backend (if using Docker)
Frontend: /var/log/nginx/access.log
MongoDB:  /var/log/mongodb/mongod.log
```

### Prometheus Metrics (Optional)
Add to `server.py`:
```python
from prometheus_client import Counter, Histogram, generate_latest

REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests')
REQUEST_LATENCY = Histogram('http_request_latency_seconds', 'HTTP request latency')

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

---

## Troubleshooting

### Common Issues

#### 1. WebSocket Connection Failed
```bash
# Check if backend is running
curl http://localhost:8001/api/health

# Check nginx WebSocket config
nginx -t

# Check firewall
sudo ufw status
sudo ufw allow 8001
```

#### 2. MongoDB Connection Error
```bash
# Check MongoDB status
sudo systemctl status mongodb

# Check connection
mongosh --eval "db.adminCommand('ping')"

# Check logs
sudo tail -f /var/log/mongodb/mongod.log
```

#### 3. CORS Errors
```bash
# Verify CORS_ORIGINS in .env
# Must include full URL with protocol
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

#### 4. Frontend Not Loading
```bash
# Check build
ls -la /app/frontend/build

# Check nginx config
nginx -t

# Check permissions
sudo chown -R www-data:www-data /app/frontend/build
```

### Performance Optimization

```nginx
# Add to nginx.conf
worker_processes auto;
worker_connections 1024;

# Enable gzip
gzip on;
gzip_comp_level 6;
gzip_types text/plain text/css application/json application/javascript;

# Enable caching
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m max_size=100m inactive=60m;
```

---

## Quick Start Checklist

- [ ] Install prerequisites (Node.js, Python, MongoDB, Nginx)
- [ ] Clone repository
- [ ] Configure `.env` files (backend and frontend)
- [ ] Set up MongoDB with indexes
- [ ] Build frontend (`yarn build`)
- [ ] Configure Nginx
- [ ] Set up SSL with Certbot
- [ ] Start backend service
- [ ] Test health endpoints
- [ ] Create first admin user:
  ```bash
  mongosh ton_city_builder
  db.users.updateOne(
    { wallet_address: "YOUR_WALLET_ADDRESS" },
    { $set: { is_admin: true } }
  )
  ```
- [ ] Test WebSocket connection
- [ ] Set up monitoring and backups

---

## Support

For issues and questions:
- Check logs first
- Review this documentation
- Open an issue on GitHub

**WebSocket Status**: ✅ Fully supported
**Real-time Features**: ✅ Plot updates, business events, announcements
