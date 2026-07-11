import sys
sys.stdout.reconfigure(encoding='utf-8')

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1440, 'height': 900})

    page.goto('http://127.0.0.1:8000/rules', wait_until='networkidle')
    page.wait_for_timeout(3000)
    print("Page loaded")

    page.click('button:has-text("Use")')
    page.wait_for_timeout(2000)
    print("Clicked Use")

    modal_visible = page.evaluate("""() => {
        const m = document.getElementById('newSessionModal');
        return m && !m.classList.contains('hidden');
    }""")
    print(f"Modal visible: {modal_visible}")

    trigger_text = page.evaluate("""() => document.getElementById('rule-dropdown-trigger')?.innerText?.substring(0, 50) || 'null'""")
    print(f"Trigger text: {trigger_text}")

    page.screenshot(path='screenshots/modal_simple.png')
    browser.close()
    print("Done")
