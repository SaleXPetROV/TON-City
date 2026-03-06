# TON City - PRD Document

## Session 4 Summary (Jan 2026)

### Completed Tasks:

1. **Testnet/Mainnet Switch Fixed**
   - Made `receiver_address` optional in `/admin/wallet-settings` POST
   - Now network can be changed without providing wallet address

2. **Credits Moved to Promos Tab**
   - Removed separate "Кредиты" tab
   - Added all credit management to "Promos" tab
   - Includes: promo creation, promo list, gov rate settings, telegram bot

3. **Full User ID in Credits**
   - Added full `borrower_id` (36-char UUID) display
   - Click-to-copy functionality with toast notification
   - Styled as monospace code block

### API Changes:
- `POST /api/admin/wallet-settings?network=mainnet` - network as query param, receiver_address optional

### Admin Tabs Now:
- TON Кошелек (with wallets for deposits)
- Доходы
- pendingWithdrawals
- users
- transactions
- Promos (now includes credits)
- announcements
- Данные
- Детали
- Налоги

### Test Credentials:
- admin@toncity.com / admin123

### Test Results:
- Backend: 90%
- Frontend: Working (verified via API tests)

### Previous Sessions:
- Session 1: Land listing fixes, React error fix, diamond avatars
- Session 2: Balance refresh, bulk withdrawal, 2FA, taxes
- Session 3: 2FA status, business financial model, wallet percentages
