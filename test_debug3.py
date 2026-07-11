import sys
sys.stdout.reconfigure(encoding='utf-8')

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1440, 'height': 900})

    page.goto('http://127.0.0.1:8000/rules')
    page.wait_for_load_state('networkidle')
    page.wait_for_timeout(3000)

    ready_state = page.evaluate("() => document.readyState")
    print(f"readyState after 3s: {ready_state}")

    # Check if DOMContentLoaded already fired
    result = page.evaluate("""() => {
        let fired = false;
        const check = () => { fired = true; };
        document.addEventListener('DOMContentLoaded', check);
        // If we add the listener after DOMContentLoaded, it won't fire again
        // So check readyState
        return { readyState: document.readyState, hasLoadRulesPage: typeof loadRulesPage };
    }""")
    print(f"Page state: {result}")

    browser.close()
