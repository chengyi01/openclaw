# Technical Documentation

## Scripts Overview

### 1. query_report.py
**Main script** for generating monthly credit card spending reports.

**Features:**
- Queries SQLite database for transaction data
- Generates formatted reports with categories and visualizations
- **Auto-fetch**: Automatically calls `fetch_bills.py` if data is missing
- Provides detailed error messages and troubleshooting hints

**Usage:**
```bash
python3 query_report.py 2026 1
```

### 2. fetch_bills.py
**Data acquisition script** that retrieves bills from email.

**Features:**
- Connects to Alibaba Cloud IMAP server
- Searches for CMB credit card bill emails
- Parses bill content and transactions
- Saves data to SQLite database
- Skips already-processed emails

**Usage:**
```bash
python3 fetch_bills.py --days 60
```

**Requirements:**
- Environment variables: `ALIBABA_MAIL_USERNAME`, `ALIBABA_MAIL_PASSWORD`
- Network connectivity to Alibaba Cloud IMAP server

### 3. cmb_cc_assistant.py
**Core processing module** containing the main logic.

**Key Classes:**
- `CMBCCBillAssistant`: Main class for bill processing
  - Database initialization and management
  - IMAP connection handling
  - Email parsing and bill extraction
  - Transaction categorization
  - Data persistence

**Features:**
- Expense categorization (10 categories: 餐饮、购物、出行、高铁、娱乐、医疗、购书、知识、生活缴费、其他)
- Duplicate email detection
- Multi-encoding support (UTF-8, GBK, GB2312)
- Bill date parsing and validation

### 4. alibaba_mail_helper.py
**Email utility module** for Alibaba Cloud operations.

**Key Classes:**
- `AlibabaMailHelper`: Email operations helper
  - IMAP connection management
  - Folder navigation
  - Email fetching and searching
  - MIME decoding

**Features:**
- SSL/TLS connection to Alibaba Cloud IMAP
- Multiple encoding support
- Email body extraction
- Folder listing and management

## Data Flow

```
┌─────────────────┐
│  User Request   │
│  (year, month)  │
└────────┬────────┘
         │
         v
┌─────────────────┐
│ query_report.py │
└────────┬────────┘
         │
         v
  ┌─────────────────┐
  │  Query Database │
  └────────┬────────┘
           │
           v
    ┌──────────────┐     ┌──────────────┐
    │ Data Found?  │────>│ Generate     │
    │     Yes      │     │ Report       │
    └──────────────┘     └──────────────┘
           │
           │ No
           v
    ┌──────────────────┐
    │  fetch_bills.py  │
    └────────┬─────────┘
             │
             v
    ┌─────────────────────┐
    │ cmb_cc_assistant.py │
    │ + alibaba_mail_     │
    │   helper.py         │
    └────────┬────────────┘
             │
             v
    ┌────────────────┐
    │ Connect IMAP   │
    │ Search Emails  │
    │ Parse Bills    │
    │ Save to DB     │
    └────────┬───────┘
             │
             v
    ┌────────────────┐
    │ Retry Query    │
    │ Generate Report│
    └────────────────┘
```

## Database Schema

### bills table
```sql
CREATE TABLE bills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bill_date TEXT,
    due_date TEXT,
    total_amount REAL,
    min_payment REAL,
    currency TEXT DEFAULT 'CNY',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### transactions table
```sql
CREATE TABLE transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bill_id INTEGER,
    transaction_date TEXT,
    merchant_name TEXT,
    amount REAL,
    category TEXT,
    description TEXT,
    currency TEXT DEFAULT 'CNY',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bill_id) REFERENCES bills (id)
)
```

### processed_emails table
```sql
CREATE TABLE processed_emails (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email_uid TEXT UNIQUE,
    subject TEXT,
    sender TEXT,
    received_date TEXT,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

## Error Handling

### Database Not Found
- Message: "错误: 数据库文件不存在"
- Resolution: Ensures CMB assistant workspace exists

### No Data for Month
- Auto-triggers email fetch
- Searches past 60 days by default
- Provides helpful error messages if still no data

### Email Connection Failed
- Checks environment variables
- Verifies credentials
- Tests network connectivity
- Provides troubleshooting steps

### Bill Parsing Failed
- Logs detailed error information
- Continues processing other emails
- Reports processing statistics

## Security Considerations

1. **Credentials Storage**
   - Never hardcode credentials
   - Use environment variables only
   - Consider using system keychain for production

2. **Database Access**
   - SQLite file permissions should be user-only
   - Database path is in user's home directory

3. **Email Security**
   - Uses SSL/TLS for IMAP connection
   - Supports app-specific passwords
   - No plain text credential storage

## Performance

- **Database queries**: Optimized with indexes on bill_date
- **Email fetching**: Processes up to 60 days at a time
- **Duplicate detection**: Uses email UID for efficiency
- **Memory usage**: Processes emails one at a time

## Future Enhancements

Potential improvements:
- [ ] Add support for multiple credit cards
- [ ] Implement data export (CSV, Excel)
- [ ] Add trend analysis across months
- [ ] Support custom category rules
- [ ] Add budget tracking and alerts
- [ ] Implement data visualization (charts)
- [ ] Support other email providers (Gmail, Outlook)
