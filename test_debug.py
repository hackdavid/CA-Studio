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

    # Check if api is defined
    api_defined = page.evaluate("() => typeof api !== 'undefined'")
    print(f"api defined: {api_defined}")

    # Check allRules
    allrules_len = page.evaluate("() => typeof allRules !== 'undefined' ? allRules.length : 'undefined'")
    print(f"allRules length: {allrules_len}")

    # Check if category pills rendered
    pills_html = page.evaluate("() => document.getElementById('category-pills')?.innerHTML || 'null'")
    print(f"category-pills innerHTML (first 200 chars): {pills_html[:200]}")

    # Check network requests
    requests = []
    def handle_route(route, request):
        requests.append(request.url)
        route.continue_()
    page.route("**/*", handle_route)

    # Reload to capture network
    page.reload()
    page.wait_for_load_state('networkidle')
    page.wait_for_timeout(3000)

    api_requests = [r for r in requests if '/api/' in r]
    print(f"API requests made: {api_requests}")

    browser.close()
