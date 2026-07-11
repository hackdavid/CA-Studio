import sys
sys.stdout.reconfigure(encoding='utf-8')

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1440, 'height': 900})

    # Rules page
    page.goto('http://127.0.0.1:8000/rules')
    page.wait_for_load_state('networkidle')
    page.wait_for_timeout(3000)

    # Try calling api.get manually
    result = page.evaluate("""async () => {
        try {
            const rules = await api.get('/api/rules/');
            return { success: true, count: rules.length };
        } catch (e) {
            return { success: false, error: e.message };
        }
    }""")
    print(f"Manual api.get result: {result}")

    # Check if loadRulesPage exists and call it
    result2 = page.evaluate("""async () => {
        try {
            await loadRulesPage();
            return { success: true, allRulesLength: allRules.length };
        } catch (e) {
            return { success: false, error: e.message, stack: e.stack };
        }
    }""")
    print(f"Manual loadRulesPage result: {result2}")

    browser.close()
