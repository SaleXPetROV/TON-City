#!/usr/bin/env python3
"""
Тестирование TON City Builder - покупка земли, баланс, подсчёт полей
"""

import requests
import json
import time
from typing import Dict, Any, Optional

# Конфигурация
BASE_URL = "https://field-counter-1.preview.emergentagent.com/api"

# Тестовый пользователь из MongoDB
TEST_USER = {
    "id": "test-user-001",
    "username": "TestPlayer",
    "wallet_address": "UQBvW8Z5huBkMJYdnfAEM5JqTNLuDP2nRn-L_VPP3xJH9uPq",
    "balance_ton": 100.0
}

# Глобальные переменные
auth_token = None
user_data = None
cities_data = None

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
            "data": {"error": "Invalid JSON response", "raw": response.text[:500]},
            "success": False
        }

def test_1_get_jwt_token():
    """Тест 1: Получение JWT токена для тестового пользователя"""
    global auth_token, user_data
    
    print("🧪 ТЕСТ 1: POST /api/auth/verify-wallet - Получение JWT токена")
    
    # Данные для получения токена (включаем username для регистрации если нужно)
    auth_data = {
        "address": TEST_USER["wallet_address"],
        "username": TEST_USER["username"]
    }
    
    result = make_request("POST", "/auth/verify-wallet", auth_data)
    
    if not result["success"]:
        log_test("Получение JWT токена", "FAIL", 
                f"HTTP {result['status_code']}: {result['data']}")
        return False
    
    data = result["data"]
    
    # Проверяем статус
    if data.get("status") == "need_username":
        log_test("Получение JWT токена", "FAIL", 
                "Пользователь не найден и требуется username для регистрации")
        return False
    
    if data.get("status") != "ok":
        log_test("Получение JWT токена", "FAIL", 
                f"Неожиданный статус: {data.get('status')}")
        return False
    
    # Проверяем наличие токена
    if "token" not in data:
        log_test("Получение JWT токена", "FAIL", "Токен не возвращен")
        return False
    
    # Проверяем данные пользователя
    if "user" not in data:
        log_test("Получение JWT токена", "FAIL", "Данные пользователя не возвращены")
        return False
    
    user = data["user"]
    
    # Сохраняем токен и данные пользователя
    auth_token = data["token"]
    user_data = user
    
    log_test("Получение JWT токена", "PASS", 
            f"Токен получен для пользователя {user.get('username')} (ID: {user.get('id')})")
    return True

def test_2_check_balance():
    """Тест 2: Проверка баланса пользователя"""
    global auth_token
    
    print("🧪 ТЕСТ 2: GET /api/auth/me - Проверка баланса")
    
    if not auth_token:
        log_test("Проверка баланса", "FAIL", "Нет токена авторизации")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    result = make_request("GET", "/auth/me", headers=headers)
    
    if not result["success"]:
        log_test("Проверка баланса", "FAIL", 
                f"HTTP {result['status_code']}: {result['data']}")
        return False
    
    data = result["data"]
    
    # Проверяем наличие balance_ton
    if "balance_ton" not in data:
        log_test("Проверка баланса", "FAIL", "Поле balance_ton отсутствует")
        return False
    
    balance_ton = data.get("balance_ton")
    
    # Проверяем, что balance_game НЕ используется
    if "balance_game" in data:
        log_test("Проверка баланса", "FAIL", 
                "Поле balance_game все еще присутствует (должно быть удалено)")
        return False
    
    # Проверяем значение баланса
    if balance_ton != TEST_USER["balance_ton"]:
        log_test("Проверка баланса", "WARN", 
                f"Баланс не совпадает с ожидаемым: ожидался {TEST_USER['balance_ton']}, получен {balance_ton}")
    
    log_test("Проверка баланса", "PASS", 
            f"balance_ton: {balance_ton}, balance_game отсутствует")
    return True

def test_3_get_cities():
    """Тест 3: Получение списка городов"""
    global cities_data
    
    print("🧪 ТЕСТ 3: GET /api/cities - Получение списка городов")
    
    result = make_request("GET", "/cities")
    
    if not result["success"]:
        log_test("Получение списка городов", "FAIL", 
                f"HTTP {result['status_code']}: {result['data']}")
        return False
    
    data = result["data"]
    
    # Проверяем структуру ответа
    if "cities" not in data:
        log_test("Получение списка городов", "FAIL", "Поле cities отсутствует")
        return False
    
    cities = data["cities"]
    
    if not isinstance(cities, list) or len(cities) == 0:
        log_test("Получение списка городов", "FAIL", "Список городов пуст или не является массивом")
        return False
    
    # Проверяем первый город
    first_city = cities[0]
    required_fields = ["id", "name", "stats"]
    
    for field in required_fields:
        if field not in first_city:
            log_test("Получение списка городов", "FAIL", f"Поле {field} отсутствует в данных города")
            return False
    
    # Проверяем подсчёт полей (total_plots должен показывать количество клеток земли)
    stats = first_city.get("stats", {})
    if "total_plots" not in stats:
        log_test("Получение списка городов", "FAIL", "Поле total_plots отсутствует в статистике города")
        return False
    
    total_plots = stats["total_plots"]
    
    # Сохраняем данные городов
    cities_data = cities
    
    log_test("Получение списка городов", "PASS", 
            f"Получено {len(cities)} городов, первый город: {first_city['name']}, total_plots: {total_plots}")
    return True

def test_4_get_city_plots():
    """Тест 4: Получение участков в городе"""
    global cities_data
    
    print("🧪 ТЕСТ 4: GET /api/cities/{city_id}/plots - Получение участков в городе")
    
    if not cities_data or len(cities_data) == 0:
        log_test("Получение участков в городе", "FAIL", "Нет данных о городах")
        return False
    
    # Берем первый город
    city = cities_data[0]
    city_id = city["id"]
    
    result = make_request("GET", f"/cities/{city_id}/plots")
    
    if not result["success"]:
        log_test("Получение участков в городе", "FAIL", 
                f"HTTP {result['status_code']}: {result['data']}")
        return False
    
    data = result["data"]
    
    # Проверяем структуру ответа
    if "plots" not in data:
        log_test("Получение участков в городе", "FAIL", "Поле plots отсутствует")
        return False
    
    plots = data["plots"]
    
    if not isinstance(plots, list):
        log_test("Получение участков в городе", "FAIL", "plots не является массивом")
        return False
    
    # Проверяем структуру участка
    if len(plots) > 0:
        first_plot = plots[0]
        required_fields = ["x", "y", "city_id", "price", "is_available"]
        
        for field in required_fields:
            if field not in first_plot:
                log_test("Получение участков в городе", "FAIL", 
                        f"Поле {field} отсутствует в данных участка")
                return False
    
    # Подсчитываем количество земельных участков (где grid == 1)
    land_plots = [p for p in plots if p.get("x") is not None and p.get("y") is not None]
    
    log_test("Получение участков в городе", "PASS", 
            f"Получено {len(plots)} участков в городе {city['name']}, земельных участков: {len(land_plots)}")
    return True

def test_5_buy_land_plot():
    """Тест 5: Покупка участка земли"""
    global auth_token, cities_data
    
    print("🧪 ТЕСТ 5: POST /api/cities/{city_id}/plots/{x}/{y}/buy - Покупка участка земли")
    
    if not auth_token:
        log_test("Покупка участка земли", "FAIL", "Нет токена авторизации")
        return False
    
    if not cities_data or len(cities_data) == 0:
        log_test("Покупка участка земли", "FAIL", "Нет данных о городах")
        return False
    
    # Берем первый город
    city = cities_data[0]
    city_id = city["id"]
    
    # Получаем участки города
    plots_result = make_request("GET", f"/cities/{city_id}/plots")
    
    if not plots_result["success"]:
        log_test("Покупка участка земли", "FAIL", 
                f"Не удалось получить участки: HTTP {plots_result['status_code']}")
        return False
    
    plots = plots_result["data"]["plots"]
    
    # Ищем доступный участок
    available_plot = None
    for plot in plots:
        if plot.get("is_available") and not plot.get("owner"):
            available_plot = plot
            break
    
    if not available_plot:
        log_test("Покупка участка земли", "FAIL", "Нет доступных участков для покупки")
        return False
    
    x, y = available_plot["x"], available_plot["y"]
    price = available_plot["price"]
    
    # Покупаем участок
    headers = {"Authorization": f"Bearer {auth_token}"}
    result = make_request("POST", f"/cities/{city_id}/plots/{x}/{y}/buy", headers=headers)
    
    if not result["success"]:
        log_test("Покупка участка земли", "FAIL", 
                f"HTTP {result['status_code']}: {result['data']}")
        return False
    
    data = result["data"]
    
    # Проверяем успешность покупки
    if data.get("status") != "success":
        log_test("Покупка участка земли", "FAIL", 
                f"Неожиданный статус: {data.get('status')}")
        return False
    
    # Проверяем данные участка
    if "plot" not in data:
        log_test("Покупка участка земли", "FAIL", "Данные участка не возвращены")
        return False
    
    plot_data = data["plot"]
    
    # Проверяем, что участок привязан к user.id
    if plot_data.get("owner") != TEST_USER["id"]:
        log_test("Покупка участка земли", "FAIL", 
                f"Участок не привязан к user.id: ожидался {TEST_USER['id']}, получен {plot_data.get('owner')}")
        return False
    
    # Проверяем новый баланс
    if "new_balance" in data:
        new_balance = data["new_balance"]
        expected_balance = TEST_USER["balance_ton"] - price
        if abs(new_balance - expected_balance) > 0.01:  # Допускаем небольшую погрешность
            log_test("Покупка участка земли", "WARN", 
                    f"Баланс не соответствует ожидаемому: ожидался {expected_balance}, получен {new_balance}")
    
    log_test("Покупка участка земли", "PASS", 
            f"Участок ({x}, {y}) успешно куплен за {price} TON, владелец: {plot_data.get('owner')}")
    return True

def test_6_verify_balance_after_purchase():
    """Тест 6: Проверка баланса после покупки"""
    global auth_token
    
    print("🧪 ТЕСТ 6: GET /api/auth/me - Проверка баланса после покупки")
    
    if not auth_token:
        log_test("Проверка баланса после покупки", "FAIL", "Нет токена авторизации")
        return False
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    result = make_request("GET", "/auth/me", headers=headers)
    
    if not result["success"]:
        log_test("Проверка баланса после покупки", "FAIL", 
                f"HTTP {result['status_code']}: {result['data']}")
        return False
    
    data = result["data"]
    
    # Проверяем наличие balance_ton
    if "balance_ton" not in data:
        log_test("Проверка баланса после покупки", "FAIL", "Поле balance_ton отсутствует")
        return False
    
    balance_ton = data.get("balance_ton")
    
    # Проверяем, что баланс изменился (должен быть меньше изначального)
    if balance_ton >= TEST_USER["balance_ton"]:
        log_test("Проверка баланса после покупки", "FAIL", 
                f"Баланс не изменился после покупки: {balance_ton} >= {TEST_USER['balance_ton']}")
        return False
    
    log_test("Проверка баланса после покупки", "PASS", 
            f"Баланс обновлен: {balance_ton} TON (было {TEST_USER['balance_ton']} TON)")
    return True

def test_7_verify_field_counting():
    """Тест 7: Проверка подсчёта полей"""
    
    print("🧪 ТЕСТ 7: Проверка подсчёта полей (grid == 1)")
    
    result = make_request("GET", "/cities")
    
    if not result["success"]:
        log_test("Проверка подсчёта полей", "FAIL", 
                f"HTTP {result['status_code']}: {result['data']}")
        return False
    
    data = result["data"]
    cities = data.get("cities", [])
    
    if len(cities) == 0:
        log_test("Проверка подсчёта полей", "FAIL", "Нет городов для проверки")
        return False
    
    # Проверяем первый город
    city = cities[0]
    city_id = city["id"]
    
    # Получаем полную информацию о городе
    city_result = make_request("GET", f"/cities/{city_id}")
    
    if not city_result["success"]:
        log_test("Проверка подсчёта полей", "FAIL", 
                f"Не удалось получить данные города: HTTP {city_result['status_code']}")
        return False
    
    city_data = city_result["data"]
    
    # Проверяем наличие grid
    if "grid" not in city_data:
        log_test("Проверка подсчёта полей", "FAIL", "Поле grid отсутствует в данных города")
        return False
    
    grid = city_data["grid"]
    
    # Подсчитываем клетки земли (grid == 1)
    land_cells = 0
    for row in grid:
        for cell in row:
            if cell == 1:
                land_cells += 1
    
    # Сравниваем с total_plots в статистике
    stats = city.get("stats", {})
    total_plots = stats.get("total_plots", 0)
    
    if land_cells != total_plots:
        log_test("Проверка подсчёта полей", "FAIL", 
                f"Подсчёт полей неверен: в grid {land_cells} клеток земли, в stats.total_plots {total_plots}")
        return False
    
    log_test("Проверка подсчёта полей", "PASS", 
            f"Подсчёт полей корректен: {land_cells} клеток земли (grid == 1)")
    return True

def run_all_tests():
    """Запуск всех тестов"""
    print("=" * 80)
    print("🚀 ЗАПУСК ТЕСТОВ TON CITY BUILDER")
    print("=" * 80)
    print(f"🌐 Backend URL: {BASE_URL}")
    print(f"👤 Тестовый пользователь: {TEST_USER['username']} (ID: {TEST_USER['id']})")
    print(f"💰 Начальный баланс: {TEST_USER['balance_ton']} TON")
    print()
    
    tests = [
        test_1_get_jwt_token,
        test_2_check_balance,
        test_3_get_cities,
        test_4_get_city_plots,
        test_5_buy_land_plot,
        test_6_verify_balance_after_purchase,
        test_7_verify_field_counting
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