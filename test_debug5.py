import sys
sys.stdout.reconfigure(encoding='utf-8')

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={'width': 1440, 'height': 900})
    page = context.new_page()

    page.goto('http://127.0.0.1:8000/rules', wait_until='networkidle')
    page.wait_for_timeout(2000)

    # Try calling initRulesPage manually
    result = page.evaluate("""async () => {
        try {
            if (typeof initRulesPage === 'function') {
                await initRulesPage();
                return { success: true, allRulesLength: allRules.length };
            } else {
                return { success: false, error: 'initRulesPage not defined' };
            }
        } catch (e) {
            return { success: false, error: e.message, stack: e.stack };
        }
    }""")
    print(f"Manual initRulesPage result: {result}")

    # Check if the function was auto-called by checking a global flag
    result2 = page.evaluate("""() => {
        return {
            readyState: document.readyState,
            hasInitRulesPage: typeof initRulesPage !== 'undefined',
            allRulesLength: typeof allRules !== 'undefined' ? allRules.length : 'undefined'
        };
    }""")
    print(f"Page globals: {result2}")

    page.screenshot(path='screenshots/rules_after_manual_init.png')

    browser.close()
