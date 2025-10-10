import os
from playwright.sync_api import Playwright, sync_playwright, expect

def run(playwright: Playwright) -> None:
    # 1. 定义邮箱和密码变量
    # 优先从环境变量获取，如果未设置，则使用默认值 (请确保在生产环境中设置环境变量)
    LEAFLOW_EMAIL = os.environ.get('LEAFLOW_EMAIL', '')
    LEAFLOW_PASSWORD = os.environ.get('LEAFLOW_PASSWORD', '')

    # 2. 检查环境变量是否设置 (非常重要!)
    if not LEAFLOW_EMAIL or not LEAFLOW_PASSWORD:
        print("错误: 环境变量 LEAFLOW_EMAIL 或 LEAFLOW_PASSWORD 未设置。")
        return

    # 3. 启用无头模式 (在 CI/CD 中推荐)
    # 将 headless=False 改为 True 在生产环境中运行
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    # --- 执行步骤 ---
    try:
        print("开始执行签到任务...")
        page.goto("https://leaflow.net/")

        # 4. 使用 expect 等待元素出现和操作
        # 等待页面上的 'Close' 按钮出现并点击
        page.get_by_role("button", name="Close").click()
        page.get_by_role("button", name="登录", exact=True).click()
        page.get_by_role("textbox", name="邮箱或手机号").fill(LEAFLOW_EMAIL)
        page.get_by_role("textbox", name="密码").fill(LEAFLOW_PASSWORD)

        # 点击登录/注册，Playwright会自动等待导航完成
        page.get_by_role("button", name="登录 / 注册").click()
        print("已完成登录尝试...")

        # 等待“工作区”链接出现，表示登录成功
        page.get_by_role("link", name="工作区").click()
        # 等待点击后的页面加载，然后点击“签到试用”
        page.get_by_text("签到试用").click()
        print("已进入签到页面...")

        # 使用 frame_locator 查找 iframe 内的按钮 (这是同步 Playwright 推荐的做法)
        # Playwright 会等待元素可见并点击，如果超时则抛出异常
        sign_in_button = page.frame_locator("#app iframe").get_by_role("button", name=" 立即签到")
        sign_in_button.click()

        # 成功点击后，打印最终成功消息
        print("任务执行成功: 签到操作已完成。")

    except Exception as e:
        # 如果在任何步骤失败，包括找不到签到按钮超时，则执行此块
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
