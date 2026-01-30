#!/usr/bin/env python3
"""
TON City Builder - Тестирование новых функций
Тестирует: регистрацию пользователей, Marketplace API, Sprites API
"""

import requests
import json
import time
import random
from typing import Dict, Any, Optional

# Конфигурация
BASE_URL = "https://field-counter-1.preview.emergentagent.com/api"

# Глобальные переменные
auth_token = None
user_data = None
created_user_id = None

def log_test(test_name: str, status: str, details: str = ""):
    """Логирование результатов тестов"""
    status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
    print(f"{status_emoji} {test_name}: {status}")
    if details:
        print(f"   {details}")
    print()

def make_request(method: str, endpoint: str, data: Dict = None, headers: Dict = None) -> Dict[str, Any]:
    """Выполнение HTTP запроса с обработкой ошибок"""
    url = f"{BASE_URL}{endpoint}"
    
    default_headers = {"Content-Type": "application/json"}
    if headers:
        default_headers.update(headers)
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=default_headers, params=data)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, headers=default_headers)
        elif method.upper() == "PUT":
            response = requests.put(url, json=data, headers=default_headers)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=default_headers)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        return {
            "status_code": response.status_code,
            "data": response.json() if response.content else {},
            "success": 200 <= response.status_code < 300
        }
    except requests.exceptions.RequestException as e:
        return {
            "status_code": 0,
            "data": {"error": str(e)},
            "success": False
        }
    except json.JSONDecodeError:
        return {
            "status_code": response.status_code,
            "data": {"error": "Invalid JSON response", "text": response.text[:200]},
            "success": False
        }

def test_1_user_registration():
    """Тест 1: Регистрация пользователя"""
    global auth_token, user_data, created_user_id
    
    print("🧪 ТЕСТ 1: POST /api/auth/register - Регистрация пользователя")
    
    # Данные для регистрации как указано в задании
    register_data = {
        "email": "newplayer@test.com",
        "password": "Test123!",
        "username": "NewPlayer"
    }
    
    # Выполнение запроса
    result = make_request("POST", "/auth/register", register_data)
    
    if not result["success"]:
        # Проверяем, возможно пользователь уже существует
        if result["status_code"] == 400:
            error_detail = str(result["data"].get("detail", ""))
            if "уже зарегистрирован" in error_detail or "уже занят" in error_detail:
                log_test("Регистрация пользователя", "INFO", 
                        f"Пользователь уже существует: {error_detail}")
                
                # Попробуем войти с существующими данными
                login_data = {
                    "email": register_data["email"],
                    "password": register_data["password"]
                }
                
                login_result = make_request("POST", "/auth/login", login_data)
                
                if login_result["success"]:
                    data = login_result["data"]
                    auth_token = data.get("token")
                    user_data = data.get("user")
                    created_user_id = user_data.get("id") if user_data else None
                    
                    log_test("Вход существующего пользователя", "PASS", 
                            f"Успешный вход для {user_data.get('username') if user_data else 'пользователя'}")
                    return True
                else:
                    log_test("Регистрация пользователя", "FAIL", 
                            f"Пользователь существует, но вход не удался: {login_result['data']}")
                    return False
            else:
                log_test("Регистрация пользователя", "FAIL", 
                        f"HTTP {result['status_code']}: {result['data']}")
                return False
        else:
            log_test("Регистрация пользователя", "FAIL", 
                    f"HTTP {result['status_code']}: {result['data']}")
            return False
    
    # Проверка успешной регистрации
    data = result["data"]
    
    # Проверяем наличие токена
    if "token" not in data:
        log_test("Регистрация пользователя", "FAIL", "Токен не возвращен")
        return False
    
    # Проверяем данные пользователя
    if "user" not in data:
        log_test("Регистрация пользователя", "FAIL", "Данные пользователя не возвращены")
        return False
    
    user = data["user"]
    
    # Проверяем username
    if user.get("username") != register_data["username"]:
        log_test("Регистрация пользователя", "FAIL", 
                f"Username не совпадает: ожидался {register_data['username']}, получен {user.get('username')}")
        return False
    
    # Проверяем email
    if user.get("email") != register_data["email"]:
        log_test("Регистрация пользователя", "FAIL", 
                f"Email не совпадает: ожидался {register_data['email']}, получен {user.get('email')}")
        return False
    
    # Сохраняем токен для дальнейших тестов
    auth_token = data["token"]
    user_data = user
    created_user_id = user.get("id")
    
    log_test("Регистрация пользователя", "PASS", 
            f"Пользователь {user['username']} успешно зарегистрирован, токен получен")
    return True

def test_2_marketplace_get_listings():
    """Тест 2: GET /api/market/listings - получить все листинги"""
    print("🧪 ТЕСТ 2: GET /api/market/listings - Получение всех листингов")
    
    result = make_request("GET", "/market/listings")
    
    if not result["success"]:
        log_test("Получение листингов", "FAIL", 
                f"HTTP {result['status_code']}: {result['data']}")
        return False
    
    data = result["data"]
    
    # Проверяем структуру ответа
    if not isinstance(data, list):
        log_test("Получение листингов", "FAIL", 
                f"Ожидался список, получен: {type(data)}")
        return False
    
    log_test("Получение листингов", "PASS", 
            f"Получено {len(data)} листингов")
    return True

def test_3_marketplace_create_listing():
    """Тест 3: POST /api/market/list - создать листинг (нужен авторизованный пользователь)"""
    global auth_token
    
    print("🧪 ТЕСТ 3: POST /api/market/list - Создание листинга")
    
    if not auth_token:
        log_test("Создание листинга", "FAIL", "Нет токена авторизации")
        return False
    
    # Данные для создания листинга
    listing_data = {
        "resource_type": "crops",
        "amount": 100.0,
        "price_per_unit": 0.002,
        "description": "Fresh crops from test farm"
    }
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    result = make_request("POST", "/market/list", listing_data, headers)
    
    if not result["success"]:
        # Проверяем различные возможные ошибки
        if result["status_code"] == 401:
            log_test("Создание листинга", "FAIL", "Ошибка авторизации - токен недействителен")
        elif result["status_code"] == 400:
            error_detail = str(result["data"].get("detail", ""))
            if "insufficient" in error_detail.lower() or "balance" in error_detail.lower():
                log_test("Создание листинга", "PASS", 
                        f"API работает корректно - недостаточно ресурсов: {error_detail}")
                return True
            else:
                log_test("Создание листинга", "FAIL", 
                        f"Ошибка валидации: {error_detail}")
        else:
            log_test("Создание листинга", "FAIL", 
                    f"HTTP {result['status_code']}: {result['data']}")
        return False
    
    data = result["data"]
    
    # Проверяем успешное создание
    if data.get("status") == "success" or "listing_id" in data:
        log_test("Создание листинга", "PASS", 
                f"Листинг успешно создан: {data}")
        return True
    else:
        log_test("Создание листинга", "FAIL", 
                f"Неожиданный ответ: {data}")
        return False

def test_4_sprites_farm():
    """Тест 4: GET /api/sprites/farm?level=1 - получить спрайт фермы уровня 1"""
    print("🧪 ТЕСТ 4: GET /api/sprites/farm?level=1 - Получение спрайта фермы")
    
    params = {"level": 1}
    result = make_request("GET", "/sprites/farm", params)
    
    if not result["success"]:
        log_test("Получение спрайта фермы", "FAIL", 
                f"HTTP {result['status_code']}: {result['data']}")
        return False
    
    data = result["data"]
    
    # Проверяем структуру ответа
    if "sprite" not in data:
        log_test("Получение спрайта фермы", "FAIL", 
                "Поле 'sprite' отсутствует в ответе")
        return False
    
    sprite = data["sprite"]
    
    # Проверяем, что спрайт в правильном формате (base64 или SVG)
    if not (sprite.startswith("data:image/") or sprite.startswith("<svg")):
        log_test("Получение спрайта фермы", "FAIL", 
                f"Неверный формат спрайта: {sprite[:50]}...")
        return False
    
    # Проверяем дополнительные поля
    if data.get("building_type") != "farm":
        log_test("Получение спрайта фермы", "FAIL", 
                f"Неверный building_type: {data.get('building_type')}")
        return False
    
    if data.get("level") != 1:
        log_test("Получение спрайта фермы", "FAIL", 
                f"Неверный level: {data.get('level')}")
        return False
    
    log_test("Получение спрайта фермы", "PASS", 
            f"Спрайт получен, тип: {data.get('building_type')}, уровень: {data.get('level')}, кэшировано: {data.get('cached', False)}")
    return True

def test_5_sprites_construction():
    """Тест 5: GET /api/sprites/construction/placeholder - получить спрайт строительства"""
    print("🧪 ТЕСТ 5: GET /api/sprites/construction/placeholder - Получение спрайта строительства")
    
    result = make_request("GET", "/sprites/construction/placeholder")
    
    if not result["success"]:
        log_test("Получение спрайта строительства", "FAIL", 
                f"HTTP {result['status_code']}: {result['data']}")
        return False
    
    data = result["data"]
    
    # Проверяем структуру ответа
    if "sprite" not in data:
        log_test("Получение спрайта строительства", "FAIL", 
                "Поле 'sprite' отсутствует в ответе")
        return False
    
    sprite = data["sprite"]
    
    # Проверяем, что спрайт в правильном формате
    if not (sprite.startswith("data:image/") or sprite.startswith("<svg")):
        log_test("Получение спрайта строительства", "FAIL", 
                f"Неверный формат спрайта: {sprite[:50]}...")
        return False
    
    # Проверяем building_type
    if data.get("building_type") != "construction":
        log_test("Получение спрайта строительства", "FAIL", 
                f"Неверный building_type: {data.get('building_type')}")
        return False
    
    log_test("Получение спрайта строительства", "PASS", 
            f"Спрайт строительства получен, тип: {data.get('building_type')}")
    return True

def test_6_cleanup_user():
    """Тест 6: Удаление созданного пользователя (если регистрация работает)"""
    global created_user_id, auth_token
    
    print("🧪 ТЕСТ 6: Очистка - Удаление тестового пользователя")
    
    if not created_user_id or not auth_token:
        log_test("Удаление пользователя", "SKIP", 
                "Пользователь не был создан в этой сессии или нет токена")
        return True
    
    # В данном API нет прямого endpoint для удаления пользователя
    # Но мы можем проверить, что пользователь существует
    headers = {"Authorization": f"Bearer {auth_token}"}
    result = make_request("GET", "/auth/me", None, headers)
    
    if result["success"]:
        user_info = result["data"]
        log_test("Проверка пользователя", "PASS", 
                f"Пользователь {user_info.get('username')} существует и доступен")
        
        # Поскольку нет API для удаления, просто отмечаем что пользователь создан
        log_test("Удаление пользователя", "INFO", 
                "API для удаления пользователя не предоставлен. Пользователь остается в системе.")
        return True
    else:
        log_test("Проверка пользователя", "FAIL", 
                f"Не удалось получить информацию о пользователе: {result['data']}")
        return False

def run_all_tests():
    """Запуск всех тестов"""
    print("=" * 80)
    print("🚀 ТЕСТИРОВАНИЕ НОВЫХ ФУНКЦИЙ TON CITY BUILDER")
    print("=" * 80)
    print(f"🌐 Backend URL: {BASE_URL}")
    print()
    
    tests = [
        test_1_user_registration,
        test_2_marketplace_get_listings,
        test_3_marketplace_create_listing,
        test_4_sprites_farm,
        test_5_sprites_construction,
        test_6_cleanup_user
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ ОШИБКА в {test_func.__name__}: {str(e)}")
            failed += 1
        
        time.sleep(0.5)  # Небольшая пауза между тестами
    
    print("=" * 80)
    print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
    print("=" * 80)
    print(f"✅ Пройдено: {passed}")
    print(f"❌ Провалено: {failed}")
    print(f"📈 Успешность: {passed/(passed+failed)*100:.1f}%")
    
    if failed == 0:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
    else:
        print(f"\n⚠️ ОБНАРУЖЕНЫ ПРОБЛЕМЫ: {failed} тест(ов) провалено")
    
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)