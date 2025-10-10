import os
from playwright.sync_api import Playwright, sync_playwright, expect

def run(playwright: Playwright) -> None:
    # 1. 定义邮箱和密码变量
    LEAFLOW_EMAIL = os.environ.get('LEAFLOW_EMAIL', '')
    LEAFLOW_PASSWORD = os.environ.get('LEAFLOW_PASSWORD', '')

    # 2. 检查环境变量是否设置 (非常重要!)
    if not LEAFLOW_EMAIL or not LEAFLOW_PASSWORD:
        print("错误: 环境变量 LEAFLOW_EMAIL 或 LEAFLOW_PASSWORD 未设置。")
        return

    # 3. 启用无头模式 (在 CI/CD 中推荐)
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    # --- 执行步骤 ---
    try:
        page.goto("https://leaflow.net/")

        # 4. 使用 expect 等待元素出现和操作
        # 等待页面上的 'Close' 按钮出现并点击
        page.get_by_role("button", name="Close").click()

        page.get_by_role("button", name="登录", exact=True).click()

        page.get_by_role("textbox", name="邮箱或手机号").fill(LEAFLOW_EMAIL)
        page.get_by_role("textbox", name="密码").fill(LEAFLOW_PASSWORD)

        # 点击登录/注册，Playwright会自动等待导航完成
        page.get_by_role("button", name="登录 / 注册").click()

        # 等待“工作区”链接出现，表示登录成功
        page.get_by_role("link", name="工作区").click()

        # 等待点击后的页面加载，然后点击“签到试用”
        page.get_by_text("签到试用").click()

        # 等待包含“立即签到”的按钮出现，然后点击
        page.get_by_role("button").filter(has_text="立即签到").click()

        print("任务执行成功: 签到操作已尝试。")

    except Exception as e:
        print(f"任务执行失败: {e}")
        # 可选：如果失败，保存截图用于调试
        # page.screenshot(path="error_screenshot.png")

    finally:
        # ---------------------
        context.close()
        browser.close()

if __name__ == '__main__':
    with sync_playwright() as playwright:
        run(playwright)
