import sys
sys.stdout.reconfigure(encoding='utf-8')

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1440, 'height': 900})

    # Capture console logs
    console_logs = []
    page.on("console", lambda msg: console_logs.append(f"{msg.type}: {msg.text}"))

    # Rules page
    page.goto('http://127.0.0.1:8000/rules')
    page.wait_for_load_state('networkidle')
    page.wait_for_timeout(4000)
    page.screenshot(path='screenshots/rules_loaded.png')

    # Metrics page
    page.goto('http://127.0.0.1:8000/metrics')
    page.wait_for_load_state('networkidle')
    page.wait_for_timeout(4000)
    page.screenshot(path='screenshots/metrics_loaded.png')

    browser.close()

    print("Screenshots saved")
    if console_logs:
        print("\nConsole logs:")
        for log in console_logs[:30]:
            print(log)
