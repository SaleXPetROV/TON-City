#!/usr/bin/env python3
"""
Тестирование расширенной системы аутентификации TON City Builder Backend
"""

import requests
import json
import base64
import time
from typing import Dict, Any, Optional

# Конфигурация
BASE_URL = "https://profile-settings-14.preview.emergentagent.com/api"
TEST_DATABASE = "test_database"

# Тестовые данные
TEST_USER = {
    "email": "testuser@example.com",
    "password": "testpass123",
    "username": "testuser123"
}

TEST_USER_2 = {
    "email": "testuser2@example.com", 
    "password": "testpass456",
    "username": "testuser456"
}

# Глобальные переменные для токенов
auth_token = None
user_data = None

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
            response = requests.get(url, headers=default_headers)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, headers=default_headers)
        elif method.upper() == "PUT":
            response = requests.put(url, json=data, headers=default_headers)
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
            "data": {"error": "Invalid JSON response"},
            "success": False
        }

def test_1_register_email():
    """Тест 1: Регистрация через Email"""
    global auth_token, user_data
    
    print("🧪 ТЕСТ 1: POST /api/auth/register - Регистрация через Email")
    
    # Подготовка данных
    register_data = {
        "email": TEST_USER["email"],
        "password": TEST_USER["password"],
        "username": TEST_USER["username"]
    }
    
    # Выполнение запроса
    result = make_request("POST", "/auth/register", register_data)
    
    if not result["success"]:
        log_test("Регистрация через Email", "FAIL", 
                f"HTTP {result['status_code']}: {result['data']}")
        return False
    
    # Проверка ответа
    data = result["data"]
    
    # Проверяем наличие токена
    if "token" not in data:
        log_test("Регистрация через Email", "FAIL", "Токен не возвращен")
        return False
    
    # Проверяем данные пользователя
    if "user" not in data:
        log_test("Регистрация через Email", "FAIL", "Данные пользователя не возвращены")
        return False
    
    user = data["user"]
    
    # Проверяем username
    if user.get("username") != TEST_USER["username"]:
        log_test("Регистрация через Email", "FAIL", 
                f"Username не совпадает: ожидался {TEST_USER['username']}, получен {user.get('username')}")
        return False
    
    # Проверяем email
    if user.get("email") != TEST_USER["email"]:
        log_test("Регистрация через Email", "FAIL", 
                f"Email не совпадает: ожидался {TEST_USER['email']}, получен {user.get('email')}")
        return False
    
    # Проверяем наличие аватара (должен быть сгенерирован из инициалов)
    if "avatar" not in user or not user["avatar"]:
        log_test("Регистрация через Email", "FAIL", "Аватар не сгенерирован")
        return False
    
    # Проверяем, что аватар в формате base64 SVG
    if not user["avatar"].startswith("data:image/svg+xml;base64,"):
        log_test("Регистрация через Email", "FAIL", "Аватар не в формате SVG base64")
        return False
    
    # Сохраняем токен для дальнейших тестов
    auth_token = data["token"]
    user_data = user
    
    log_test("Регистрация через Email", "PASS", 
            f"Пользователь {user['username']} зарегистрирован, токен получен, аватар сгенерирован")
    return True

def test_2a_login_email():
    """Тест 2A: Вход через Email"""
    print("🧪 ТЕСТ 2A: POST /api/auth/login - Вход через Email")
    
    login_data = {
        "email": TEST_USER["email"],
        "password": TEST_USER["password"]
    }
    
    result = make_request("POST", "/auth/login", login_data)
    
    if not result["success"]:
        log_test("Вход через Email", "FAIL", 
                f"HTTP {result['status_code']}: {result['data']}")
        return False
    
    data = result["data"]
    
    # Проверяем токен и данные пользователя
    if "token" not in data or "user" not in data:
        log_test("Вход через Email", "FAIL", "Токен или данные пользователя отсутствуют")
        return False
    
    user = data["user"]
    if user.get("email") != TEST_USER["email"]:
        log_test("Вход через Email", "FAIL", "Email пользователя не совпадает")
        return False
    
    log_test("Вход через Email", "PASS", f"Успешный вход для {user['email']}")
    return True

def test_2b_login_username():
    """Тест 2B: Вход через Username"""
    print("🧪 ТЕСТ 2B: POST /api/auth/login - Вход через Username")
    
    # Используем username в поле email (как указано в требованиях)
    login_data = {
        "email": TEST_USER["username"],  # username вместо email
        "password": TEST_USER["password"]
    }
    
    result = make_request("POST", "/auth/login", login_data)
    
    if not result["success"]:
        log_test("Вход через Username", "FAIL", 
                f"HTTP {result['status_code']}: {result['data']}")
        return False
    
    data = result["data"]
    
    # Проверяем токен и данные пользователя
    if "token" not in data or "user" not in data:
        log_test("Вход через Username", "FAIL", "Токен или данные пользователя отсутствуют")
        return False
    
    user = data["user"]
    if user.get("username") != TEST_USER["username"]:
        log_test("Вход через Username", "FAIL", "Username пользователя не совпадает")
        return False
    
    log_test("Вход через Username", "PASS", f"Успешный вход для username {user['username']}")
    return True

def test_3_update_username():
    """Тест 3: Смена username"""
    global auth_token
    
    print("🧪 ТЕСТ 3: PUT /api/auth/update-username - Смена username")
    
    if not auth_token:
        log_test("Смена username", "FAIL", "Нет токена авторизации")
        return False
    
    new_username = "newusername123"
    update_data = {"username": new_username}
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    result = make_request("PUT", "/auth/update-username", update_data, headers)
    
    if not result["success"]:
        log_test("Смена username", "FAIL", 
                f"HTTP {result['status_code']}: {result['data']}")
        return False
    
    data = result["data"]
    
    if data.get("status") != "success":
        log_test("Смена username", "FAIL", f"Неожиданный статус: {data}")
        return False
    
    if data.get("username") != new_username:
        log_test("Смена username", "FAIL", 
                f"Username не обновился: ожидался {new_username}, получен {data.get('username')}")
        return False
    
    log_test("Смена username", "PASS", f"Username успешно изменен на {new_username}")
    
    # Обновляем тестовые данные
    TEST_USER["username"] = new_username
    return True

def test_4_update_email():
    """Тест 4: Смена email"""
    global auth_token
    
    print("🧪 ТЕСТ 4: PUT /api/auth/update-email - Смена email")
    
    if not auth_token:
        log_test("Смена email", "FAIL", "Нет токена авторизации")
        return False
    
    new_email = "newemail@example.com"
    update_data = {
        "email": new_email,
        "password": TEST_USER["password"]  # Требуется текущий пароль
    }
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    result = make_request("PUT", "/auth/update-email", update_data, headers)
    
    if not result["success"]:
        log_test("Смена email", "FAIL", 
                f"HTTP {result['status_code']}: {result['data']}")
        return False
    
    data = result["data"]
    
    if data.get("status") != "success":
        log_test("Смена email", "FAIL", f"Неожиданный статус: {data}")
        return False
    
    if data.get("email") != new_email:
        log_test("Смена email", "FAIL", 
                f"Email не обновился: ожидался {new_email}, получен {data.get('email')}")
        return False
    
    log_test("Смена email", "PASS", f"Email успешно изменен на {new_email}")
    
    # Обновляем тестовые данные
    TEST_USER["email"] = new_email
    return True

def test_5_update_password():
    """Тест 5: Смена пароля"""
    global auth_token
    
    print("🧪 ТЕСТ 5: PUT /api/auth/update-password - Смена пароля")
    
    if not auth_token:
        log_test("Смена пароля", "FAIL", "Нет токена авторизации")
        return False
    
    new_password = "newpass456"
    update_data = {
        "current_password": TEST_USER["password"],
        "new_password": new_password
    }
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    result = make_request("PUT", "/auth/update-password", update_data, headers)
    
    if not result["success"]:
        log_test("Смена пароля", "FAIL", 
                f"HTTP {result['status_code']}: {result['data']}")
        return False
    
    data = result["data"]
    
    if data.get("status") != "success":
        log_test("Смена пароля", "FAIL", f"Неожиданный статус: {data}")
        return False
    
    log_test("Смена пароля", "PASS", "Пароль успешно изменен")
    
    # Проверяем, что можно войти с новым паролем
    login_data = {
        "email": TEST_USER["email"],
        "password": new_password
    }
    
    login_result = make_request("POST", "/auth/login", login_data)
    
    if not login_result["success"]:
        log_test("Проверка нового пароля", "FAIL", "Не удается войти с новым паролем")
        return False
    
    log_test("Проверка нового пароля", "PASS", "Вход с новым паролем работает")
    
    # Обновляем тестовые данные
    TEST_USER["password"] = new_password
    return True

def test_6_link_wallet():
    """Тест 6: Привязка кошелька"""
    global auth_token
    
    print("🧪 ТЕСТ 6: POST /api/auth/link-wallet - Привязка кошелька")
    
    if not auth_token:
        log_test("Привязка кошелька", "FAIL", "Нет токена авторизации")
        return False
    
    test_wallet = "EQTest123456789abcdef"
    wallet_data = {"wallet_address": test_wallet}
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    result = make_request("POST", "/auth/link-wallet", wallet_data, headers)
    
    if not result["success"]:
        log_test("Привязка кошелька", "FAIL", 
                f"HTTP {result['status_code']}: {result['data']}")
        return False
    
    data = result["data"]
    
    if data.get("status") != "success":
        log_test("Привязка кошелька", "FAIL", f"Неожиданный статус: {data}")
        return False
    
    if data.get("wallet_address") != test_wallet:
        log_test("Привязка кошелька", "FAIL", 
                f"Кошелек не привязался: ожидался {test_wallet}, получен {data.get('wallet_address')}")
        return False
    
    log_test("Привязка кошелька", "PASS", f"Кошелек {test_wallet} успешно привязан")
    return True

def test_7_upload_avatar():
    """Тест 7: Загрузка аватара"""
    global auth_token
    
    print("🧪 ТЕСТ 7: POST /api/auth/upload-avatar - Загрузка аватара")
    
    if not auth_token:
        log_test("Загрузка аватара", "FAIL", "Нет токена авторизации")
        return False
    
    # Создаем тестовый base64 PNG (1x1 пиксель)
    test_avatar = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    
    avatar_data = {"avatar_data": test_avatar}
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    result = make_request("POST", "/auth/upload-avatar", avatar_data, headers)
    
    if not result["success"]:
        log_test("Загрузка аватара", "FAIL", 
                f"HTTP {result['status_code']}: {result['data']}")
        return False
    
    data = result["data"]
    
    if data.get("status") != "success":
        log_test("Загрузка аватара", "FAIL", f"Неожиданный статус: {data}")
        return False
    
    if data.get("avatar") != test_avatar:
        log_test("Загрузка аватара", "FAIL", "Аватар не обновился")
        return False
    
    log_test("Загрузка аватара", "PASS", "Аватар успешно загружен")
    return True

def test_validation_errors():
    """Тест валидации и ошибок"""
    print("🧪 ДОПОЛНИТЕЛЬНЫЕ ТЕСТЫ: Проверка валидации")
    
    # Тест уникальности email при регистрации
    duplicate_email_data = {
        "email": TEST_USER["email"],  # Уже существующий email
        "password": "somepass",
        "username": "someuser"
    }
    
    result = make_request("POST", "/auth/register", duplicate_email_data)
    
    if result["success"]:
        log_test("Проверка уникальности email", "FAIL", "Регистрация с дублирующим email прошла")
        return False
    
    if result["status_code"] != 400:
        log_test("Проверка уникальности email", "FAIL", 
                f"Неожиданный код ошибки: {result['status_code']}")
        return False
    
    log_test("Проверка уникальности email", "PASS", "Дублирующий email корректно отклонен")
    
    # Тест уникальности username при регистрации
    duplicate_username_data = {
        "email": "another@example.com",
        "password": "somepass",
        "username": TEST_USER["username"]  # Уже существующий username
    }
    
    result = make_request("POST", "/auth/register", duplicate_username_data)
    
    if result["success"]:
        log_test("Проверка уникальности username", "FAIL", "Регистрация с дублирующим username прошла")
        return False
    
    if result["status_code"] != 400:
        log_test("Проверка уникальности username", "FAIL", 
                f"Неожиданный код ошибки: {result['status_code']}")
        return False
    
    log_test("Проверка уникальности username", "PASS", "Дублирующий username корректно отклонен")
    
    # Тест неверного пароля при входе
    wrong_password_data = {
        "email": TEST_USER["email"],
        "password": "wrongpassword"
    }
    
    result = make_request("POST", "/auth/login", wrong_password_data)
    
    if result["success"]:
        log_test("Проверка неверного пароля", "FAIL", "Вход с неверным паролем прошел")
        return False
    
    if result["status_code"] != 401:
        log_test("Проверка неверного пароля", "FAIL", 
                f"Неожиданный код ошибки: {result['status_code']}")
        return False
    
    log_test("Проверка неверного пароля", "PASS", "Неверный пароль корректно отклонен")
    
    return True

def test_google_oauth_configuration():
    """Тест конфигурации Google OAuth"""
    print("🧪 ТЕСТ: Проверка конфигурации Google OAuth")
    
    # Попытка использовать Google OAuth без настроенных credentials
    google_data = {"credential": "fake_google_token"}
    
    result = make_request("POST", "/auth/google", google_data)
    
    # Ожидаем ошибку конфигурации
    if result["success"]:
        log_test("Google OAuth конфигурация", "WARN", 
                "Google OAuth работает (возможно, настроены реальные credentials)")
        return True
    
    if result["status_code"] == 500:
        error_msg = result["data"].get("detail", "")
        if "not configured" in error_msg:
            log_test("Google OAuth конфигурация", "PASS", 
                    "Google OAuth корректно сообщает об отсутствии конфигурации")
            return True
    
    log_test("Google OAuth конфигурация", "WARN", 
            f"Неожиданный ответ: HTTP {result['status_code']}: {result['data']}")
    return True

def run_all_tests():
    """Запуск всех тестов"""
    print("=" * 80)
    print("🚀 ЗАПУСК ТЕСТОВ СИСТЕМЫ АУТЕНТИФИКАЦИИ TON CITY BUILDER")
    print("=" * 80)
    print(f"🌐 Backend URL: {BASE_URL}")
    print(f"🗄️ База данных: {TEST_DATABASE}")
    print()
    
    tests = [
        test_1_register_email,
        test_2a_login_email,
        test_2b_login_username,
        test_3_update_username,
        test_4_update_email,
        test_5_update_password,
        test_6_link_wallet,
        test_7_upload_avatar,
        test_validation_errors,
        test_google_oauth_configuration
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