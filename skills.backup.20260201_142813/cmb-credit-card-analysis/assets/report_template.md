# 招商银行信用卡月度消费报告模板

## {{MONTH}} 月度消费摘要

**持卡人:** {{HOLDER_NAME}}
**卡号:** **** **** **** {{CARD_SUFFIX}}
**账单周期:** {{START_DATE}} 至 {{END_DATE}}

---

## 总体消费情况
- **总支出:** ¥{{TOTAL_SPENDING}}
- **总交易笔数:** {{TRANSACTION_COUNT}} 笔
- **平均每日消费:** ¥{{DAILY_AVERAGE}}

---

## 消费分类统计

{% for category, amount in CATEGORIES %}
- **{{category}}:** ¥{{amount}} ({{percentage}}%)
{% endfor %}

---

## 消费趋势分析
- 最高单笔消费: ¥{{MAX_TRANSACTION}} - {{MERCHANT_NAME}}
- 消费高峰时段: {{PEAK_TIME}}
- 主要消费场所: {{MAIN_MERCHANTS}}

---

## 财务建议
{% for suggestion in SUGGESTIONS %}
- {{suggestion}}
{% endfor %}