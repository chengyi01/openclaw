#!/usr/bin/env python3
"""
招商银行信用卡分析工具
用于解析和分析CMB信用卡账单数据
"""

import pandas as pd
import re
from datetime import datetime
from typing import Dict, List, Optional


class CMBCreditCardAnalyzer:
    def __init__(self):
        self.transactions = []
        self.card_number = None
        
    def parse_transaction_data(self, data_source: str) -> List[Dict]:
        """
        解析招商银行信用卡交易数据
        :param data_source: 数据源（文本、文件路径等）
        :return: 交易记录列表
        """
        transactions = []
        
        # 根据不同数据源类型进行解析
        if data_source.endswith('.csv'):
            transactions = self._parse_csv(data_source)
        elif data_source.endswith('.pdf'):
            transactions = self._parse_pdf(data_source)
        else:
            # 假设是文本数据
            transactions = self._parse_text(data_source)
            
        return transactions
    
    def _parse_text(self, text_data: str) -> List[Dict]:
        """解析文本格式的交易数据"""
        transactions = []
        
        # 示例正则表达式匹配招商银行常见的交易记录格式
        # 实际应用中需要根据具体格式调整
        transaction_pattern = r'(\d{4}-\d{2}-\d{2})\s+(.+?)\s+([\-+]?\d+\.\d{2})'
        
        matches = re.findall(transaction_pattern, text_data)
        for match in matches:
            date, merchant, amount = match
            transactions.append({
                'date': date,
                'merchant': merchant.strip(),
                'amount': float(amount),
                'category': self.categorize_expense(merchant.strip())
            })
        
        return transactions
    
    def categorize_expense(self, merchant: str) -> str:
        """
        根据商户名称自动分类消费类型
        :param merchant: 商户名称
        :return: 消费类别
        """
        # 定义分类关键词
        categories = {
            '餐饮': ['餐厅', '咖啡', '奶茶', '快餐', '火锅', '烧烤', '肯德基', '麦当劳', '星巴克'],
            '购物': ['超市', '商场', '淘宝', '天猫', '京东', '拼多多', '苏宁', '国美'],
            '交通': ['滴滴', '高德', '地铁', '公交', '加油', '航空', '火车票'],
            '娱乐': ['电影', '游戏', '旅游', '景点', '酒店', '门票'],
            '生活缴费': ['电费', '水费', '燃气费', '话费', '物业费']
        }
        
        merchant_lower = merchant.lower()
        for category, keywords in categories.items():
            for keyword in keywords:
                if keyword.lower() in merchant_lower:
                    return category
        
        return '其他'
    
    def generate_monthly_report(self, transactions: List[Dict], month: str) -> Dict:
        """
        生成月度消费报告
        :param transactions: 交易记录列表
        :param month: 月份（如 '2025-12'）
        :return: 月度报告
        """
        # 过滤指定月份的交易
        monthly_transactions = [
            t for t in transactions 
            if t['date'].startswith(month)
        ]
        
        # 按类别汇总
        category_totals = {}
        total_amount = 0
        
        for transaction in monthly_transactions:
            category = transaction['category']
            amount = abs(transaction['amount'])  # 使用绝对值计算总支出
            
            if category in category_totals:
                category_totals[category] += amount
            else:
                category_totals[category] = amount
            
            if transaction['amount'] > 0:  # 只统计支出
                total_amount += amount
        
        return {
            'month': month,
            'total_spending': total_amount,
            'category_breakdown': category_totals,
            'transaction_count': len(monthly_transactions),
            'transactions': monthly_transactions
        }


def analyze_cmb_card(card_number_suffix: str, month: str, data_source: str):
    """
    主要分析函数
    :param card_number_suffix: 卡号后四位
    :param month: 分析月份
    :param data_source: 数据源
    :return: 分析结果
    """
    analyzer = CMBCreditCardAnalyzer()
    transactions = analyzer.parse_transaction_data(data_source)
    
    # 过滤指定卡号的交易（在实际实现中需要根据真实数据结构调整）
    filtered_transactions = transactions  # 简化处理
    
    report = analyzer.generate_monthly_report(filtered_transactions, month)
    return report