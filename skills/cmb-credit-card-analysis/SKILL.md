---
name: cmb-credit-card-analysis
description: Analyze China Merchants Bank credit card monthly spending reports with automatic categorization and visual breakdown.
homepage: https://github.com/openclaw/openclaw
metadata:
  {
    "openclaw":
      {
        "emoji": "💳",
        "requires": { "bins": ["python3"], "env": ["ALIBABA_MAIL_USERNAME", "ALIBABA_MAIL_PASSWORD"] },
        "primaryEnv": "ALIBABA_MAIL_USERNAME",
        "install":
          [
            {
              "id": "python-brew",
              "kind": "brew",
              "formula": "python",
              "bins": ["python3"],
              "label": "Install Python (brew)",
            },
          ],
      },
  }
---

# 💳 CMB Credit Card Analysis

_Analyze your China Merchants Bank credit card spending patterns_

此技能分析招商银行信用卡月度账单,提供分类统计和可视化报告。

## 核心功能

- **自动数据获取**: 从阿里云邮箱自动抓取招行信用卡账单邮件
- **智能分类**: 自动将交易按类别分组(餐饮、购物、交通、高铁等)
- **可视化报告**: 生成文本形式的支出占比图和详细交易记录
- **账单周期识别**: 按账单周期结束日期准确匹配月份账单

## 快速开始

### 环境配置

```bash
# 设置阿里云邮箱凭证(必需)
export ALIBABA_MAIL_USERNAME='your_email@example.com'
export ALIBABA_MAIL_PASSWORD='your_password'

# 添加到 ~/.zshrc 或 ~/.bash_profile 以持久化
echo "export ALIBABA_MAIL_USERNAME='your_email@example.com'" >> ~/.zshrc
echo "export ALIBABA_MAIL_PASSWORD='your_password'" >> ~/.zshrc
```

### 生成月度报告

```bash
cd {baseDir}
python3 scripts/query_report.py <年份> <月份>
```

**示例:**
```bash
# 生成2025年11月的账单报告
python3 scripts/query_report.py 2025 11

# 生成2026年1月的账单报告
python3 scripts/query_report.py 2026 1
```

## 重要说明

### 账单周期匹配规则

招行信用卡的账单周期通常是**上月13日至本月12日**。本技能按**账单周期结束日期**来匹配月份:

- 查询 `202511` (2025年11月) → 返回 `bill_date = 2025-11-12` 的账单
- 查询 `202512` (2025年12月) → 返回 `bill_date = 2025-12-12` 的账单

这确保了查询的月份与账单周期正确对应。

### 自动数据获取

如果查询的月份没有数据,脚本会:
1. 自动连接阿里云邮箱
2. 搜索最近60天的招行信用卡账单邮件
3. 解析并保存账单数据到本地数据库
4. 重新生成报告

### 手动获取账单

```bash
# 从邮箱获取最近30天的账单(默认)
python3 scripts/fetch_bills.py

# 获取最近90天的账单
python3 scripts/fetch_bills.py --days 90
```

## 报告内容

生成的报告包含:

1. **账单信息**
   - 账单日期(账单周期结束日期)
   - 应还总额
   - 最低还款额

2. **支出统计**
   - 总支出金额
   - 总交易笔数

3. **类别分析**
   - 各类别支出金额和占比
   - 每个类别的交易笔数
   - 按支出金额降序排列

4. **可视化图表**
   - ASCII条形图展示各类别占比

5. **交易明细**
   - 日期、商户、金额、类别的详细列表

## 消费分类

系统自动将交易分为以下类别:

- **餐饮**: 餐厅、咖啡店、快餐
- **购物**: 超市、商场、电商
- **出行**: 地铁、打车、网约车
- **高铁**: 火车票、高铁票
- **娱乐**: 电影、游戏、酒店、旅游
- **医疗**: 医院、药店
- **购书**: 书店
- **知识**: 在线课程、培训
- **生活缴费**: 水电、网络
- **其他**: 未分类交易

## 数据存储

- **数据库路径**: `{baseDir}/scripts/cmb_cc_bills.db`
- **数据库类型**: SQLite 3
- **表结构**:
  - `bills`: 账单信息(日期、金额)
  - `transactions`: 交易记录(日期、商户、金额、类别)
  - `processed_emails`: 邮件处理日志

## 技术栈

- **语言**: Python 3
- **数据库**: SQLite 3
- **依赖**: 标准库(sqlite3, datetime, collections, argparse)
- **邮件**: IMAP协议连接阿里云邮箱

## 故障排查

### 没有找到数据

如果查询的月份没有返回数据:

1. **检查环境变量**
   ```bash
   echo $ALIBABA_MAIL_USERNAME
   echo $ALIBABA_MAIL_PASSWORD
   ```

2. **手动获取数据**
   ```bash
   python3 scripts/fetch_bills.py --days 90
   ```

3. **检查数据库**
   ```bash
   sqlite3 scripts/cmb_cc_bills.db "SELECT id, bill_date, total_amount FROM bills"
   ```

### 自动获取失败

可能的原因:
- 环境变量未设置或密码错误
- 网络连接问题
- 账单邮件在垃圾箱中
- 需要增加搜索天数范围(`--days 90`)

## 注意事项

- 所有数据存储在本地,确保数据安全
- 账单邮件需要在阿里云邮箱收件箱中
- 支持多次运行,已处理的邮件会自动跳过
- 金额单位为人民币(CNY)