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

        page.get_by_role("button", name="登录 / 注册").click()

        # Playwright会等待工作区链接出现后才点击
        page.get_by_role("link", name="工作区").click()

        # Playwright会等待签到试用文本可见后才点击
        page.get_by_text("签到试用").click()

        # Playwright会等待包含“立即签到”的按钮出现（最多 30s）才点击
        # 如果您确定该按钮加载慢，可以增加超时时间，但通常 Playwright 默认的 30s 足够
        try:
            page.locator("div").filter(has_text=re.compile(r"^签到$")).nth(1).click()
            page.get_by_text("立即签到", exact=True).click()
            # page.get_by_role("button").filter(has_text="立即签到").click(timeout=45000) # 延长到 45 秒
            print("任务执行成功: 立即签到已尝试点击。")

        except Exception as e:
            # 如果再次失败，打印出错误，并尝试截图以供调试
            print(f"任务执行失败: 签到按钮点击超时。{e}")
            # 在 GitHub Actions 运行结束后，您可以下载 artifacts 查看这张截图
            page.screenshot(path="failed_sign_in.png")

    finally:
        # ---------------------
        context.close()
        browser.close()

if __name__ == '__main__':
    with sync_playwright() as playwright:
        run(playwright)
