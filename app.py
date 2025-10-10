import re
import os
from playwright.sync_api import Playwright, sync_playwright, expect
import time

def run(playwright: Playwright) -> None:
    # 定义邮箱和密码变量
    LEAFLOW_EMAIL = os.environ.get('LEAFLOW_EMAIL', '')
    LEAFLOW_PASSWORD = os.environ.get('LEAFLOW_PASSWORD', '')

    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://leaflow.net/")

    page.get_by_role("button", name="Close").click()
    page.get_by_role("button", name="登录", exact=True).click()
    page.get_by_role("textbox", name="邮箱或手机号").click()
    page.get_by_role("textbox", name="邮箱或手机号").fill(LEAFLOW_EMAIL)
    page.get_by_role("textbox", name="密码").click()
    page.get_by_role("textbox", name="密码").fill(LEAFLOW_PASSWORD)
    page.get_by_role("button", name="登录 / 注册").click()
    time.sleep(20)
    page.get_by_role("link", name="工作区").click()
    time.sleep(5)
    page.get_by_text("签到试用").click()
    time.sleep(10)
    page.get_by_role("button").filter(has_text="立即签到").click()
    print("任务执行成功")
    # ---------------------
    context.close()
    browser.close()

with sync_playwright() as playwright:
    run(playwright)
