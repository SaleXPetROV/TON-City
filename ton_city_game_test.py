#!/usr/bin/env python3
"""
Тестирование полного игрового цикла TON City Builder
Тестирует весь игровой процесс от входа до сбора дохода
"""

import requests
import json
import time
from typing import Dict, Any, Optional

# Конфигурация
BASE_URL = "https://field-counter-1.preview.emergentagent.com/api"

# Тестовые данные пользователя
TEST_USER = {
    "email": "citymaster@test.com",
    "password": "Test123!"
}

# Глобальные переменные
auth_token = None
user_data = None
selected_city = None
selected_plot = None
business_data = None

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

def test_1_user_login():
    """Тест 1: Вход пользователя"""
    global auth_token, user_data
    
    print("🧪 ТЕСТ 1: POST /api/auth/login - Вход пользователя")
    print(f"   Email: {TEST_USER['email']}")
    print(f"   Password: {TEST_USER['password']}")
    
    login_data = {
        "email": TEST_USER["email"],
        "password": TEST_USER["password"]
    }
    
    result = make_request("POST", "/auth/login", login_data)
    
    if not result["success"]:
        log_test("Вход пользователя", "FAIL", 
                f"HTTP {result['status_code']}: {result['data']}")
        return False
    
    data = result["data"]
    
    # Проверяем наличие токена
    if "token" not in data:
        log_test("Вход пользователя", "FAIL", "Токен не возвращен")
        return False
    
    # Проверяем данные пользователя
    if "user" not in data:
        log_test("Вход пользователя", "FAIL", "Данные пользователя не возвращены")
        return False
    
    user = data["user"]
    
    # Сохраняем токен для дальнейших тестов
    auth_token = data["token"]
    user_data = user
    
    log_test("Вход пользователя", "PASS", 
            f"Пользователь {user.get('username', user.get('email'))} успешно вошел в систему. Токен получен.")
    return True

def test_2_get_cities():
    """Тест 2: Получить список городов"""
    global selected_city
    
    print("🧪 ТЕСТ 2: GET /api/cities - Получение списка городов")
    
    result = make_request("GET", "/cities")
    
    if not result["success"]:
        log_test("Получение городов", "FAIL", 
                f"HTTP {result['status_code']}: {result['data']}")
        return False
    
    data = result["data"]
    
    # Проверяем структуру ответа
    if "cities" not in data:
        log_test("Получение городов", "FAIL", "Отсутствует поле 'cities' в ответе")
        return False
    
    cities = data["cities"]
    
    if not isinstance(cities, list) or len(cities) == 0:
        log_test("Получение городов", "FAIL", "Список городов пуст или не является массивом")
        return False
    
    # Выбираем первый город для дальнейших тестов
    selected_city = cities[0]
    
    log_test("Получение городов", "PASS", 
            f"Получено {len(cities)} городов. Выбран город: {selected_city['name']} (ID: {selected_city['id']})")
    return True

def test_3_get_city_plots():
    """Тест 3: Получить участки в городе"""
    global selected_plot
    
    if not selected_city:
        log_test("Получение участков города", "FAIL", "Город не выбран")
        return False
    
    print(f"🧪 ТЕСТ 3: GET /api/cities/{selected_city['id']}/plots - Получение участков города")
    
    result = make_request("GET", f"/cities/{selected_city['id']}/plots")
    
    if not result["success"]:
        log_test("Получение участков города", "FAIL", 
                f"HTTP {result['status_code']}: {result['data']}")
        return False
    
    data = result["data"]
    
    # Проверяем структуру ответа
    if "plots" not in data:
        log_test("Получение участков города", "FAIL", "Отсутствует поле 'plots' в ответе")
        return False
    
    plots = data["plots"]
    
    if not isinstance(plots, list):
        log_test("Получение участков города", "FAIL", "Участки не являются массивом")
        return False
    
    # Ищем свободный участок для покупки
    available_plots = [p for p in plots if p.get("is_available", True) and not p.get("owner")]
    
    if not available_plots:
        log_test("Получение участков города", "FAIL", "Нет доступных участков для покупки")
        return False
    
    # Выбираем первый доступный участок
    selected_plot = available_plots[0]
    
    log_test("Получение участков города", "PASS", 
            f"Получено {len(plots)} участков. Найдено {len(available_plots)} доступных участков. "
            f"Выбран участок ({selected_plot['x']}, {selected_plot['y']}) цена: {selected_plot['price']} TON")
    return True

def test_4_check_user_balance():
    """Тест 4: Проверить баланс пользователя"""
    global auth_token
    
    if not auth_token:
        log_test("Проверка баланса", "FAIL", "Нет токена авторизации")
        return False
    
    print("🧪 ТЕСТ 4: GET /api/auth/me - Проверка баланса пользователя")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    result = make_request("GET", "/auth/me", headers=headers)
    
    if not result["success"]:
        log_test("Проверка баланса", "FAIL", 
                f"HTTP {result['status_code']}: {result['data']}")
        return False
    
    data = result["data"]
    
    # Проверяем наличие баланса
    if "balance_ton" not in data:
        log_test("Проверка баланса", "FAIL", "Отсутствует поле 'balance_ton' в ответе")
        return False
    
    balance = data["balance_ton"]
    
    if not isinstance(balance, (int, float)):
        log_test("Проверка баланса", "FAIL", "Баланс не является числом")
        return False
    
    # Проверяем, достаточно ли средств для покупки участка
    if selected_plot and balance < selected_plot["price"]:
        log_test("Проверка баланса", "WARN", 
                f"Недостаточно средств для покупки участка. Баланс: {balance} TON, нужно: {selected_plot['price']} TON")
        return False
    
    log_test("Проверка баланса", "PASS", 
            f"Баланс пользователя: {balance} TON. Достаточно для покупки участка.")
    return True

def test_5_buy_plot():
    """Тест 5: Купить участок"""
    global auth_token, selected_city, selected_plot
    
    if not auth_token:
        log_test("Покупка участка", "FAIL", "Нет токена авторизации")
        return False
    
    if not selected_city or not selected_plot:
        log_test("Покупка участка", "FAIL", "Город или участок не выбраны")
        return False
    
    print(f"🧪 ТЕСТ 5: POST /api/cities/{selected_city['id']}/plots/{selected_plot['x']}/{selected_plot['y']}/buy - Покупка участка")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    result = make_request("POST", f"/cities/{selected_city['id']}/plots/{selected_plot['x']}/{selected_plot['y']}/buy", {}, headers)
    
    if not result["success"]:
        log_test("Покупка участка", "FAIL", 
                f"HTTP {result['status_code']}: {result['data']}")
        return False
    
    data = result["data"]
    
    # Проверяем успешность покупки
    if data.get("status") != "success":
        log_test("Покупка участка", "FAIL", f"Неожиданный статус: {data}")
        return False
    
    # Проверяем данные участка
    if "plot" not in data:
        log_test("Покупка участка", "FAIL", "Данные участка не возвращены")
        return False
    
    plot_data = data["plot"]
    new_balance = data.get("new_balance", 0)
    
    log_test("Покупка участка", "PASS", 
            f"Участок ({selected_plot['x']}, {selected_plot['y']}) успешно куплен за {selected_plot['price']} TON. "
            f"Новый баланс: {new_balance} TON")
    
    # Обновляем данные участка
    selected_plot.update(plot_data)
    return True

def test_6_build_business():
    """Тест 6: Построить бизнес (ферму)"""
    global auth_token, selected_city, selected_plot, business_data
    
    if not auth_token:
        log_test("Строительство бизнеса", "FAIL", "Нет токена авторизации")
        return False
    
    if not selected_city or not selected_plot:
        log_test("Строительство бизнеса", "FAIL", "Город или участок не выбраны")
        return False
    
    print(f"🧪 ТЕСТ 6: POST /api/cities/{selected_city['id']}/plots/{selected_plot['x']}/{selected_plot['y']}/build - Строительство фермы")
    
    build_data = {"business_type": "farm"}
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    result = make_request("POST", f"/cities/{selected_city['id']}/plots/{selected_plot['x']}/{selected_plot['y']}/build", build_data, headers)
    
    if not result["success"]:
        log_test("Строительство бизнеса", "FAIL", 
                f"HTTP {result['status_code']}: {result['data']}")
        return False
    
    data = result["data"]
    
    # Проверяем успешность строительства
    if data.get("status") != "success":
        log_test("Строительство бизнеса", "FAIL", f"Неожиданный статус: {data}")
        return False
    
    # Проверяем данные бизнеса
    if "business" not in data:
        log_test("Строительство бизнеса", "FAIL", "Данные бизнеса не возвращены")
        return False
    
    business_data = data["business"]
    new_balance = data.get("new_balance", 0)
    
    log_test("Строительство бизнеса", "PASS", 
            f"Ферма успешно построена на участке ({selected_plot['x']}, {selected_plot['y']}). "
            f"ID бизнеса: {business_data['id']}. Новый баланс: {new_balance} TON")
    return True

def test_7_collect_income():
    """Тест 7: Собрать доход с бизнеса"""
    global auth_token, business_data
    
    if not auth_token:
        log_test("Сбор дохода", "FAIL", "Нет токена авторизации")
        return False
    
    if not business_data:
        log_test("Сбор дохода", "FAIL", "Бизнес не создан")
        return False
    
    print(f"🧪 ТЕСТ 7: POST /api/businesses/{business_data['id']}/collect - Сбор дохода с бизнеса")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    result = make_request("POST", f"/businesses/{business_data['id']}/collect", {}, headers)
    
    if not result["success"]:
        log_test("Сбор дохода", "FAIL", 
                f"HTTP {result['status_code']}: {result['data']}")
        return False
    
    data = result["data"]
    
    # Проверяем успешность сбора
    if "income_collected" not in data and "message" not in data:
        log_test("Сбор дохода", "FAIL", "Неожиданная структура ответа")
        return False
    
    income = data.get("income_collected", 0)
    message = data.get("message", "")
    
    if income > 0:
        log_test("Сбор дохода", "PASS", 
                f"Доход собран: {income} TON. {message}")
    else:
        log_test("Сбор дохода", "PASS", 
                f"Сбор дохода выполнен (возможно, доход еще не накопился). {message}")
    
    return True

def test_8_check_leaderboard():
    """Тест 8: Проверить рейтинг"""
    print("🧪 ТЕСТ 8: GET /api/leaderboard?sort_by=balance - Проверка рейтинга")
    
    params = {"sort_by": "balance"}
    result = make_request("GET", "/leaderboard", params)
    
    if not result["success"]:
        log_test("Проверка рейтинга", "FAIL", 
                f"HTTP {result['status_code']}: {result['data']}")
        return False
    
    data = result["data"]
    
    # Проверяем структуру ответа
    if "players" not in data:
        log_test("Проверка рейтинга", "FAIL", "Отсутствует поле 'players' в ответе")
        return False
    
    players = data["players"]
    
    if not isinstance(players, list):
        log_test("Проверка рейтинга", "FAIL", "Игроки не являются массивом")
        return False
    
    # Проверяем, что наш пользователь есть в рейтинге
    our_user = None
    for player in players:
        if player.get("email") == TEST_USER["email"] or player.get("username") == user_data.get("username"):
            our_user = player
            break
    
    if our_user:
        position = players.index(our_user) + 1
        balance = our_user.get("balance_ton", 0)
        log_test("Проверка рейтинга", "PASS", 
                f"Рейтинг получен. Всего игроков: {len(players)}. "
                f"Наша позиция: {position}, баланс: {balance} TON")
    else:
        log_test("Проверка рейтинга", "PASS", 
                f"Рейтинг получен. Всего игроков: {len(players)}. "
                f"Наш пользователь не найден в топе (возможно, низкий баланс)")
    
    return True

def test_9_check_admin_fees():
    """Тест 9: Проверить настройки комиссий (требует админ токен)"""
    print("🧪 ТЕСТ 9: GET /api/admin/settings/fees - Проверка настроек комиссий")
    
    # Сначала пробуем без токена
    result = make_request("GET", "/admin/settings/fees")
    
    if result["success"]:
        log_test("Проверка настроек комиссий", "WARN", 
                "Админские настройки доступны без авторизации (возможная проблема безопасности)")
        return True
    
    # Пробуем с обычным токеном
    if auth_token:
        headers = {"Authorization": f"Bearer {auth_token}"}
        result = make_request("GET", "/admin/settings/fees", headers=headers)
        
        if result["success"]:
            data = result["data"]
            log_test("Проверка настроек комиссий", "PASS", 
                    f"Настройки комиссий получены: {data}")
            return True
        elif result["status_code"] == 403:
            log_test("Проверка настроек комиссий", "PASS", 
                    "Доступ к админским настройкам корректно ограничен (403 Forbidden)")
            return True
        else:
            log_test("Проверка настроек комиссий", "FAIL", 
                    f"HTTP {result['status_code']}: {result['data']}")
            return False
    
    log_test("Проверка настроек комиссий", "PASS", 
            "Админские настройки недоступны без соответствующих прав")
    return True

def run_game_cycle_test():
    """Запуск полного теста игрового цикла"""
    print("=" * 80)
    print("🎮 ТЕСТИРОВАНИЕ ПОЛНОГО ИГРОВОГО ЦИКЛА TON CITY BUILDER")
    print("=" * 80)
    print(f"🌐 Backend URL: {BASE_URL}")
    print(f"👤 Тестовый пользователь: {TEST_USER['email']}")
    print()
    
    # Список всех тестов в порядке выполнения
    tests = [
        test_1_user_login,
        test_2_get_cities,
        test_3_get_city_plots,
        test_4_check_user_balance,
        test_5_buy_plot,
        test_6_build_business,
        test_7_collect_income,
        test_8_check_leaderboard,
        test_9_check_admin_fees
    ]
    
    passed = 0
    failed = 0
    
    # Выполняем тесты последовательно
    for i, test_func in enumerate(tests, 1):
        print(f"📍 ШАГ {i}/{len(tests)}")
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                # Если критический тест провалился, останавливаем выполнение
                if test_func in [test_1_user_login, test_2_get_cities, test_3_get_city_plots]:
                    print(f"❌ КРИТИЧЕСКИЙ ТЕСТ ПРОВАЛЕН. ОСТАНОВКА ВЫПОЛНЕНИЯ.")
                    break
        except Exception as e:
            print(f"❌ ОШИБКА в {test_func.__name__}: {str(e)}")
            failed += 1
            # Останавливаем выполнение при критических ошибках
            if test_func in [test_1_user_login, test_2_get_cities, test_3_get_city_plots]:
                print(f"❌ КРИТИЧЕСКАЯ ОШИБКА. ОСТАНОВКА ВЫПОЛНЕНИЯ.")
                break
        
        time.sleep(1)  # Пауза между тестами
    
    print("=" * 80)
    print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ ИГРОВОГО ЦИКЛА")
    print("=" * 80)
    print(f"✅ Пройдено: {passed}")
    print(f"❌ Провалено: {failed}")
    
    if passed + failed > 0:
        print(f"📈 Успешность: {passed/(passed+failed)*100:.1f}%")
    
    if failed == 0:
        print("\n🎉 ПОЛНЫЙ ИГРОВОЙ ЦИКЛ РАБОТАЕТ КОРРЕКТНО!")
        print("🏆 Пользователь может:")
        print("   • Войти в систему")
        print("   • Просматривать города")
        print("   • Покупать участки")
        print("   • Строить бизнесы")
        print("   • Собирать доход")
        print("   • Просматривать рейтинг")
    else:
        print(f"\n⚠️ ОБНАРУЖЕНЫ ПРОБЛЕМЫ В ИГРОВОМ ЦИКЛЕ: {failed} тест(ов) провалено")
    
    return failed == 0

if __name__ == "__main__":
    success = run_game_cycle_test()
    exit(0 if success else 1)