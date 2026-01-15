# 🧪 Руководство по тестированию TON City

## 📋 Содержание
1. [Быстрый старт](#быстрый-старт)
2. [Управление БД через код](#управление-бд)
3. [Тестирование админки](#тестирование-админки)
4. [Тестирование покупки поля](#тестирование-покупки)
5. [Тестирование торговли](#тестирование-торговли)
6. [API тесты через curl](#api-тесты)

---

## 🚀 Быстрый старт

### Стать админом (первый шаг!)

```bash
# Способ 1: Через Python скрипт
cat > /tmp/make_admin.py << 'EOF'
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def make_admin():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["test_database"]
    
    # Введите свой адрес кошелька
    wallet = input("Введите адрес вашего кошелька: ")
    
    result = await db.users.update_one(
        {"wallet_address": wallet},
        {"$set": {"is_admin": True}},
        upsert=True
    )
    
    if result.modified_count > 0 or result.upserted_id:
        print(f"✅ Адрес {wallet} теперь админ!")
    else:
        print("⚠️ Пользователь не найден. Войдите в игру сначала.")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(make_admin())
EOF

python3 /tmp/make_admin.py
```

---

## 💾 Управление БД через код

### Создать тестового пользователя с балансом

```python
cat > /tmp/create_test_user.py << 'EOF'
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone

async def create_test_user():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["test_database"]
    
    test_user = {
        "wallet_address": "EQTestUser123456789",
        "username": "TestPlayer",
        "balance_game": 1000.0,  # 1000 TON игрового баланса
        "balance_ton": 0.0,
        "plots_owned": [],
        "businesses_owned": [],
        "is_admin": False,
        "language": "ru",
        "created_at": datetime.now(timezone.utc),
        "last_login": datetime.now(timezone.utc)
    }
    
    result = await db.users.insert_one(test_user)
    print(f"✅ Создан тестовый пользователь: {test_user['wallet_address']}")
    print(f"   Баланс: {test_user['balance_game']} TON")
    client.close()

if __name__ == "__main__":
    asyncio.run(create_test_user())
EOF

python3 /tmp/create_test_user.py
```

### Добавить баланс существующему пользователю

```python
cat > /tmp/add_balance.py << 'EOF'
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def add_balance():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["test_database"]
    
    wallet = input("Адрес кошелька: ")
    amount = float(input("Сумма для добавления: "))
    
    result = await db.users.update_one(
        {"wallet_address": wallet},
        {"$inc": {"balance_game": amount}}
    )
    
    if result.modified_count > 0:
        user = await db.users.find_one({"wallet_address": wallet})
        print(f"✅ Новый баланс: {user['balance_game']} TON")
    else:
        print("❌ Пользователь не найден")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(add_balance())
EOF

python3 /tmp/add_balance.py
```

### Посмотреть все участки

```python
cat > /tmp/view_plots.py << 'EOF'
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def view_plots():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["test_database"]
    
    total = await db.plots.count_documents({})
    owned = await db.plots.count_documents({"is_available": False})
    available = await db.plots.count_documents({"is_available": True})
    
    print(f"📊 Статистика участков:")
    print(f"   Всего: {total}")
    print(f"   Куплено: {owned}")
    print(f"   Доступно: {available}")
    
    # Показать 5 участков
    plots = await db.plots.find({}).limit(5).to_list(5)
    print(f"\n📍 Примеры участков:")
    for p in plots:
        status = "🟢 Свободен" if p.get('is_available') else f"🔴 Занят ({p.get('owner')})"
        print(f"   ({p['x']}, {p['y']}) - {status}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(view_plots())
EOF

python3 /tmp/view_plots.py
```

### Удалить все данные (сброс игры)

```python
cat > /tmp/reset_game.py << 'EOF'
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def reset_game():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["test_database"]
    
    confirm = input("⚠️  УДАЛИТЬ ВСЕ ДАННЫЕ? (yes/no): ")
    if confirm.lower() != "yes":
        print("Отменено")
        return
    
    # Удаляем всё кроме админов
    await db.plots.delete_many({})
    await db.businesses.delete_many({})
    await db.trade_contracts.delete_many({})
    await db.transactions.delete_many({})
    
    # Сбрасываем балансы пользователей (кроме админов)
    await db.users.update_many(
        {"is_admin": False},
        {"$set": {
            "balance_game": 0,
            "plots_owned": [],
            "businesses_owned": []
        }}
    )
    
    print("✅ Игра сброшена!")
    print("   - Все участки удалены")
    print("   - Все бизнесы удалены")
    print("   - Балансы игроков обнулены")
    print("   - Админы сохранены")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(reset_game())
EOF

python3 /tmp/reset_game.py
```

---

## 👨‍💼 Тестирование админки

### 1. Войти как админ

```bash
# 1. Сделайте себя админом (см. выше)
# 2. Откройте http://localhost:3000
# 3. Подключите кошелек
# 4. Перейдите на http://localhost:3000/admin
```

### 2. Настроить адрес кошелька для оплаты

```bash
# Через API
curl -X POST http://localhost:8001/api/admin/wallet-settings \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "network": "testnet",
    "receiver_address": "EQYourTestWalletAddress"
  }'

# Проверить настройки
curl http://localhost:8001/api/wallet-settings/public | jq
```

### 3. Просмотреть депозиты

```bash
curl -X GET http://localhost:8001/api/admin/deposits \
  -H "Authorization: Bearer YOUR_TOKEN" | jq
```

### 4. Одобрить вывод средств

```bash
# Получить список запросов
curl -X GET "http://localhost:8001/api/admin/withdrawals?status=pending" \
  -H "Authorization: Bearer YOUR_TOKEN" | jq

# Одобрить
curl -X POST "http://localhost:8001/api/admin/withdraw/WITHDRAWAL_ID/approve" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"tx_hash": "your_transaction_hash"}'
```

---

## 🏗️ Тестирование покупки поля

### Способ 1: Через UI

1. Откройте http://localhost:3000/game
2. Кликните на карте на свободную ячейку
3. Нажмите "Купить"
4. Подтвердите покупку

### Способ 2: Через API

```bash
# Получить токен авторизации (после входа в игру через UI)
TOKEN=$(cat ~/.ton_city_token 2>/dev/null || echo "YOUR_TOKEN")

# Купить участок
curl -X POST http://localhost:8001/api/plots/purchase \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "x": 50,
    "y": 50
  }'
```

### Способ 3: Прямая вставка в БД (для тестов)

```python
cat > /tmp/buy_plot_test.py << 'EOF'
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def buy_plot():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["test_database"]
    
    wallet = input("Адрес кошелька: ")
    x = int(input("Координата X: "))
    y = int(input("Координата Y: "))
    
    # Создать участок
    plot = {
        "x": x,
        "y": y,
        "owner": wallet,
        "is_available": False,
        "business_id": None,
        "zone": "center" if (x-50)**2 + (y-50)**2 < 100 else "outskirts"
    }
    
    result = await db.plots.insert_one(plot)
    
    # Добавить в список участков пользователя
    await db.users.update_one(
        {"wallet_address": wallet},
        {"$push": {"plots_owned": f"{x},{y}"}}
    )
    
    print(f"✅ Участок ({x}, {y}) куплен!")
    client.close()

if __name__ == "__main__":
    asyncio.run(buy_plot())
EOF

python3 /tmp/buy_plot_test.py
```

---

## 🏢 Тестирование строительства бизнеса

### Через API

```bash
# Построить бизнес на участке
curl -X POST http://localhost:8001/api/businesses/build \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "plot_x": 50,
    "plot_y": 50,
    "business_type": "farm"
  }'
```

### Через БД

```python
cat > /tmp/build_business.py << 'EOF'
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import uuid

async def build_business():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["test_database"]
    
    wallet = input("Адрес кошелька владельца: ")
    x = int(input("Координата X участка: "))
    y = int(input("Координата Y участка: "))
    
    # Типы бизнесов
    print("\nДоступные типы:")
    print("1. farm - Ферма")
    print("2. factory - Завод")
    print("3. shop - Магазин")
    print("4. bank - Банк")
    
    biz_type = input("Тип бизнеса: ")
    
    business_id = str(uuid.uuid4())
    
    # Создать бизнес
    business = {
        "id": business_id,
        "owner": wallet,
        "plot_x": x,
        "plot_y": y,
        "type": biz_type,
        "level": 1,
        "income_per_day": 10.0
    }
    
    await db.businesses.insert_one(business)
    
    # Обновить участок
    await db.plots.update_one(
        {"x": x, "y": y},
        {"$set": {"business_id": business_id}}
    )
    
    print(f"✅ Бизнес построен!")
    print(f"   ID: {business_id}")
    print(f"   Тип: {biz_type}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(build_business())
EOF

python3 /tmp/build_business.py
```

---

## 🤝 Тестирование торговли

### Создать предложение

```bash
curl -X POST http://localhost:8001/api/trade/contract \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "resource_type": "wood",
    "quantity": 100,
    "price_per_unit": 1.5,
    "contract_type": "sell"
  }'
```

### Посмотреть все предложения

```bash
curl http://localhost:8001/api/trade/contracts | jq
```

---

## 🔧 API тесты через curl

### Проверка здоровья

```bash
curl http://localhost:8001/api/health
```

### Статистика игры

```bash
curl http://localhost:8001/api/stats | jq
```

### Получить типы бизнесов

```bash
curl http://localhost:8001/api/businesses/types | jq
```

### Получить все участки

```bash
curl http://localhost:8001/api/plots | jq
```

### Получить настройки кошелька (публичные)

```bash
curl http://localhost:8001/api/wallet-settings/public | jq
```

---

## 📊 Мониторинг логов

### Backend логи

```bash
# Следить за логами в реальном времени
tail -f /var/log/supervisor/backend.out.log

# Ошибки
tail -f /var/log/supervisor/backend.err.log

# Последние 50 строк
tail -n 50 /var/log/supervisor/backend.out.log
```

### Frontend логи

```bash
tail -f /var/log/supervisor/frontend.out.log
```

### MongoDB логи

```bash
tail -f /var/log/mongodb/mongod.log
```

---

## 🎯 Быстрые команды

```bash
# Перезапустить всё
sudo supervisorctl restart all

# Проверить статус
sudo supervisorctl status

# Остановить сервисы
sudo supervisorctl stop all

# Запустить сервисы
sudo supervisorctl start all
```

---

## ⚡ Полезные скрипты

### Просмотр всех пользователей

```bash
mongosh test_database --eval "db.users.find().pretty()"
```

### Статистика БД

```bash
mongosh test_database --eval "
  printjson({
    users: db.users.countDocuments({}),
    plots: db.plots.countDocuments({}),
    businesses: db.businesses.countDocuments({}),
    trades: db.trade_contracts.countDocuments({})
  })
"
```

---

**Готово! Теперь вы можете тестировать всё без выхода из системы! 🚀**
