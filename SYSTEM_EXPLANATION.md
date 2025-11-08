# Expenzo System Explanation

## Add Income/Expense/Card System कैसे काम करता है

### 1. **Add Card System** 💳

**कहाँ है:** `/cards` page पर

**कैसे काम करता है:**
1. User "Add Card" button click करता है
2. Form open होता है जिसमें:
   - Cardholder Name
   - Card Number
   - Expiry Month (MM)
   - Expiry Year (YYYY)
   - Brand (Visa/Mastercard/RuPay/etc.)
3. Form submit करने पर:
   - JavaScript form data collect करता है
   - `/api/cards` endpoint पर POST request भेजता है
   - Backend card number को mask करता है (last 4 digits only store)
   - Database में card save होता है
   - Success message दिखता है
   - Page reload होकर नया card दिखता है

**API Endpoint:** `POST /api/cards`
**Data Format:**
```json
{
  "cardholder": "John Doe",
  "number": "1234567890123456",
  "exp_month": 12,
  "exp_year": 2025,
  "brand": "Visa"
}
```

---

### 2. **Add Income System** 💰

**कहाँ है:** `/income` page पर

**कैसे काम करता है:**
1. User "Add Income" button click करता है
2. Form open होता है जिसमें:
   - Source (कहाँ से आया - Salary, Freelance, Business, etc.)
   - Amount (₹)
   - Date (optional - default today)
   - Note (optional)
3. Form submit करने पर:
   - JavaScript form data collect करता है
   - `/api/income` endpoint पर POST request भेजता है
   - Backend transaction create करता है (type: "income")
   - Database में save होता है
   - Success message दिखता है
   - Form close हो जाता है
   - Page reload होकर नया income दिखता है

**API Endpoint:** `POST /api/income`
**Data Format:**
```json
{
  "source": "Salary",
  "amount": 50000,
  "date": "2025-11-08",
  "note": "Monthly salary"
}
```

**Database में कैसे store होता है:**
- `transactions` collection में
- `type: "income"`
- `user_id` automatically add होता है (session से)

---

### 3. **Add Expense System** 💸

**कहाँ है:** `/expense` page पर

**कैसे काम करता है:**
1. User "Add Expense" button click करता है
2. Form open होता है जिसमें:
   - Category (Food & Dining, Transport, Shopping, etc.)
   - Amount (₹)
   - Payee (किसको दिया - optional)
   - Date (optional - default today)
   - Note (optional)
3. Form submit करने पर:
   - JavaScript form data collect करता है
   - `/api/expense` endpoint पर POST request भेजता है
   - Backend transaction create करता है (type: "expense")
   - Database में save होता है
   - Success message दिखता है
   - Form close हो जाता है
   - Page reload होकर नया expense दिखता है

**API Endpoint:** `POST /api/expense`
**Data Format:**
```json
{
  "category": "Food & Dining",
  "amount": 500,
  "payee": "Restaurant ABC",
  "date": "2025-11-08",
  "note": "Dinner with friends"
}
```

**Database में कैसे store होता है:**
- `transactions` collection में
- `type: "expense"`
- `user_id` automatically add होता है (session से)

---

## Complete Flow Diagram

```
User Action → JavaScript → API Call → Backend Processing → Database → Response → UI Update
```

### Example: Add Income
1. **User:** "Add Income" button click करता है
2. **JavaScript:** Form data collect करता है
3. **API Call:** `POST /api/income` with JSON data
4. **Backend:**
   - Session check करता है (user logged in?)
   - Data validate करता है
   - Transaction create करता है
   - MongoDB में save करता है
5. **Response:** Success/Error message
6. **UI:** Success message दिखता है, page reload होता है

---

## Data Storage Structure

### Cards Collection
```json
{
  "_id": "ObjectId",
  "user_id": "user123",
  "cardholder": "John Doe",
  "last4": "3456",
  "masked_number": "**** **** **** 3456",
  "exp_month": 12,
  "exp_year": 2025,
  "brand": "Visa",
  "created_at": "2025-11-08T10:00:00Z"
}
```

### Transactions Collection (Income & Expense)
```json
{
  "_id": "ObjectId",
  "user_id": "user123",
  "type": "income" or "expense",
  "amount": 5000.00,
  "source": "Salary" (for income),
  "category": "Food & Dining" (for expense),
  "payee": "Store Name" (optional, for expense),
  "date": "2025-11-08",
  "note": "Additional details",
  "created_at": "2025-11-08T10:00:00Z"
}
```

---

## Features

✅ **Automatic User Association:** सभी data automatically logged-in user से link होता है
✅ **Real-time Updates:** Add करने के बाद page reload होकर नया data दिखता है
✅ **Validation:** Forms में required fields check होते हैं
✅ **Error Handling:** अगर कोई error हो तो user को message दिखता है
✅ **Success Messages:** Successfully add होने पर confirmation message
✅ **Delete Functionality:** हर record को delete कर सकते हैं

---

## API Endpoints Summary

| Action | Method | Endpoint | Description |
|--------|--------|----------|-------------|
| Add Card | POST | `/api/cards` | New card add करें |
| Get Cards | GET | `/api/cards` | सभी cards देखें |
| Delete Card | DELETE | `/api/cards/<id>` | Card delete करें |
| Add Income | POST | `/api/income` | Income add करें |
| Get Income | GET | `/api/income` | सभी income देखें |
| Delete Income | DELETE | `/api/income/<id>` | Income delete करें |
| Add Expense | POST | `/api/expense` | Expense add करें |
| Get Expenses | GET | `/api/expense` | सभी expenses देखें |
| Delete Expense | DELETE | `/api/expense/<id>` | Expense delete करें |

---

## Testing

1. **Add Card:**
   - `/cards` page पर जाएं
   - "Add Card" button click करें
   - Form fill करें
   - Submit करें
   - Card list में नया card दिखेगा

2. **Add Income:**
   - `/income` page पर जाएं
   - "Add Income" button click करें
   - Source, Amount, Date fill करें
   - Submit करें
   - Income table में नया entry दिखेगा

3. **Add Expense:**
   - `/expense` page पर जाएं
   - "Add Expense" button click करें
   - Category, Amount, Payee fill करें
   - Submit करें
   - Expense table में नया entry दिखेगा

---

## Troubleshooting

**अगर form submit नहीं हो रहा:**
- Browser console check करें (F12)
- Network tab में API call देखें
- Error message read करें

**अगर data save नहीं हो रहा:**
- MongoDB connection check करें
- Session check करें (logged in हैं?)
- Required fields fill किए हैं?

**अगर page reload नहीं हो रहा:**
- JavaScript file load हुई है?
- Browser console में errors check करें

