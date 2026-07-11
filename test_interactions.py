import sys
sys.stdout.reconfigure(encoding='utf-8')

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={'width': 1440, 'height': 900})
    page = context.new_page()

    # Test Rules page interactions
    page.goto('http://127.0.0.1:8000/rules', wait_until='networkidle')
    page.wait_for_timeout(3000)

    # Test search
    page.fill('#rule-search', 'Conway')
    page.wait_for_timeout(1000)
    visible_rules = page.evaluate("""() => {
        const cards = document.querySelectorAll('#rules-grid > div');
        return Array.from(cards).map(c => c.innerText).filter(t => t.includes('Conway') || t.includes('No rules'));
    }""")
    print(f"Search 'Conway' results: {visible_rules}")

    # Test "Use" button on Conway rule
    page.fill('#rule-search', '')
    page.wait_for_timeout(500)
    page.click('button:has-text("Use")')
    page.wait_for_timeout(1500)

    # Check if New Session modal is open and Conway is pre-selected
    modal_visible = page.evaluate("""() => {
        const modal = document.getElementById('newSessionModal');
        return modal && !modal.classList.contains('hidden');
    }""")
    print(f"New Session modal visible: {modal_visible}")

    selected_rule = page.evaluate("""() => {
        const selected = document.querySelector('#modal-rule-list .rule-option.bg-primary-50');
        return selected ? selected.innerText.substring(0, 50) : 'none';
    }""")
    print(f"Pre-selected rule: {selected_rule}")

    page.screenshot(path='screenshots/rules_use_modal.png')

    # Close modal
    page.click('button:has-text("Cancel")')
    page.wait_for_timeout(500)

    # Test Metrics page search
    page.goto('http://127.0.0.1:8000/metrics', wait_until='networkidle')
    page.wait_for_timeout(3000)
    page.fill('#metric-search', 'entropy')
    page.wait_for_timeout(1000)
    visible_metrics = page.evaluate("""() => {
        const cards = document.querySelectorAll('#metrics-list > div');
        return Array.from(cards).map(c => c.innerText).filter(t => t.includes('entropy') || t.includes('No metrics'));
    }""")
    print(f"Search 'entropy' results: {visible_metrics}")

    page.screenshot(path='screenshots/metrics_search.png')

    browser.close()
    print("Interaction tests complete")
