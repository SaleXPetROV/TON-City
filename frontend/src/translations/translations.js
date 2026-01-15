// Централизованная система переводов для TON City

export const translations = {
  // Общие
  common: {
    loading: { en: 'Loading...', ru: 'Загрузка...', zh: '加载中...' },
    error: { en: 'Error', ru: 'Ошибка', zh: '错误' },
    success: { en: 'Success', ru: 'Успешно', zh: '成功' },
    cancel: { en: 'Cancel', ru: 'Отмена', zh: '取消' },
    confirm: { en: 'Confirm', ru: 'Подтвердить', zh: '确认' },
    close: { en: 'Close', ru: 'Закрыть', zh: '关闭' },
    save: { en: 'Save', ru: 'Сохранить', zh: '保存' },
    delete: { en: 'Delete', ru: 'Удалить', zh: '删除' },
    edit: { en: 'Edit', ru: 'Редактировать', zh: '编辑' },
    back: { en: 'Back', ru: 'Назад', zh: '返回' },
    next: { en: 'Next', ru: 'Далее', zh: '下一步' },
    previous: { en: 'Previous', ru: 'Назад', zh: '上一步' },
  },

  // Навигация
  nav: {
    home: { en: 'Home', ru: 'Главная', zh: '主页' },
    game: { en: 'Game', ru: 'Игра', zh: '游戏' },
    trading: { en: 'Trading', ru: 'Торговля', zh: '交易' },
    dashboard: { en: 'Dashboard', ru: 'Панель', zh: '仪表板' },
    admin: { en: 'Admin', ru: 'Админ', zh: '管理员' },
    leaderboard: { en: 'Leaderboard', ru: 'Лидеры', zh: '排行榜' },
  },

  // Баланс
  balance: {
    title: { en: 'Balance', ru: 'Баланс', zh: '余额' },
    deposit: { en: 'Deposit', ru: 'Пополнить', zh: '充值' },
    withdraw: { en: 'Withdraw', ru: 'Вывести', zh: '提款' },
    game_balance: { en: 'Game Balance', ru: 'Игровой баланс', zh: '游戏余额' },
    available: { en: 'Available', ru: 'Доступно', zh: '可用' },
    insufficient: { en: 'Insufficient funds', ru: 'Недостаточно средств', zh: '余额不足' },
  },

  // Участки
  plots: {
    title: { en: 'Plots', ru: 'Участки', zh: '地块' },
    available: { en: 'Available Plots', ru: 'Доступные участки', zh: '可用地块' },
    owned: { en: 'Owned', ru: 'Куплено', zh: '已拥有' },
    buy: { en: 'Buy Plot', ru: 'Купить участок', zh: '购买地块' },
    sell: { en: 'Sell Plot', ru: 'Продать участок', zh: '出售地块' },
    price: { en: 'Price', ru: 'Цена', zh: '价格' },
    coordinates: { en: 'Coordinates', ru: 'Координаты', zh: '坐标' },
    zone: { en: 'Zone', ru: 'Зона', zh: '区域' },
    select_plot: { en: 'Select a plot for purchase', ru: 'Выберите участок для покупки', zh: '选择要购买的地块' },
  },

  // Зоны
  zones: {
    title: { en: 'Zones', ru: 'Зоны', zh: '区域' },
    center: { en: 'Center', ru: 'Центр', zh: '中心' },
    business: { en: 'Business', ru: 'Бизнес', zh: '商业区' },
    residential: { en: 'Residential', ru: 'Жилая', zh: '住宅区' },
    industrial: { en: 'Industrial', ru: 'Промышл.', zh: '工业区' },
    outskirts: { en: 'Outskirts', ru: 'Окраина', zh: '郊区' },
  },

  // Бизнесы
  businesses: {
    title: { en: 'Businesses', ru: 'Бизнесы', zh: '企业' },
    build: { en: 'Build Business', ru: 'Построить бизнес', zh: '建造企业' },
    upgrade: { en: 'Upgrade', ru: 'Улучшить', zh: '升级' },
    level: { en: 'Level', ru: 'Уровень', zh: '等级' },
    income: { en: 'Income', ru: 'Доход', zh: '收入' },
    cost: { en: 'Cost', ru: 'Стоимость', zh: '成本' },
    daily_income: { en: 'Daily Income', ru: 'Ежедневный доход', zh: '每日收入' },
    select_type: { en: 'Select business type', ru: 'Выберите тип бизнеса', zh: '选择企业类型' },
  },

  // Типы бизнесов
  business_types: {
    farm: { en: 'Farm', ru: 'Ферма', zh: '农场' },
    factory: { en: 'Factory', ru: 'Завод', zh: '工厂' },
    shop: { en: 'Shop', ru: 'Магазин', zh: '商店' },
    bank: { en: 'Bank', ru: 'Банк', zh: '银行' },
    tech_hub: { en: 'Tech Hub', ru: 'Тех центр', zh: '科技中心' },
    restaurant: { en: 'Restaurant', ru: 'Ресторан', zh: '餐厅' },
  },

  // Торговля
  trading: {
    title: { en: 'Trading', ru: 'Торговля', zh: '交易' },
    create_offer: { en: 'Create Offer', ru: 'Создать предложение', zh: '创建报价' },
    buy: { en: 'Buy', ru: 'Купить', zh: '购买' },
    sell: { en: 'Sell', ru: 'Продать', zh: '出售' },
    quantity: { en: 'Quantity', ru: 'Количество', zh: '数量' },
    price_per_unit: { en: 'Price per unit', ru: 'Цена за единицу', zh: '单价' },
    total: { en: 'Total', ru: 'Итого', zh: '总计' },
    commission: { en: 'Commission', ru: 'Комиссия', zh: '佣金' },
    my_offers: { en: 'My Offers', ru: 'Мои предложения', zh: '我的报价' },
    market: { en: 'Market', ru: 'Рынок', zh: '市场' },
  },

  // Админ панель
  admin: {
    title: { en: 'Admin Panel', ru: 'Админ панель', zh: '管理面板' },
    users: { en: 'Users', ru: 'Пользователи', zh: '用户' },
    deposits: { en: 'Deposits', ru: 'Депозиты', zh: '充值' },
    withdrawals: { en: 'Withdrawals', ru: 'Выводы', zh: '提款' },
    settings: { en: 'Settings', ru: 'Настройки', zh: '设置' },
    wallet_settings: { en: 'Wallet Settings', ru: 'Настройки кошелька', zh: '钱包设置' },
    approve: { en: 'Approve', ru: 'Одобрить', zh: '批准' },
    reject: { en: 'Reject', ru: 'Отклонить', zh: '拒绝' },
    pending: { en: 'Pending', ru: 'В ожидании', zh: '待处理' },
    approved: { en: 'Approved', ru: 'Одобрено', zh: '已批准' },
    rejected: { en: 'Rejected', ru: 'Отклонено', zh: '已拒绝' },
  },

  // Модалки
  modals: {
    deposit_title: { en: 'Deposit TON', ru: 'Пополнить баланс', zh: '充值TON' },
    withdraw_title: { en: 'Withdraw TON', ru: 'Вывести средства', zh: '提取TON' },
    purchase_title: { en: 'Purchase Plot', ru: 'Покупка участка', zh: '购买地块' },
    build_title: { en: 'Build Business', ru: 'Построить бизнес', zh: '建造企业' },
    amount: { en: 'Amount', ru: 'Сумма', zh: '金额' },
    enter_amount: { en: 'Enter amount', ru: 'Введите сумму', zh: '输入金额' },
    min_amount: { en: 'Minimum', ru: 'Минимум', zh: '最小值' },
    max_amount: { en: 'Maximum', ru: 'Максимум', zh: '最大值' },
  },

  // Сообщения
  messages: {
    connect_wallet: { en: 'Connect Wallet', ru: 'Подключить кошелёк', zh: '连接钱包' },
    wallet_connected: { en: 'Wallet connected', ru: 'Кошелёк подключён', zh: '钱包已连接' },
    transaction_success: { en: 'Transaction successful', ru: 'Транзакция успешна', zh: '交易成功' },
    transaction_failed: { en: 'Transaction failed', ru: 'Транзакция не удалась', zh: '交易失败' },
    plot_purchased: { en: 'Plot purchased!', ru: 'Участок куплен!', zh: '地块已购买!' },
    business_built: { en: 'Business built!', ru: 'Бизнес построен!', zh: '企业已建造!' },
    insufficient_balance: { en: 'Insufficient balance', ru: 'Недостаточно средств', zh: '余额不足' },
    plot_not_available: { en: 'Plot not available', ru: 'Участок недоступен', zh: '地块不可用' },
    admin_only: { en: 'Admin access only', ru: 'Только для админов', zh: '仅限管理员' },
  },

  // Лендинг
  landing: {
    title: { en: 'TON City Builder', ru: 'TON City Builder', zh: 'TON城市建造者' },
    subtitle: { en: 'Build, Trade, Earn on TON Blockchain', ru: 'Строй, торгуй, зарабатывай на блокчейне TON', zh: '在TON区块链上建造、交易、赚钱' },
    play_now: { en: 'Play Now', ru: 'Играть сейчас', zh: '立即游戏' },
    learn_more: { en: 'Learn More', ru: 'Узнать больше', zh: '了解更多' },
    features_title: { en: 'Features', ru: 'Возможности', zh: '特点' },
    how_to_play: { en: 'How to Play', ru: 'Как играть', zh: '如何游戏' },
  },

  // Статистика
  stats: {
    total_players: { en: 'Total Players', ru: 'Всего игроков', zh: '总玩家数' },
    total_plots: { en: 'Total Plots', ru: 'Всего участков', zh: '总地块数' },
    total_businesses: { en: 'Total Businesses', ru: 'Всего бизнесов', zh: '总企业数' },
    total_trades: { en: 'Total Trades', ru: 'Всего сделок', zh: '总交易数' },
    total_volume: { en: 'Total Volume', ru: 'Общий объём', zh: '总交易量' },
  },

  // Лидеры
  leaderboard: {
    title: { en: 'Leaderboard', ru: 'Таблица лидеров', zh: '排行榜' },
    rank: { en: 'Rank', ru: 'Место', zh: '排名' },
    player: { en: 'Player', ru: 'Игрок', zh: '玩家' },
    net_worth: { en: 'Net Worth', ru: 'Капитал', zh: '净值' },
    plots: { en: 'Plots', ru: 'Участков', zh: '地块' },
    businesses: { en: 'Businesses', ru: 'Бизнесов', zh: '企业' },
  },

  // Время
  time: {
    day: { en: 'day', ru: 'день', zh: '天' },
    days: { en: 'days', ru: 'дней', zh: '天' },
    hour: { en: 'hour', ru: 'час', zh: '小时' },
    hours: { en: 'hours', ru: 'часов', zh: '小时' },
    minute: { en: 'minute', ru: 'минута', zh: '分钟' },
    minutes: { en: 'minutes', ru: 'минут', zh: '分钟' },
    ago: { en: 'ago', ru: 'назад', zh: '前' },
  },
};

// Хелпер для получения перевода
export const t = (path, lang = 'en') => {
  const keys = path.split('.');
  let value = translations;
  
  for (const key of keys) {
    value = value[key];
    if (!value) return path;
  }
  
  return value[lang] || value['en'] || path;
};
