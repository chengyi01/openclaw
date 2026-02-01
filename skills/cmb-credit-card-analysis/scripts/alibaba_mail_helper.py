#!/usr/bin/env python3
"""
阿里企业邮箱助手 - 用于读取和管理阿里企业邮箱邮件
"""

import imaplib
import email
from email.header import decode_header
import getpass
import json
import os
import sys
from datetime import datetime, timedelta


class AlibabaMailHelper:
    def __init__(self, username=None, password=None):
        self.username = username or os.getenv('ALIBABA_MAIL_USERNAME')
        self.password = password or os.getenv('ALIBABA_MAIL_PASSWORD')
        self.imap_server = "imap.mxhichina.com"  # 阿里企业邮箱 IMAP 服务器
        self.smtp_server = "smtp.mxhichina.com"  # 阿里企业邮箱 SMTP 服务器
        
    def connect(self):
        """连接到阿里企业邮箱 IMAP 服务器"""
        try:
            self.mail = imaplib.IMAP4_SSL(self.imap_server)
            self.mail.login(self.username, self.password)
            return True
        except Exception as e:
            print(f"连接失败: {str(e)}")
            return False
    
    def disconnect(self):
        """断开连接"""
        if hasattr(self, 'mail'):
            try:
                self.mail.close()
                self.mail.logout()
            except:
                self.mail.logout()
    
    def list_folders(self):
        """列出所有邮箱文件夹"""
        try:
            status, folders = self.mail.list()
            folder_list = []
            for folder in folders:
                folder_info = folder.decode().split('"')
                if len(folder_info) >= 3:
                    folder_name = folder_info[-1].strip()
                    folder_list.append(folder_name)
            return folder_list
        except Exception as e:
            print(f"获取文件夹列表失败: {str(e)}")
            return []
    
    def select_folder(self, folder='INBOX'):
        """选择邮箱文件夹"""
        try:
            status, messages = self.mail.select(f'"{folder}"')
            if status == 'OK':
                if messages and len(messages) > 0:
                    msg_str = messages[0].decode() if isinstance(messages[0], bytes) else str(messages[0])
                    return int(msg_str) if msg_str.isdigit() else 0
                else:
                    return 0
            else:
                print(f"选择文件夹失败，状态: {status}")
                return 0
        except Exception as e:
            print(f"选择文件夹失败: {str(e)}")
            return 0
    
    def fetch_emails(self, num_emails=10, folder='INBOX'):
        """获取最新邮件"""
        try:
            self.select_folder(folder)
            status, messages = self.mail.search(None, 'ALL')
            
            if status != 'OK':
                return []
                
            email_ids = messages[0].split()
            # 获取最新的 num_emails 封邮件
            latest_email_ids = email_ids[-num_emails:] if len(email_ids) >= num_emails else email_ids
            
            emails = []
            for email_id in reversed(latest_email_ids):  # 从最新的开始
                status, msg_data = self.mail.fetch(email_id, '(RFC822)')
                if status == 'OK':
                    msg = email.message_from_bytes(msg_data[0][1])
                    
                    # 解码邮件主题
                    subject = self.decode_mime_words(str(msg.get("Subject")))
                    sender = self.decode_mime_words(str(msg.get("From")))
                    date = str(msg.get("Date"))
                    
                    # 获取邮件正文
                    body = self.get_body(msg)
                    
                    email_info = {
                        'id': email_id.decode(),
                        'subject': subject,
                        'sender': sender,
                        'date': date,
                        'body': body[:500] + "..." if len(body) > 500 else body  # 截取前500字符
                    }
                    emails.append(email_info)
            
            return emails
        except Exception as e:
            print(f"获取邮件失败: {str(e)}")
            return []
    
    def get_unread_count(self, folder='INBOX'):
        """获取未读邮件数量"""
        try:
            self.select_folder(folder)
            status, messages = self.mail.search(None, 'UNSEEN')
            if status == 'OK':
                email_ids = messages[0].split()
                return len(email_ids)
            return 0
        except Exception as e:
            print(f"获取未读邮件数失败: {str(e)}")
            return 0
    
    def get_recent_emails(self, days=1, folder='INBOX'):
        """获取最近几天的邮件"""
        try:
            self.select_folder(folder)
            since_date = (datetime.now() - timedelta(days=days)).strftime("%d-%b-%Y")
            status, messages = self.mail.search(None, f'SINCE {since_date}')
            
            if status != 'OK':
                return []
                
            email_ids = messages[0].split()
            emails = []
            for email_id in reversed(email_ids[-20:]):  # 最多返回20封
                status, msg_data = self.mail.fetch(email_id, '(RFC822)')
                if status == 'OK':
                    msg = email.message_from_bytes(msg_data[0][1])
                    
                    subject = self.decode_mime_words(str(msg.get("Subject")))
                    sender = self.decode_mime_words(str(msg.get("From")))
                    date = str(msg.get("Date"))
                    body = self.get_body(msg)
                    
                    email_info = {
                        'id': email_id.decode(),
                        'subject': subject,
                        'sender': sender,
                        'date': date,
                        'body': body[:500] + "..." if len(body) > 500 else body
                    }
                    emails.append(email_info)
            
            return emails
        except Exception as e:
            print(f"获取近期邮件失败: {str(e)}")
            return []
    
    def decode_mime_words(self, s):
        """解码 MIME 编码的邮件头"""
        decoded_fragments = decode_header(s)
        fragments = []
        for fragment, encoding in decoded_fragments:
            if isinstance(fragment, bytes):
                if encoding:
                    fragment = fragment.decode(encoding)
                else:
                    fragment = fragment.decode('utf-8', errors='ignore')
            fragments.append(fragment)
        return ''.join(fragments)
    
    def get_body(self, msg):
        """提取邮件正文"""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                
                if content_type == "text/plain" and "attachment" not in content_disposition:
                    try:
                        body = part.get_payload(decode=True).decode('utf-8')
                        return body
                    except:
                        try:
                            body = part.get_payload(decode=True).decode('gbk')
                            return body
                        except:
                            try:
                                body = part.get_payload(decode=True).decode('gb2312')
                                return body
                            except:
                                return "无法解析邮件正文"
        else:
            try:
                body = msg.get_payload(decode=True).decode('utf-8')
                return body
            except:
                try:
                    body = msg.get_payload(decode=True).decode('gbk')
                    return body
                except:
                    try:
                        body = msg.get_payload(decode=True).decode('gb2312')
                        return body
                    except:
                        return "无法解析邮件正文"
        return "无法解析邮件正文"


def main():
    if len(sys.argv) < 2:
        print("Usage: python alibaba_mail_helper.py [action] [options]")
        print("Actions: connect, list_folders, fetch_emails, get_unread, get_recent")
        return
    
    action = sys.argv[1]
    
    # 从环境变量或命令行参数获取用户名密码
    username = os.getenv('ALIBABA_MAIL_USERNAME') or (sys.argv[2] if len(sys.argv) > 2 else None)
    password = os.getenv('ALIBABA_MAIL_PASSWORD') or (sys.argv[3] if len(sys.argv) > 3 else None)
    
    if not username or not password:
        print("错误: 需要提供用户名和密码")
        print("可以通过环境变量 ALIBABA_MAIL_USERNAME 和 ALIBABA_MAIL_PASSWORD 设置")
        return
    
    helper = AlibabaMailHelper(username, password)
    
    if not helper.connect():
        print("连接失败")
        return
    
    try:
        if action == "connect":
            print("连接成功!")
            
        elif action == "list_folders":
            folders = helper.list_folders()
            print(json.dumps(folders, ensure_ascii=False))
            
        elif action == "fetch_emails":
            folder = sys.argv[2] if len(sys.argv) > 2 else 'INBOX'
            num = int(sys.argv[3]) if len(sys.argv) > 3 else 5
            emails = helper.fetch_emails(num, folder)
            print(json.dumps(emails, ensure_ascii=False))
            
        elif action == "get_unread":
            folder = sys.argv[2] if len(sys.argv) > 2 else 'INBOX'
            count = helper.get_unread_count(folder)
            print(f"未读邮件数量: {count}")
            
        elif action == "get_recent":
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 1
            folder = sys.argv[3] if len(sys.argv) > 3 else 'INBOX'
            emails = helper.get_recent_emails(days, folder)
            print(json.dumps(emails, ensure_ascii=False))
            
        else:
            print(f"未知操作: {action}")
    finally:
        helper.disconnect()


if __name__ == "__main__":
    main()