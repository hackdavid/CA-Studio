import sys
sys.stdout.reconfigure(encoding='utf-8')

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={'width': 1440, 'height': 900})
    page = context.new_page()

    # Hard reload rules page
    page.goto('http://127.0.0.1:8000/rules', wait_until='networkidle')
    page.reload(wait_until='networkidle')
    page.wait_for_timeout(4000)

    # Check if data loaded
    result = page.evaluate("""() => {
        return {
            allRulesLength: typeof allRules !== 'undefined' ? allRules.length : 'undefined',
            categoryPills: document.getElementById('category-pills')?.innerText?.substring(0, 100) || 'null',
            rulesGrid: document.getElementById('rules-grid')?.innerText?.substring(0, 100) || 'null'
        };
    }""")
    print(f"Rules page state: {result}")

    # Screenshot
    page.screenshot(path='screenshots/rules_hard_reload.png')

    # Hard reload metrics page
    page.goto('http://127.0.0.1:8000/metrics', wait_until='networkidle')
    page.reload(wait_until='networkidle')
    page.wait_for_timeout(4000)

    result2 = page.evaluate("""() => {
        return {
            allMetricsLength: typeof allMetrics !== 'undefined' ? allMetrics.length : 'undefined',
            typePills: document.getElementById('type-pills')?.innerText?.substring(0, 100) || 'null',
            metricsList: document.getElementById('metrics-list')?.innerText?.substring(0, 100) || 'null'
        };
    }""")
    print(f"Metrics page state: {result2}")

    page.screenshot(path='screenshots/metrics_hard_reload.png')

    browser.close()
