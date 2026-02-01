#!/usr/bin/env python3
"""
招行信用卡电子账单AI助理
每天轮询邮箱，读取招行信用卡账单并生成支出报告
"""

import imaplib
import email
from email.header import decode_header
import os
import json
import re
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional
import sqlite3


class CMBCCBillAssistant:
    def __init__(self):
        # 从环境变量获取邮箱凭据
        self.username = os.getenv('ALIBABA_MAIL_USERNAME')
        self.password = os.getenv('ALIBABA_MAIL_PASSWORD')
        
        if not self.username or not self.password:
            raise ValueError("未设置邮箱凭据环境变量")
            
        # 设置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # 设置数据库路径：优先使用 cmb_cc_assistant 子目录
        base_dir = os.path.dirname(os.path.abspath(__file__))
        assistant_dir = os.path.join(base_dir, 'cmb_cc_assistant')
        if os.path.isdir(assistant_dir):
            db_dir = assistant_dir
        else:
            db_dir = base_dir
        self.db_path = os.path.join(db_dir, 'cmb_cc_bills.db')
        self.init_database()
        
        # 招行账单相关关键词
        self.sender_keywords = ['creditcard@cmbchina.com', '招商银行', '信用卡']
        self.subject_keywords = ['信用卡', '账单', 'CMB', 'credit', '账单日', '还款日']
        
        # 消费分类规则
        self.expense_categories = {
            '餐饮': ['餐厅', '美食', '快餐', '咖啡', '茶饮', '火锅', '烤肉', '料理', '饭', '菜', '麦当劳', '肯德基', '星巴克'],
            '购物': ['超市', '商场', '购物', '百货', '服装', '鞋包', '化妆品', '数码', '电器', '淘宝', '天猫', '京东', '书籍', '书店'],
            '出行': ['地铁', '公交', '出租车', '滴滴', '加油', '航空', '机场'],
            '高铁': ['高铁', '火车', '铁路', '中铁网络', '中国铁路'],
            '娱乐': ['电影', '游戏', 'KTV', '酒吧', '旅游', '景点', '酒店', '度假', '游乐场'],
            '医疗': ['医院', '药房', '体检', '药品', '诊所'],
            '购书': ['书籍', '书店', '图书'],
            '知识': ['培训', '在线课程', '学习', '教育', '学校', '先知书店', '流利说'],
            '生活缴费': ['水电煤', '物业费', '宽带', '手机费', '燃气', '供暖'],
            '其他': []
        }
        
        # 最近一次账单信息缓存
        self.latest_bill_id = None
        self.latest_bill_date = None
    
    def init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建账单表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bill_date TEXT,
                due_date TEXT,
                total_amount REAL,
                min_payment REAL,
                currency TEXT DEFAULT 'CNY',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建消费明细表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
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
        ''')
        
        # 创建已处理邮件记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS processed_emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email_uid TEXT UNIQUE,
                subject TEXT,
                sender TEXT,
                received_date TEXT,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def connect_imap(self):
        """连接到IMAP服务器"""
        import ssl
        
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        mail = imaplib.IMAP4_SSL("imap.qiye.aliyun.com", 993, ssl_context=context)
        mail.login(self.username, self.password)
        return mail
    
    def search_cmb_emails(self, mail, days_back=7):
        """搜索招商银行信用卡账单邮件"""
        # 选择收件箱
        mail.select('INBOX')
        
        # 计算日期范围
        since_date = (datetime.now() - timedelta(days=days_back)).strftime("%d-%b-%Y")
        
        # 搜索邮件
        result, data = mail.search(None, f'SINCE {since_date}')
        
        if result != 'OK':
            self.logger.error("搜索邮件失败")
            return []
        
        email_ids = data[0].split()
        cmb_emails = []
        
        for email_id in email_ids:
            result, msg_data = mail.fetch(email_id, '(RFC822)')
            
            if result != 'OK':
                continue
                
            msg = email.message_from_bytes(msg_data[0][1])
            
            # 解析邮件头信息
            subject = self.decode_mime_words(str(msg['Subject'] or ''))
            sender = str(msg['From'] or '')
            
            # 检查是否为招行账单邮件
            if self.is_cmb_bill_email(subject, sender):
                # 获取邮件唯一ID
                result, uid_data = mail.fetch(email_id, '(UID)')
                uid = None
                if result == 'OK':
                    uid_match = re.search(rb'UID\s+(\d+)', uid_data[0])
                    if uid_match:
                        uid = uid_match.group(1).decode()
                
                cmb_emails.append({
                    'id': email_id,
                    'uid': uid,
                    'subject': subject,
                    'sender': sender,
                    'date': str(msg['Date']),
                    'message': msg
                })
        
        return cmb_emails
    
    def decode_mime_words(self, s):
        """解码MIME编码的字符串"""
        decoded_fragments = decode_header(s)
        decoded_string = ''
        
        for fragment, encoding in decoded_fragments:
            if isinstance(fragment, bytes):
                if encoding:
                    decoded_string += fragment.decode(encoding)
                else:
                    decoded_string += fragment.decode('utf-8', errors='ignore')
            else:
                decoded_string += fragment
        
        return decoded_string
    
    def is_cmb_bill_email(self, subject, sender):
        """判断是否为招行信用卡账单邮件"""
        subject_lower = subject.lower()
        sender_lower = sender.lower()
        
        # 检查发件人
        sender_match = any(keyword.lower() in sender_lower for keyword in self.sender_keywords)
        
        # 检查主题
        subject_match = any(keyword.lower() in subject_lower for keyword in self.subject_keywords)
        
        # 如果发件人匹配或主题匹配，则认为是招行账单邮件
        return sender_match or subject_match
    
    def extract_bill_info(self, email_message):
        """从邮件中提取账单信息"""
        # 获取邮件正文
        body = self.get_email_body(email_message)
        
        if not body:
            return None
        
        # 使用正则表达式提取账单信息
        bill_info = {}
        
        # 首先尝试提取账单周期信息，从中获取账单日
        cycle_pattern = r'([0-9]{4}/[0-9]{2}/[0-9]{2})-([0-9]{4}/[0-9]{2}/[0-9]{2})'
        cycle_match = re.search(cycle_pattern, body)
        if cycle_match:
            start_date, end_date = cycle_match.groups()
            # 使用结束日期作为账单日
            bill_info['bill_date'] = end_date.replace('/', '-')
        
        # 提取到期还款日 - 从文本中查找明确标识
        due_date_patterns = [
            r'到期还款日.*?([0-9]{4}/[0-9]{2}/[0-9]{2})',  # 到期还款日后跟日期
            r'([0-9]{4}/[0-9]{2}/[0-9]{2}).*?到期还款日',  # 日期后跟到期还款日
            r'[到期还款日|最后还款日|Due Date|Payment Due Date][：:]\s*([0-9]{4}-[0-9]{2}-[0-9]{2})',
            r'[到期还款日|最后还款日|Due Date|Payment Due Date][：:]\s*([0-9]{2}/[0-9]{2}/[0-9]{4})',
            r'([0-9]{4})年([0-9]{1,2})月([0-9]{1,2})日.*到期还款日',
            r'到期还款日.*?([0-9]{4})年([0-9]{1,2})月([0-9]{1,2})日',
        ]
        
        for pattern in due_date_patterns:
            due_date_match = re.search(pattern, body)
            if due_date_match:
                date_text = due_date_match.group(1)
                if '/' in date_text and '-' not in date_text:  # 如果是 YYYY/MM/DD 格式
                    bill_info['due_date'] = date_text.replace('/', '-')
                elif len(due_date_match.groups()) == 3:  # 年月日格式
                    year, month, day = due_date_match.groups()
                    bill_info['due_date'] = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                else:
                    bill_info['due_date'] = date_text
                break
        
        # 查找账单结构：信用额度 -> 应还总额 -> 最低还款额
        # 形如：&yen; 60,000.00  &yen; 4,145.01  &yen; 207.38
        credit_structure_pattern = r'&yen;\s*([0-9,]+\.[0-9]{2})\s*&yen;\s*([0-9,]+\.[0-9]{2})\s*&yen;\s*([0-9,]+\.[0-9]{2})'
        structure_match = re.search(credit_structure_pattern, body)
        
        if structure_match:
            credit_limit = float(structure_match.group(1).replace(',', ''))
            total_amount = float(structure_match.group(2).replace(',', ''))
            min_payment = float(structure_match.group(3).replace(',', ''))
            
            bill_info['total_amount'] = total_amount  # 第二个通常是应还总额
            bill_info['min_payment'] = min_payment   # 第三个是最小还款额
        else:
            # 如果没有找到这种结构，使用备用方法
            # 提取应还总额 - 优先查找明确标识
            total_amount_patterns = [
                r'(?:本期应还总额|应还总额|本期应还).*?&yen;\s*([0-9,]+\.[0-9]{2})',
                r'[应还总额|本期应还总额|Total Amount Due|Amount Due][：:]\s*[¥￥$]?\s*([0-9,]+\.?[0-9]*)',
                r'应还总额[：:]?\s*([0-9,]+\.?[0-9]*)',
                # 查找合理范围内的金额（排除信用额度）
                r'&yen;\s*([0-9,]{1,7}\.[0-9]{2})'  # 限制位数，排除大额信用额度
            ]
            
            for pattern in total_amount_patterns:
                for match in re.finditer(pattern, body):
                    amount_str = match.group(1).replace(',', '')
                    try:
                        amount = float(amount_str)
                        # 应还总额通常在几百到几千之间，不会超过信用额度
                        if 10 <= amount <= 50000:
                            bill_info['total_amount'] = amount
                            break
                    except ValueError:
                        continue
                if 'total_amount' in bill_info:
                    break
            
            # 提取最低还款额
            min_payment_patterns = [
                r'(?:最低还款额|最低).*?&yen;\s*([0-9,]+\.[0-9]{2})',
                r'[最低还款额|Minimum Payment][：:]\s*[¥￥$]?\s*([0-9,]+\.?[0-9]*)',
                r'最低还款额[：:]?\s*([0-9,]+\.?[0-9]*)',
                # 查找紧跟应还总额之后的金额（最小还款额）
                r'&yen;\s*' + str(bill_info.get('total_amount', r'[0-9,]+\.[0-9]{2}')) + r'\s*&yen;\s*([0-9,]+\.[0-9]{2})'
            ]
            
            for pattern in min_payment_patterns:
                for match in re.finditer(pattern, body):
                    amount_str = match.group(1).replace(',', '')
                    try:
                        amount = float(amount_str)
                        if amount < bill_info.get('total_amount', 100000):  # 最低还款额应小于应还总额
                            bill_info['min_payment'] = amount
                            break
                    except ValueError:
                        continue
                if 'min_payment' in bill_info:
                    break
        
        # 提取交易明细
        transactions = self.extract_transactions(body)
        bill_info['transactions'] = transactions
        
        return bill_info
    
    def get_email_body(self, email_message):
        """获取邮件正文"""
        body = ""
        
        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                
                # 跳过附件
                if "attachment" not in content_disposition:
                    if content_type == "text/plain":
                        charset = part.get_content_charset() or 'utf-8'
                        try:
                            body += part.get_payload(decode=True).decode(charset, errors='ignore')
                        except:
                            pass
                    elif content_type == "text/html":
                        # 对于HTML邮件，简单地移除标签
                        charset = part.get_content_charset() or 'utf-8'
                        try:
                            html_body = part.get_payload(decode=True).decode(charset, errors='ignore')
                            # 移除HTML标签
                            import re
                            clean_html = re.sub(r'<[^>]+>', ' ', html_body)
                            body += clean_html
                        except:
                            pass
        else:
            charset = email_message.get_content_charset() or 'utf-8'
            try:
                body = email_message.get_payload(decode=True).decode(charset, errors='ignore')
            except:
                body = ""
        
        return body
    
    def extract_transactions(self, body):
        """从账单文本中提取交易明细"""
        transactions = []
        
        # 消费记录的格式：日期  日期  商户名称  &yen;&nbsp;金额
        # 例如：1212      1213      财付通-肯德基      &yen;&nbsp;18.50
        transaction_pattern = r'(\d{2})(\d{2})\s+(\d{2})(\d{2})\s+([^\d\s&]{2,60}?)\s+&yen;&nbsp;([0-9,]+\.[0-9]{2})'
        matches = re.findall(transaction_pattern, body)
        
        for match in matches:
            # match[0][1] = 记账日期, match[2][3] = 交易日期, match[4] = 商户名称, match[5] = 金额
            transaction_date = f"{match[2]}/{match[3]}"  # 使用交易日期
            merchant = match[4].strip()
            amount_str = re.sub(r'[¥￥$,]', '', match[5]).strip()
            
            # 排除非消费类项目，如积分等
            if any(keyword in merchant.lower() for keyword in ['积分', '积分值', '查询']):
                continue
            
            # 过滤掉过于简短或不合理的商户名称
            if len(merchant) < 2 or len(merchant) > 50:
                continue
                
            # 过滤掉明显不合理的金额
            if not re.match(r'^[0-9,.]+$', amount_str):
                continue
            
            try:
                amount = float(amount_str.replace(',', ''))
                category = self.categorize_expense(merchant)
                
                transactions.append({
                    'transaction_date': transaction_date,
                    'merchant_name': merchant,
                    'amount': amount,
                    'category': category,
                    'description': f'{merchant} - ¥{amount}'
                })
            except ValueError:
                continue
        
        return transactions
    
    def categorize_expense(self, merchant_name):
        """对消费进行分类"""
        merchant_lower = merchant_name.lower()
        
        for category, keywords in self.expense_categories.items():
            for keyword in keywords:
                if keyword.lower() in merchant_lower:
                    return category
        
        return '其他'
    
    def save_bill_to_db(self, bill_info, email_uid, subject, sender, received_date):
        """将账单信息保存到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 插入账单基本信息
            cursor.execute('''
                INSERT INTO bills (bill_date, due_date, total_amount, min_payment)
                VALUES (?, ?, ?, ?)
            ''', (
                bill_info.get('bill_date'),
                bill_info.get('due_date'),
                bill_info.get('total_amount'),
                bill_info.get('min_payment')
            ))
            
            bill_id = cursor.lastrowid
            
            # 插入交易明细
            for transaction in bill_info.get('transactions', []):
                cursor.execute('''
                    INSERT INTO transactions (bill_id, transaction_date, merchant_name, amount, category, description)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    bill_id,
                    transaction['transaction_date'],
                    transaction['merchant_name'],
                    transaction['amount'],
                    transaction['category'],
                    transaction['description']
                ))
            
            # 记录已处理的邮件
            cursor.execute('''
                INSERT OR IGNORE INTO processed_emails (email_uid, subject, sender, received_date)
                VALUES (?, ?, ?, ?)
            ''', (email_uid, subject, sender, received_date))
            
            conn.commit()
            self.logger.info(f"成功保存账单信息，账单ID: {bill_id}")
            return bill_id
            
        except Exception as e:
            conn.rollback()
            self.logger.error(f"保存账单信息失败: {str(e)}")
            return None
        finally:
            conn.close()
    
    def is_email_processed(self, email_uid):
        """检查邮件是否已被处理"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM processed_emails WHERE email_uid = ?', (email_uid,))
        result = cursor.fetchone()
        
        conn.close()
        return result is not None
    
    def generate_bill_cycle_report(self, bill_id=None):
        """生成账单周期支出报告"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if bill_id:
            # 查询特定账单的交易数据
            query = '''
                SELECT t.category, SUM(t.amount) as total_amount, COUNT(*) as transaction_count
                FROM transactions t
                WHERE t.bill_id = ?
                GROUP BY t.category
                ORDER BY total_amount DESC
            '''
            
            cursor.execute(query, (bill_id,))
        else:
            # 查询最新的账单交易数据
            query = '''
                SELECT t.category, SUM(t.amount) as total_amount, COUNT(*) as transaction_count
                FROM transactions t
                JOIN bills b ON t.bill_id = b.id
                WHERE b.id = (SELECT MAX(id) FROM bills)
                GROUP BY t.category
                ORDER BY total_amount DESC
            '''
            
            cursor.execute(query)
        
        results = cursor.fetchall()
        
        # 获取账单信息
        if bill_id:
            cursor.execute('SELECT bill_date, due_date, total_amount, min_payment FROM bills WHERE id = ?', (bill_id,))
        else:
            cursor.execute('SELECT bill_date, due_date, total_amount, min_payment FROM bills ORDER BY id DESC LIMIT 1')
        
        bill_info = cursor.fetchone()
        
        conn.close()
        
        if not results:
            return "当前账单周期暂无消费记录"
        
        if bill_info:
            bill_date = bill_info[0]
            due_date = bill_info[1]
            total_amount = bill_info[2]
            min_payment = bill_info[3]
            
            # 生成报告
            report_lines = ["=== 招商银行信用卡账单周期消费报告 ==="]
            report_lines.append("")
            
            # 账单信息
            if bill_date:
                report_lines.append(f"账单周期: {bill_date}")
            if due_date:
                report_lines.append(f"到期还款日: {due_date}")
            if total_amount:
                report_lines.append(f"应还总额: ¥{total_amount}")
            if min_payment:
                report_lines.append(f"最低还款额: ¥{min_payment}")
            
            report_lines.append("")
            
            total_spending = sum(row[1] for row in results)  # row[1] is total_amount
            report_lines.append(f"本期消费总额: ¥{total_spending:.2f}")
            report_lines.append(f"本期消费笔数: {sum(row[2] for row in results)} 笔")  # row[2] is transaction_count
            report_lines.append("")
            
            report_lines.append("按类别支出明细:")
            for category, amount, count in results:
                percentage = (amount / total_spending) * 100 if total_spending > 0 else 0
                report_lines.append(f"- {category}: ¥{amount:.2f} ({percentage:.1f}%) [{count}笔]")
            
            report_lines.append("")
            report_lines.append("各类别占比图:")
            
            # 简单的文本形式饼图
            max_bar_length = 30
            for category, amount, _ in results:
                bar_length = int((amount / total_spending) * max_bar_length) if total_spending > 0 else 0
                bar = '█' * bar_length + '░' * (max_bar_length - bar_length)
                percentage = (amount / total_spending) * 100 if total_spending > 0 else 0
                report_lines.append(f"{category:8} {bar} {percentage:5.1f}%")
        else:
            # 如果没有账单信息，只显示消费统计
            report_lines = ["=== 招商银行信用卡账单周期消费报告 ==="]
            report_lines.append("")
            
            total_spending = sum(row[1] for row in results)
            report_lines.append(f"本期消费总额: ¥{total_spending:.2f}")
            report_lines.append(f"本期消费笔数: {sum(row[2] for row in results)} 笔")
            report_lines.append("")
            
            report_lines.append("按类别支出明细:")
            for category, amount, count in results:
                percentage = (amount / total_spending) * 100 if total_spending > 0 else 0
                report_lines.append(f"- {category}: ¥{amount:.2f} ({percentage:.1f}%) [{count}笔]")
            
            report_lines.append("")
            report_lines.append("各类别占比图:")
            
            # 简单的文本形式饼图
            max_bar_length = 30
            for category, amount, _ in results:
                bar_length = int((amount / total_spending) * max_bar_length) if total_spending > 0 else 0
                bar = '█' * bar_length + '░' * (max_bar_length - bar_length)
                percentage = (amount / total_spending) * 100 if total_spending > 0 else 0
                report_lines.append(f"{category:8} {bar} {percentage:5.1f}%")
        
        return '\n'.join(report_lines)
    
    def generate_monthly_report(self, year=None, month=None):
        """按自然月生成信用卡支出分析报告"""
        # 如果未指定月份，优先使用最近账单月，否则使用当前月份
        if year is None or month is None:
            target_date = None
            if getattr(self, "latest_bill_date", None):
                try:
                    target_date = datetime.strptime(self.latest_bill_date[:10], "%Y-%m-%d")
                except Exception:
                    target_date = None
            if target_date is None:
                target_date = datetime.now()
            year = target_date.year
            month = target_date.month

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 查询指定年月内所有账单的消费数据，按类别汇总
        query = '''
            SELECT t.category, SUM(t.amount) as total_amount, COUNT(*) as transaction_count
            FROM transactions t
            JOIN bills b ON t.bill_id = b.id
            WHERE strftime('%Y', b.bill_date) = ? AND strftime('%m', b.bill_date) = ?
            GROUP BY t.category
            ORDER BY total_amount DESC
        '''
        cursor.execute(query, (str(year), f"{month:02d}"))
        results = cursor.fetchall()

        if not results:
            conn.close()
            return f"{year}年{month}月暂无消费记录"

        # 计算总支出和总笔数
        total_spending = sum(row[1] for row in results)
        total_transactions = sum(row[2] for row in results)

        conn.close()

        # 生成报告
        report_lines = [f"=== 招商银行信用卡消费报告 ({year}年{month}月) ==="]
        report_lines.append("")
        report_lines.append(f"总支出: ¥{total_spending:.2f}")
        report_lines.append(f"总笔数: {total_transactions} 笔")
        report_lines.append("")
        report_lines.append("按类别支出明细:")
        for category, amount, count in results:
            percentage = (amount / total_spending) * 100 if total_spending > 0 else 0
            report_lines.append(f"- {category}: ¥{amount:.2f} ({percentage:.1f}%) [{count}笔]")

        report_lines.append("")
        report_lines.append("各类别占比图:")
        max_bar_length = 30
        for category, amount, _ in results:
            bar_length = int((amount / total_spending) * max_bar_length) if total_spending > 0 else 0
            bar = '█' * bar_length + '░' * (max_bar_length - bar_length)
            percentage = (amount / total_spending) * 100 if total_spending > 0 else 0
            report_lines.append(f"{category:8} {bar} {percentage:5.1f}%")

        return '\n'.join(report_lines)
    
    def check_new_bills(self):
        """检查是否有新的招行信用卡账单"""
        try:
            mail = self.connect_imap()
            cmb_emails = self.search_cmb_emails(mail)
            
            new_bills_found = 0
            
            for email_info in cmb_emails:
                email_uid = email_info['uid']
                
                # 检查邮件是否已处理
                if self.is_email_processed(email_uid):
                    self.logger.info(f"邮件已处理: {email_info['subject']}")
                    continue
                
                self.logger.info(f"发现新邮件: {email_info['subject']}")
                
                # 提取账单信息
                bill_info = self.extract_bill_info(email_info['message'])
                
                if bill_info:
                    self.logger.info(f"提取到账单信息: {bill_info}")
                    
                    # 保存到数据库
                    bill_id = self.save_bill_to_db(
                        bill_info,
                        email_info['uid'],
                        email_info['subject'],
                        email_info['sender'],
                        email_info['date']
                    )
                    
                    if bill_id is not None:
                        new_bills_found += 1
                        self.latest_bill_id = bill_id
                        if bill_info.get('bill_date'):
                            self.latest_bill_date = bill_info['bill_date']
                else:
                    self.logger.warning(f"未能从邮件中提取到账单信息: {email_info['subject']}")
            
            mail.logout()
            
            if new_bills_found > 0:
                self.logger.info(f"发现并处理了 {new_bills_found} 份新的信用卡账单")
                return True
            else:
                self.logger.info("未发现新的信用卡账单")
                return False
                
        except Exception as e:
            self.logger.error(f"检查新账单时发生错误: {str(e)}")
            return False
    
    def run_daily_check(self):
        """运行每日检查"""
        self.logger.info("开始每日招行信用卡账单检查")
        
        new_bills = self.check_new_bills()
        
        if new_bills:
            # 生成最新账单对应月份的报告
            report = None
            if getattr(self, "latest_bill_date", None):
                try:
                    target_date = datetime.strptime(self.latest_bill_date[:10], "%Y-%m-%d")
                    report = self.generate_monthly_report(target_date.year, target_date.month)
                except Exception:
                    report = None
            if report is None:
                report = self.generate_monthly_report()
            self.logger.info("新账单处理完成，生成报告如下:\n" + report)
            return report
        else:
            self.logger.info("今日未发现新的信用卡账单")
            return "今日未发现新的信用卡账单"


def main():
    """主函数 - 每日执行"""
    try:
        assistant = CMBCCBillAssistant()
        report = assistant.run_daily_check()
        print(report)
    except Exception as e:
        print(f"执行失败: {str(e)}")
        logging.error(f"执行招行信用卡助理失败: {str(e)}")


if __name__ == "__main__":
    main()