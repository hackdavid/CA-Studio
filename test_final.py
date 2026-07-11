import sys
sys.stdout.reconfigure(encoding='utf-8')

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)

    # Rules page
    context = browser.new_context(viewport={'width': 1440, 'height': 900})
    page = context.new_page()
    page.goto('http://127.0.0.1:8000/rules', wait_until='networkidle')
    page.wait_for_timeout(4000)
    page.screenshot(path='screenshots/rules_final.png')
    result = page.evaluate("""() => ({ allRulesLength: allRules.length })""")
    print(f"Rules page: {result}")
    context.close()

    # Metrics page
    context = browser.new_context(viewport={'width': 1440, 'height': 900})
    page = context.new_page()
    page.goto('http://127.0.0.1:8000/metrics', wait_until='networkidle')
    page.wait_for_timeout(4000)
    page.screenshot(path='screenshots/metrics_final.png')
    result = page.evaluate("""() => ({ allMetricsLength: allMetrics.length })""")
    print(f"Metrics page: {result}")
    context.close()

    # Mobile rules
    context = browser.new_context(viewport={'width': 375, 'height': 812})
    page = context.new_page()
    page.goto('http://127.0.0.1:8000/rules', wait_until='networkidle')
    page.wait_for_timeout(3000)
    page.screenshot(path='screenshots/rules_mobile_final.png')
    context.close()

    browser.close()
    print("All screenshots saved")
