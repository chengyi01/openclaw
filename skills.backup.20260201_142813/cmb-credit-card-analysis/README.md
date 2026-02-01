# CMB Credit Card Analysis Skill

This skill provides monthly spending analysis for China Merchants Bank (招商银行) credit cards.

## What it does

- Reads credit card transaction data from a local SQLite database
- Generates comprehensive monthly spending reports based on **billing cycle end date**
- Automatically categorizes expenses (dining, shopping, transportation, etc.)
- Provides visual spending distribution charts
- Lists all transaction details
- **Auto-fetches missing data**: If the requested month's data doesn't exist, automatically fetches it from Alibaba Cloud email

## Important: Billing Cycle Matching Rule

**CMB credit card billing cycles typically run from the 13th of the previous month to the 12th of the current month.**

This skill matches reports by the **billing cycle end date**:

- Query `202511` (November 2025) → Returns bill with `bill_date = 2025-11-12`
- Query `202512` (December 2025) → Returns bill with `bill_date = 2025-12-12`

For example, when you request "November 2025 report", you get the bill that **ends** on November 12, 2025, which covers transactions from October 13, 2025 to November 12, 2025.

This ensures the query month correctly corresponds to the billing cycle.

## Prerequisites

1. Database location:
   - Location: `skills/cmb-credit-card-analysis/scripts/`
   - Database: `cmb_cc_bills.db`

2. Alibaba Cloud email credentials (for automatic data fetching):
   ```bash
   export ALIBABA_MAIL_USERNAME='your_email@example.com'
   export ALIBABA_MAIL_PASSWORD='your_password'
   ```

3. Python 3 installed on your system

## Usage

Ask the AI assistant to generate a report, for example:

- "给我生成2026年1月的招行信用卡消费报告"
- "查看我上个月的信用卡支出情况"
- "分析一下我最近的信用卡消费"

The AI will automatically use this skill to:
1. Locate the database
2. Query the specified month's data
3. If data not found, automatically fetch from email
4. Generate and present the formatted report

## Automatic Data Fetching

When you request a report for a month with no data, the skill will:

1. **Detect missing data**: Recognize that the requested month has no transactions
2. **Connect to email**: Use your Alibaba Cloud email credentials
3. **Search for bills**: Look for CMB credit card bill emails (past 60 days)
4. **Parse and save**: Extract bill data and save to the database
5. **Generate report**: Create the report with the newly fetched data

This happens automatically - no manual intervention needed!

## Manual Data Fetching

You can also manually fetch bills:

```bash
cd /path/to/openclaw/skills/cmb-credit-card-analysis

# Fetch from past 30 days (default)
python3 scripts/fetch_bills.py

# Fetch from past 60 days
python3 scripts/fetch_bills.py --days 60

# Fetch from past 90 days
python3 scripts/fetch_bills.py --days 90
```

## Manual Usage

You can also run the script directly:

```bash
cd /path/to/openclaw/skills/cmb-credit-card-analysis

# Generate November 2025 report (billing cycle ending 2025-11-12)
python3 scripts/query_report.py 2025 11

# Generate January 2026 report (billing cycle ending 2026-01-12)
python3 scripts/query_report.py 2026 1
```

## Output

The report includes:

1. **Statement Summary**
   - Statement date (账单日期)
   - Due date (到期还款日)
   - Total amount (应还总额)
   - Minimum payment (最低还款额)

2. **Spending Overview**
   - Total spending amount
   - Number of transactions

3. **Category Breakdown**
   - Spending by category with percentages
   - Transaction counts per category

4. **Visual Chart**
   - ASCII bar chart showing spending distribution

5. **Transaction List**
   - Detailed list of all transactions with dates, merchants, amounts, and categories

## Categories

Transactions are categorized into:
- 餐饮 (Dining)
- 购物 (Shopping)
- 出行 (Transportation)
- 高铁 (High-speed rail)
- 娱乐 (Entertainment)
- 医疗 (Healthcare)
- 购书 (Books)
- 知识 (Education)
- 生活缴费 (Utilities)
- 其他 (Other)

## Integration

This skill is designed to work seamlessly with the OpenClaw agent system. The AI assistant can:
- Understand natural language requests for reports
- Automatically determine the correct month to query
- Present results in a clear, readable format
- Answer follow-up questions about the spending data

## Troubleshooting

### Database not found

If you get an error about the database not existing:
1. Check that `cmb_cc_bills.db` exists at `skills/cmb-credit-card-analysis/scripts/`
2. Run `python3 scripts/fetch_bills.py` to fetch bill data from email
3. Verify environment variables are set correctly

### No data for requested month

If no data is found for the requested month:
1. **Check environment variables**:
   ```bash
   echo $ALIBABA_MAIL_USERNAME
   echo $ALIBABA_MAIL_PASSWORD
   ```
2. **Manually fetch data**:
   ```bash
   python3 scripts/fetch_bills.py --days 90
   ```
3. **Check database**:
   ```bash
   sqlite3 scripts/cmb_cc_bills.db "SELECT id, bill_date, total_amount FROM bills"
   ```

### Auto-fetch fails

Possible causes:
- Environment variables not set or incorrect password
- Network connection issues
- Bill emails in spam folder
- Need to increase search range (`--days 90`)

## Technical Details

- **Language**: Python 3
- **Dependencies**: Standard library only (no pip install needed)
- **Database**: SQLite 3
- **Encoding**: UTF-8
