from appium import webdriver
from appium.options.android import UiAutomator2Options
import time

options = UiAutomator2Options()

options.platform_name = "Android"
options.automation_name = "UiAutomator2"
options.device_name = "emulator-5554"

options.app_package = "com.example.android.architecture.blueprints.main"
options.app_activity = "com.example.android.architecture.blueprints.todoapp.TodoActivity"

options.no_reset = True

driver = webdriver.Remote(
    "http://127.0.0.1:4723",
    options=options
)

print("Appium 已成功连接模拟器并启动 App")

time.sleep(5)

driver.quit()

print("测试结束")