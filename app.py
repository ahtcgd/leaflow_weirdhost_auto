import os
import re
import json
import pytz
import time
import requests
from typing import List, Tuple
from datetime import datetime, timedelta
from playwright.sync_api import Playwright, sync_playwright, expect, TimeoutError

# 定义账户凭证类型
AccountCredentials = List[Tuple[str, str]]
def parse_accounts(accounts_str: str) -> AccountCredentials:
    # 从账户字符串中解析账户凭证。 "邮箱1,密码1 邮箱2,密码2"
    accounts: AccountCredentials = []

    # 账户之间用空格分隔
    account_pairs = [pair.strip() for pair in accounts_str.split(' ') if pair.strip()]

    for pair in account_pairs:
        # 邮箱和密码之间用逗号分隔
        parts = [part.strip() for part in pair.split(',') if part.strip()]

        if len(parts) == 2:
            accounts.append((parts[0], parts[1]))
        else:
            print(f"⚠️ 警告：跳过格式错误的账户对 '{pair}'。请使用 '邮箱,密码' 格式。")
    return accounts

def run(playwright: Playwright) -> None:
    # --- 环境变量配置 ---
    # ---------------------------------------------------------------------------------
    # 用户可编辑区域：在这里直接填写您的 Leaflow 多账户 (格式: "邮箱1,密码1 邮箱2,密码2")
    # 如果设置了 LEAFLOW_ACCOUNTS 环境变量，它将覆盖此处的默认值。
    # ---------------------------------------------------------------------------------
    # 示例: "test1@example.com,pass1 test2@example.com,pass2"
    DEFAULT_LEAFLOW_ACCOUNTS_STR = ""

    # 获取账户源字符串：优先从环境变量 'LEAFLOW_ACCOUNTS' 获取，否则使用默认字符串。
    accounts_source_str = os.environ.get('LEAFLOW_ACCOUNTS', DEFAULT_LEAFLOW_ACCOUNTS_STR)
    # Leaflow 多账户配置
    LEAFLOW_ACCOUNTS = parse_accounts(accounts_source_str)

    # Telegram Bot 通知配置（可选）
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

    # 启用无头模式
    browser = playwright.chromium.launch(headless=True)

    # 推送telegram消息
    def send_telegram_message(message):
        if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
            print("Telegram bot token or chat ID not configured. Skipping Telegram notification.")
            return False

        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message
        }

        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            print("Telegram notification sent successfully.")
            return True
        except Exception as e:
            print(f"Failed to send Telegram notification: {e}")
            return False

    # 保存cookies到指定文件。
    def save_cookies(context, file_path: str):
      cookies = context.cookies()
      try:
          with open(file_path, 'w', encoding='utf-8') as f:
              json.dump(cookies, f, indent=4)
          print(f"✅ Cookies 已成功保存到 '{file_path}'")
      except Exception as e:
          print(f"❌ 错误：保存 cookies 文件时发生未知错误：{e}")

    # --- LEAFLOW 多账户执行步骤 ---
    if LEAFLOW_ACCOUNTS:
        print(f"\n--- 开始执行 Leaflow 多账户签到任务 ({len(LEAFLOW_ACCOUNTS)} 个账户) ---")

        for index, (email, password) in enumerate(LEAFLOW_ACCOUNTS):
            # 为每个账户创建新的、隔离的浏览器上下文和页面
            context = browser.new_context()
            page = context.new_page()
            email_id = email.split('@')[0]
            print(f"\n[Leaflow - {email_id}] 账号 #{index + 1} ({email}) 开始执行...")

            try:
                print(f"[{email_id}] 🚀 导航至 leaflow.net...")
                page.goto(
                    "https://leaflow.net/",
                    timeout=60000,
                    wait_until="domcontentloaded"
                )

                page.get_by_role("button", name="登录", exact=True).click()
                page.get_by_role("textbox", name="邮箱或手机号").fill(email)
                page.get_by_role("textbox", name="密码").fill(password)

                page.get_by_role("button", name="登录 / 注册").click()

                page.wait_for_selector('text="工作区"', timeout=20000)
                print(f"[{email_id}] 已完成登录尝试。")

                page.get_by_role("link", name="工作区").click()
                page.get_by_text("签到试用").click()
                print(f"[{email_id}] 已进入签到页面...")

                try:
                    page.locator("#app iframe").content_frame.get_by_role("button", name=" 立即签到").click()
                    print(f"✅ 任务执行成功: [{email_id}] 签到操作已完成。")
                    content = f"🆔LEAFLOW帐号: {email_id}\n"
                    content += f"🚀签到状态: 签到操作已完成\n"
                    telegram_message = f"**LEAFLOW签到信息**\n{content}"
                    send_telegram_message(telegram_message)
                except Exception as e:
                    print(f"✅ [{email_id}] 今日已经签到！")
                    content = f"🆔LEAFLOW帐号: {email_id}\n"
                    content += f"🚀签到状态: 今日已经签到！\n"
                    telegram_message = f"**LEAFLOW签到信息**\n{content}"
                    send_telegram_message(telegram_message)

            except TimeoutError as te:
                print(f"❌ 任务执行失败：Playwright (操作超时：{te})")
                page.screenshot(path="leaflow_error_screenshot.png")
                content = f"🆔LEAFLOW帐号: {email_id}\n"
                content += f"🚀签到状态: 任务执行失败：Playwright 操作超时\n"
                telegram_message = f"**LEAFLOW签到信息**\n{content}"
                send_telegram_message(telegram_message)
            except Exception as e:
                print("❌ 任务执行失败：详细错误信息: {e}")
                page.screenshot(path="leaflow_final_error_screenshot.png") # 失败时强制截图
                content = f"🆔LEAFLOW帐号: {email_id}\n"
                content += f"🚀签到状态: 任务执行失败 (未知错误: {e})\n"
                telegram_message = f"**LEAFLOW签到信息**\n{content}"
                send_telegram_message(telegram_message)
            finally:
                # 隔离清理：关闭当前账户的页面和上下文
                page.close()
                context.close()
                time.sleep(10) # 账户间延迟，确保资源释放

        time.sleep(30) # 两个主要任务之间的延迟
    else:
         print("\n--- ℹ️ 跳过 Leaflow 任务：未配置 LEAFLOW_ACCOUNTS。 ---")
         time.sleep(5) # 保持延迟

    # ---------------------
    browser.close()
    print("\n--- 所有任务执行完毕 ---")


if __name__ == '__main__':
    with sync_playwright() as playwright:
        run(playwright)
