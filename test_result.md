#====================================================================================================
# START - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================
# (Protocol content preserved from original)
#====================================================================================================
# END - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================

#====================================================================================================
# Testing Data
#====================================================================================================

user_problem_statement: |
  Расширение системы аутентификации TON City Builder:
  1. Регистрация: Email + password + username (✓ есть)
  2. Авторизация: Email/username + password (нужно добавить вход через username)
  3. Регистрация через TonConnect (проверить работоспособность)
  4. Регистрация через Google OAuth (добавить с .env конфигурацией)
  5. После авторизации: кнопка с аватаром+никнеймом вместо "Вход/Регистрация"
  6. Sidebar: всегда открыт на главной, при наведении на других страницах
  7. На /game: убрать кнопку домой, сместить логотип влево, добавить sidebar
  8. Настройки пользователя: смена ника, привязка кошелька, смена почты/пароля, загрузка аватара
  9. Аватары: генерация по инициалам + возможность загрузки

backend:
  - task: "Разрешение Git конфликтов"
    implemented: true
    working: true
    file: "server.py, payment_monitor.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
      - working: true
        agent: "main"
        comment: "Git conflicts resolved, backend starting successfully, health check OK"

  - task: "Вход через Email/Username + password"
    implemented: false
    working: "NA"
    file: "auth_handler.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
      - working: "NA"
        agent: "main"
        comment: "TODO: Modify /auth/login endpoint to accept email OR username"

  - task: "Google OAuth интеграция"
    implemented: false
    working: "NA"
    file: "auth_handler.py, server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
      - working: "NA"
        agent: "main"
        comment: "TODO: Add Google OAuth with env variables (GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET)"

  - task: "Генерация и загрузка аватаров"
    implemented: false
    working: "NA"
    file: "server.py, auth_handler.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
      - working: "NA"
        agent: "main"
        comment: "TODO: Avatar generation from initials + upload endpoint"

  - task: "Настройки пользователя API"
    implemented: false
    working: "NA"
    file: "server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
      - working: "NA"
        agent: "main"
        comment: "TODO: Endpoints for changing username, email, password, linking wallet"

frontend:
  - task: "AuthPage с Username/Email входом"
    implemented: false
    working: "NA"
    file: "pages/AuthPage.jsx"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
      - working: "NA"
        agent: "main"
        comment: "TODO: Update login form to accept email OR username"

  - task: "Google OAuth кнопка"
    implemented: false
    working: "NA"
    file: "pages/AuthPage.jsx"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
      - working: "NA"
        agent: "main"
        comment: "TODO: Add Google Sign In button"

  - task: "Кнопка аватар+никнейм"
    implemented: false
    working: "NA"
    file: "pages/LandingPage.jsx, App.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
      - working: "NA"
        agent: "main"
        comment: "TODO: Replace login/register buttons with avatar+username button when authenticated"

  - task: "Адаптивный Sidebar"
    implemented: false
    working: "NA"
    file: "components/Sidebar.jsx"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
      - working: "NA"
        agent: "main"
        comment: "TODO: Always open on home, hover-to-open on other pages"

  - task: "Страница настроек пользователя"
    implemented: false
    working: "NA"
    file: "pages/SettingsPage.jsx"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
      - working: "NA"
        agent: "main"
        comment: "TODO: Settings page with username, email, password, wallet, avatar options"

metadata:
  created_by: "main_agent"
  version: "1.0"
  test_sequence: 0
  run_ui: false

test_plan:
  current_focus:
    - "Backend: Вход через Email/Username"
    - "Backend: Google OAuth"
    - "Backend: Avatar system"
  stuck_tasks: []
  test_all: false
  test_priority: "sequential"

agent_communication:
  - agent: "main"
    message: "Phase 0 COMPLETE: Git conflicts resolved, services running. Starting Phase 1: Backend authentication expansion."
