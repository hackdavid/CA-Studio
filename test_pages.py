from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1440, 'height': 900})

    # Rules page
    page.goto('http://127.0.0.1:8000/rules')
    page.wait_for_load_state('networkidle')
    page.wait_for_timeout(2500)
    page.screenshot(path='screenshots/rules_page.png')

    # Metrics page
    page.goto('http://127.0.0.1:8000/metrics')
    page.wait_for_load_state('networkidle')
    page.wait_for_timeout(2500)
    page.screenshot(path='screenshots/metrics_page.png')

    # Mobile rules
    page.set_viewport_size({'width': 375, 'height': 812})
    page.goto('http://127.0.0.1:8000/rules')
    page.wait_for_timeout(2000)
    page.screenshot(path='screenshots/rules_mobile.png')

    browser.close()
    print("Screenshots saved")
