#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从阿里云邮箱获取招行信用卡账单数据并写入数据库
"""

import os
import sys
import logging
from datetime import datetime

# 导入 cmb_cc_assistant 模块
from cmb_cc_assistant import CMBCCBillAssistant


def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)


def check_environment():
    """检查环境变量"""
    username = os.getenv('ALIBABA_MAIL_USERNAME')
    password = os.getenv('ALIBABA_MAIL_PASSWORD')
    
    if not username or not password:
        print("\n❌ 错误: 未设置邮箱凭据环境变量")
        print("\n请设置以下环境变量:")
        print("  export ALIBABA_MAIL_USERNAME='your_email@example.com'")
        print("  export ALIBABA_MAIL_PASSWORD='your_password'")
        print("\n或者在 ~/.zshrc 或 ~/.bash_profile 中添加这些环境变量")
        return False
    
    return True


def fetch_and_process_bills(days_back=30):
    """
    从邮箱获取账单并处理
    
    Args:
        days_back: 往前查找的天数，默认30天
    """
    logger = setup_logging()
    
    # 检查环境变量
    if not check_environment():
        sys.exit(1)
    
    try:
        logger.info(f"🔍 开始从阿里云邮箱获取招行信用卡账单...")
        logger.info(f"📅 搜索范围: 最近 {days_back} 天")
        
        # 创建助手实例
        assistant = CMBCCBillAssistant()
        
        # 连接到IMAP服务器
        logger.info("📧 正在连接到邮箱服务器...")
        mail = assistant.connect_imap()
        
        # 搜索招行账单邮件
        logger.info("🔎 正在搜索招行信用卡账单邮件...")
        cmb_emails = assistant.search_cmb_emails(mail, days_back=days_back)
        
        if not cmb_emails:
            logger.warning("📭 未找到招行信用卡账单邮件")
            logger.info("\n💡 提示:")
            logger.info("   1. 确保招商银行已向您的邮箱发送账单邮件")
            logger.info("   2. 检查垃圾邮件文件夹")
            logger.info("   3. 确认邮箱设置中已开启账单邮件推送")
            logger.info("   4. 尝试增加搜索天数，例如: --days 60")
            mail.logout()
            return 0
        
        logger.info(f"✅ 找到 {len(cmb_emails)} 封招行信用卡账单相关邮件")
        
        # 处理账单邮件
        processed_count = 0
        skipped_count = 0
        
        for i, email_info in enumerate(cmb_emails, 1):
            logger.info(f"\n处理邮件 {i}/{len(cmb_emails)}")
            logger.info(f"  主题: {email_info['subject']}")
            logger.info(f"  日期: {email_info['date']}")
            
            # 检查是否已处理过
            if assistant.is_email_processed(email_info['uid']):
                logger.info("  ⏭️  已处理过，跳过")
                skipped_count += 1
                continue
            
            # 解析并保存账单
            logger.info("  📝 正在解析账单...")
            bill_info = assistant.extract_bill_info(email_info['message'])
            
            if bill_info:
                # 保存到数据库
                bill_id = assistant.save_bill_to_db(
                    bill_info,
                    email_info['uid'],
                    email_info['subject'],
                    email_info['sender'],
                    email_info['date']
                )
                
                if bill_id is not None:
                    logger.info("  ✅ 账单处理成功")
                    processed_count += 1
                else:
                    logger.warning("  ⚠️  账单保存失败")
            else:
                logger.warning("  ⚠️  账单解析失败")
        
        # 关闭连接
        mail.logout()
        
        # 输出统计信息
        logger.info(f"\n{'='*50}")
        logger.info(f"处理完成!")
        logger.info(f"  找到邮件: {len(cmb_emails)} 封")
        logger.info(f"  新处理: {processed_count} 封")
        logger.info(f"  跳过: {skipped_count} 封")
        logger.info(f"{'='*50}\n")
        
        return processed_count
        
    except ValueError as e:
        logger.error(f"❌ 配置错误: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ 发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='从阿里云邮箱获取招行信用卡账单数据',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  # 获取最近30天的账单（默认）
  python3 fetch_bills.py
  
  # 获取最近60天的账单
  python3 fetch_bills.py --days 60
  
  # 获取最近90天的账单
  python3 fetch_bills.py --days 90

环境变量:
  ALIBABA_MAIL_USERNAME  阿里云邮箱用户名
  ALIBABA_MAIL_PASSWORD  阿里云邮箱密码
'''
    )
    
    parser.add_argument(
        '--days',
        type=int,
        default=30,
        help='往前查找的天数 (默认: 30)'
    )
    
    args = parser.parse_args()
    
    # 执行获取
    processed = fetch_and_process_bills(days_back=args.days)
    
    # 返回退出码
    sys.exit(0 if processed > 0 else 1)


if __name__ == "__main__":
    main()
