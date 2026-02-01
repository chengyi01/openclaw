#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速查询指定月份的招行信用卡支出报告
"""

import sqlite3
from datetime import datetime
from collections import defaultdict
import sys
import os
import subprocess
import argparse


def fetch_bills_from_email(days=60):
    """
    调用 fetch_bills.py 从邮箱获取账单数据
    
    Args:
        days: 往前查找的天数，默认60天
        
    Returns:
        bool: 是否成功获取到新数据
    """
    try:
        # 获取脚本所在目录
        script_dir = os.path.dirname(os.path.abspath(__file__))
        fetch_script = os.path.join(script_dir, 'fetch_bills.py')
        
        if not os.path.exists(fetch_script):
            print(f"错误: 找不到数据获取脚本: {fetch_script}")
            return False
        
        # 调用 fetch_bills.py
        result = subprocess.run(
            [sys.executable, fetch_script, '--days', str(days)],
            capture_output=True,
            text=True
        )
        
        # 输出脚本的输出
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        
        # 返回是否成功（退出码为0表示成功）
        return result.returncode == 0
        
    except Exception as e:
        print(f"调用数据获取脚本时出错: {str(e)}")
        return False


def generate_monthly_report(year, month):
    """
    生成指定年月的信用卡支出报告
    """
    # 连接数据库 - 指向当前脚本目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(script_dir, 'cmb_cc_bills.db')
    
    if not os.path.exists(db_path):
        print(f"错误: 数据库文件不存在")
        print(f"期望路径: {db_path}")
        print("请确保 CMB 信用卡助手已正确设置并至少运行一次。")
        sys.exit(1)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 查询指定年月的交易记录
    cursor.execute('''
    SELECT t.transaction_date, t.merchant_name, t.amount, t.category, t.description
    FROM transactions t
    JOIN bills b ON t.bill_id = b.id
    WHERE strftime('%Y', b.bill_date) = ? AND strftime('%m', b.bill_date) = ?
    ORDER BY t.transaction_date ASC
    ''', (str(year), f"{month:02d}"))
    
    transactions = cursor.fetchall()
    
    if not transactions:
        # 尝试另一种查询方式：直接按交易日期查询
        cursor.execute('''
        SELECT t.transaction_date, t.merchant_name, t.amount, t.category, t.description
        FROM transactions t
        WHERE strftime('%Y', '2000-' || t.transaction_date) = ? AND strftime('%m', '2000-' || t.transaction_date) = ?
        ORDER BY t.transaction_date ASC
        ''', (str(year), f"{month:02d}"))
        
        transactions = cursor.fetchall()
        
        if not transactions:
            # 再尝试一种格式：MM/DD
            cursor.execute('''
            SELECT t.transaction_date, t.merchant_name, t.amount, t.category, t.description
            FROM transactions t
            WHERE substr(t.transaction_date, 1, instr(t.transaction_date, '/') - 1) = ? 
            AND substr(t.transaction_date, instr(t.transaction_date, '/') + 1) = ?
            ORDER BY t.transaction_date ASC
            ''', (f"{month:02d}", str(year)[2:]))
            
            transactions = cursor.fetchall()
    
    if not transactions:
        conn.close()
        print(f"\n⚠️  {year}年{month}月暂无消费记录")
        print("\n尝试从邮箱获取最新账单数据...")
        
        # 尝试从邮箱获取数据
        if fetch_bills_from_email():
            print("\n✅ 数据获取成功，重新生成报告...\n")
            # 重新连接数据库并查询
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT t.transaction_date, t.merchant_name, t.amount, t.category, t.description
            FROM transactions t
            JOIN bills b ON t.bill_id = b.id
            WHERE strftime('%Y', b.bill_date) = ? AND strftime('%m', b.bill_date) = ?
            ORDER BY t.transaction_date ASC
            ''', (str(year), f"{month:02d}"))
            
            transactions = cursor.fetchall()
            
            if not transactions:
                print(f"❌ {year}年{month}月仍然没有找到消费记录")
                print("\n可能的原因:")
                print("  1. 该月份的账单邮件尚未收到")
                print("  2. 账单邮件在垃圾邮件箱中")
                print("  3. 需要增加搜索天数范围")
                conn.close()
                return
        else:
            print("\n❌ 从邮箱获取数据失败")
            print("\n请检查:")
            print("  1. 环境变量 ALIBABA_MAIL_USERNAME 和 ALIBABA_MAIL_PASSWORD 是否已设置")
            print("  2. 邮箱账号密码是否正确")
            print("  3. 网络连接是否正常")
            return
    
    # 按类别统计
    category_totals = defaultdict(float)
    category_counts = defaultdict(int)
    total_spending = 0
    
    for trans in transactions:
        _, merchant, amount, category, desc = trans
        category_totals[category] += amount
        category_counts[category] += 1
        total_spending += amount
    
    # 获取账单信息（如果有）
    cursor.execute('''
    SELECT bill_date, due_date, total_amount, min_payment
    FROM bills
    WHERE strftime('%Y', bill_date) = ? AND strftime('%m', bill_date) = ?
    ORDER BY bill_date DESC
    LIMIT 1
    ''', (str(year), f"{month:02d}"))
    
    bill_info = cursor.fetchone()
    
    # 关闭连接
    conn.close()
    
    # 生成报告
    print(f"=== 招商银行信用卡消费报告 ({year}年{month}月) ===")
    print()
    
    if bill_info:
        bill_date, due_date, total_amount, min_payment = bill_info
        print(f"账单日期: {bill_date}")
        if due_date:
            print(f"到期还款日: {due_date}")
        if total_amount:
            print(f"应还总额: ¥{total_amount}")
        if min_payment:
            print(f"最低还款额: ¥{min_payment}")
        print()
    
    print(f"总支出: ¥{total_spending:.2f}")
    print(f"总笔数: {len(transactions)} 笔")
    print()
    
    print("按类别支出明细:")
    # 按支出金额排序
    sorted_categories = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
    
    for category, amount in sorted_categories:
        percentage = (amount / total_spending) * 100 if total_spending > 0 else 0
        count = category_counts[category]
        print(f"- {category}: ¥{amount:.2f} ({percentage:.1f}%) [{count}笔]")
    
    print()
    print("各类别占比图:")
    
    # 生成简单的文本形式饼图
    max_category_length = max(len(cat) for cat in category_totals.keys()) if category_totals else 10
    
    for category, amount in sorted_categories:
        percentage = (amount / total_spending) * 100 if total_spending > 0 else 0
        bar_length = int(percentage / 2)  # 每2%对应一个字符
        bar = "█" * bar_length + "░" * max(0, 50 - bar_length)
        print(f"{category:<{max_category_length}} {bar} {percentage:.1f}%")
    
    print()
    print("详细交易记录(≥¥20):")
    print("-" * 80)
    print(f"{'日期':<8} {'商户':<30} {'金额':<10} {'类别':<10}")
    print("-" * 80)
        
    # 过滤低于20元的交易
    filtered_transactions = [t for t in transactions if t[2] >= 20]
        
    if filtered_transactions:
        for trans in filtered_transactions:
            trans_date, merchant, amount, category, desc = trans
            # 处理日期格式,使其适合显示
            display_date = f"{month:02d}/{trans_date.split('/')[-1]}" if '/' in trans_date else trans_date
            # 截断过长的商户名称
            short_merchant = merchant[:28] + ".." if len(merchant) > 30 else merchant
            print(f"{display_date:<8} {short_merchant:<30} ¥{amount:<9.2f} {category:<10}")
    else:
        print("(所有交易金额均低于¥20)")


def main():
    parser = argparse.ArgumentParser(description='生成指定月份的招行信用卡支出报告')
    parser.add_argument('year', type=int, help='年份，例如 2026')
    parser.add_argument('month', type=int, help='月份，例如 1')
    
    args = parser.parse_args()
    
    generate_monthly_report(args.year, args.month)


if __name__ == "__main__":
    main()