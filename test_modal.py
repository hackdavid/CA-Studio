import sys
sys.stdout.reconfigure(encoding='utf-8')

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={'width': 1440, 'height': 900})
    page = context.new_page()

    # Test 1: Rules page — click "Use" on Conway rule
    page.goto('http://127.0.0.1:8000/rules', wait_until='networkidle')
    page.wait_for_timeout(3000)
    page.click('button:has-text("Use")')
    page.wait_for_timeout(2000)

    # Check modal is open
    modal_visible = page.evaluate("""() => {
        const m = document.getElementById('newSessionModal');
        return m && !m.classList.contains('hidden');
    }""")
    print(f"1. Modal open after Use: {modal_visible}")

    # Check rule trigger shows selected rule
    trigger_text = page.evaluate("""() => document.getElementById('rule-dropdown-trigger')?.innerText?.substring(0, 50) || 'null'""")
    print(f"2. Rule trigger text: {trigger_text}")

    # Check preview panel has content
    preview_html = page.evaluate("""() => document.getElementById('preview-panel')?.innerHTML?.substring(0, 100) || 'empty'""")
    print(f"3. Preview panel: {preview_html}")

    page.screenshot(path='screenshots/modal_use_rule.png')

    # Test 2: Close modal, click New Session from sidebar
    page.click('button:has-text("Cancel")')
    page.wait_for_timeout(500)
    page.click('button:has-text("New Session")')
    page.wait_for_timeout(2000)

    # Check empty preview
    empty_visible = page.evaluate("""() => {
        const e = document.getElementById('preview-empty');
        return e && !e.classList.contains('hidden');
    }""")
    print(f"4. Empty preview on fresh modal: {empty_visible}")

    # Test rule dropdown search
    page.click('#rule-dropdown-trigger')
    page.wait_for_timeout(300)
    page.fill('#dropdown-rule-search', 'Conway')
    page.wait_for_timeout(500)
    dropdown_items = page.evaluate("""() => {
        return Array.from(document.querySelectorAll('#rule-dropdown-list .dropdown-item')).map(el => el.innerText.substring(0, 50));
    }""")
    print(f"5. Dropdown filtered items: {dropdown_items}")

    # Click first item in dropdown
    page.click('#rule-dropdown-list .dropdown-item')
    page.wait_for_timeout(500)

    # Check trigger updated
    trigger_text2 = page.evaluate("""() => document.getElementById('rule-dropdown-trigger')?.innerText?.substring(0, 50) || 'null'""")
    print(f"6. Rule trigger after selection: {trigger_text2}")

    # Check preview updated
    preview_html2 = page.evaluate("""() => document.getElementById('preview-panel')?.innerHTML?.substring(0, 100) || 'empty'""")
    print(f"7. Preview after selection: {preview_html2}")

    page.screenshot(path='screenshots/modal_dropdown_select.png')

    # Test metric dropdown
    page.click('#metric-dropdown-trigger')
    page.wait_for_timeout(300)
    metric_items = page.evaluate("""() => {
        return Array.from(document.querySelectorAll('#metric-dropdown-list label')).length;
    }""")
    print(f"8. Metric dropdown items: {metric_items}")

    # Uncheck first metric
    page.click('#metric-dropdown-list input[type="checkbox"]')
    page.wait_for_timeout(300)

    # Close metric dropdown by clicking outside (on session name)
    page.click('#session-name-input')
    page.wait_for_timeout(300)

    # Check trigger shows count
    metric_trigger = page.evaluate("""() => document.getElementById('metric-dropdown-trigger')?.innerText?.substring(0, 50) || 'null'""")
    print(f"9. Metric trigger after uncheck: {metric_trigger}")

    page.screenshot(path='screenshots/modal_metrics.png')

    # Test 3: Create session
    page.fill('#session-name-input', 'Test Modal Session')
    page.click('button:has-text("Launch Session")')
    page.wait_for_timeout(3000)

    url = page.url
    print(f"10. URL after launch: {url}")
    success = '/simulation/' in url
    print(f"11. Redirected to simulation: {success}")

    browser.close()
    print("\nAll tests complete")
