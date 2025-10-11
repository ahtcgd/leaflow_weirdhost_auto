import os
import re
import pytz
import time
from datetime import datetime, timedelta
from playwright.sync_api import Playwright, sync_playwright, expect

def run(playwright: Playwright) -> None:
    # 环境变量
    LEAFLOW_EMAIL = os.environ.get('LEAFLOW_EMAIL', '')
    LEAFLOW_PASSWORD = os.environ.get('LEAFLOW_PASSWORD', '')

    WEIRDHOST_EMAIL = os.environ.get('WEIRDHOST_EMAIL', '')
    WEIRDHOST_PASSWORD = os.environ.get('WEIRDHOST_PASSWORD', '')
    REMEMBER_WEB_COOKIE = os.environ.get('REMEMBER_WEB_COOKIE')
    WEIRDHOST_SERVER_URL = os.environ.get('WEIRDHOST_SERVER_URL', '')

    # 启用无头模式 (在 CI/CD 中推荐)
    # 将 headless=False 改为 True 为无头模式
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    # --- leaflow执行步骤 ---
    try:
        print("开始执行leaflow签到任务...")
        page.goto("https://leaflow.net/")

        page.get_by_role("button", name="Close").click()
        page.get_by_role("button", name="登录", exact=True).click()
        page.get_by_role("textbox", name="邮箱或手机号").fill(LEAFLOW_EMAIL)
        page.get_by_role("textbox", name="密码").fill(LEAFLOW_PASSWORD)

        page.get_by_role("button", name="登录 / 注册").click()
        print("已完成登录尝试...")

        page.get_by_role("link", name="工作区").click()
        page.get_by_text("签到试用").click()
        print("已进入签到页面...")

        try:
            page.locator("#app iframe").content_frame.locator("form").click()
            print("✅ 任务执行成功: 签到操作已完成。")
        except Exception as e:
            print("✅ 今日已经签到！")

    except Exception as e:
        # 如果在任何步骤失败，包括找不到签到按钮超时，则执行此块
        print("任务执行失败！")
        # 打印原始错误信息用于调试
        print(f"详细错误信息: {e}")
        # 可选：如果失败，保存截图用于调试
        # page.screenshot(path="error_screenshot.png")

    # --- weirdhost执行步骤 ---
    try:
        print("开始执行weirdhost继期任务...")
        # --- 方案一：优先尝试使用 Cookie 会话登录 ---
        if REMEMBER_WEB_COOKIE:
            print("检测到 REMEMBER_WEB_COOKIE，尝试使用 Cookie 登录...")
            session_cookie = {
                'name': 'remember_web_59ba36addc2b2f9401580f014c7f58ea4e30989d',
                'value': REMEMBER_WEB_COOKIE,
                'domain': 'hub.weirdhost.xyz',
                'path': '/',
                'expires': int(time.time()) + 3600 * 24 * 365, # 设置一个较长的过期时间
                'httpOnly': True,
                'secure': True,
                'sameSite': 'Lax'
            }
            page.context.add_cookies([session_cookie])
            print(f"已设置 Cookie。正在访问目标服务器页面: {WEIRDHOST_SERVER_URL}")

            try:
                page.goto(WEIRDHOST_SERVER_URL, wait_until="domcontentloaded", timeout=90000)
            except Exception:
                print(f"页面加载超时（90秒）。")
                # page.screenshot(path="goto_timeout_error.png")
                REMEMBER_WEB_COOKIE = None

            if "login" in page.url or "auth" in page.url:
                print("Cookie 登录失败或会话已过期，将回退到邮箱密码登录。")
                page.context.clear_cookies()
                REMEMBER_WEB_COOKIE = None
            else:
                print("Cookie 登录成功，已进入服务器页面。")

        # --- 方案二：如果 Cookie 方案失败或未提供，则使用邮箱密码登录 ---
        if WEIRDHOST_EMAIL and WEIRDHOST_PASSWORD and not REMEMBER_WEB_COOKIE:
            print("使用EMAIL PASSWORD 开始执行继期任务...")
            page.goto("https://hub.weirdhost.xyz/auth/login")
            page.locator("input[name=\"username\"]").click()
            page.locator("input[name=\"username\"]").fill(WEIRDHOST_EMAIL)
            page.locator("input[name=\"password\"]").click()
            page.locator("input[name=\"password\"]").fill(WEIRDHOST_PASSWORD)
            page.get_by_role("checkbox", name="만14").check()
            page.get_by_role("button", name="로그인", exact=True).click()
            page.goto("https://hub.weirdhost.xyz/")
            print("已进入weirdhost页面...")
            page.goto(WEIRDHOST_SERVER_URL, wait_until="domcontentloaded", timeout=90000)
            print("已进入继期页面...")

        # 检查服务器是否过期，如果过期则继期
        date_element = page.get_by_text(re.compile(r"유통기한\s\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:")).locator('text=유통기한')
        full_text = date_element.inner_text()
        match = re.search(r"(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2})", full_text)
        if match:
            expiration_str = match.group(1)
            # 示例: expiration_str: "2025-10-07 20:38"
            print(f"Found Expiration Date String: {expiration_str}")

            KST = pytz.timezone('Asia/Seoul')
            # 1. 将字符串解析为 Naive datetime
            naive_dt = datetime.strptime(expiration_str, "%Y-%m-%d %H:%M")
            # 2. 将 Naive datetime 转换为 Aware KST datetime (Correct localization)
            expiration_dt = KST.localize(naive_dt)
            # 3. 获取当前的 Aware KST datetime
            now_kst = datetime.now(KST)
            print(f"Now KST time: {now_kst}")

            # 比较两个 datetime 对象
            if expiration_dt > now_kst:
                print("✅ 还未过期，不执行操作")
            else:
                page.get_by_role("button", name="시간추가").click()
                print("✅ 已经成功完成继期。")

    except Exception as e:
        # 如果在任何步骤失败，包括找不到继期按钮超时，则执行此块
        print("任务执行失败！")
        # 打印原始错误信息用于调试
        print(f"详细错误信息: {e}")
        # 可选：如果失败，保存截图用于调试
        # page.screenshot(path="error_screenshot.png")

    finally:
        # ---------------------
        context.close()
        browser.close()

if __name__ == '__main__':
    with sync_playwright() as playwright:
        run(playwright)
