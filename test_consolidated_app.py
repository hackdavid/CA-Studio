"""Test script to verify consolidated CA Lab application."""

import requests
import sys


def test_endpoint(url: str, description: str) -> bool:
    """Test if an endpoint is accessible."""
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print(f"[OK] {description}: {url}")
            return True
        else:
            print(f"[FAIL] {description}: {url} (Status: {response.status_code})")
            return False
    except requests.exceptions.ConnectionError:
        print(f"[FAIL] {description}: {url} (Server not running)")
        return False
    except Exception as e:
        print(f"[FAIL] {description}: {url} (Error: {e})")
        return False


def main():
    """Run all tests."""
    print("=" * 70)
    print("CA Lab - Consolidated Application Test")
    print("=" * 70)
    print()

    base_url = "http://127.0.0.1:8000"

    # Check if server is running
    print("Checking if server is running...")
    if not test_endpoint(f"{base_url}/health", "Health check"):
        print()
        print("[ERROR] Server is not running!")
        print()
        print("Start the server with:")
        print("  python start.py")
        print()
        return 1

    print()
    print("Testing page routes (clean URLs)...")
    tests = [
        (f"{base_url}/", "Root redirect"),
        (f"{base_url}/landing", "Landing page"),
        (f"{base_url}/dashboard", "Dashboard"),
        (f"{base_url}/simulation", "Simulation page"),
    ]

    page_results = [test_endpoint(url, desc) for url, desc in tests]

    print()
    print("Testing API endpoints...")
    api_tests = [
        (f"{base_url}/api/rules", "Rules API"),
        (f"{base_url}/api/sessions", "Sessions API"),
        (f"{base_url}/api/docs", "API Documentation"),
        (f"{base_url}/api/info", "API Info"),
    ]

    api_results = [test_endpoint(url, desc) for url, desc in api_tests]

    print()
    print("=" * 70)
    print("Summary")
    print("=" * 70)

    total_tests = len(page_results) + len(api_results)
    passed_tests = sum(page_results) + sum(api_results)

    print(f"Tests passed: {passed_tests}/{total_tests}")
    print()

    if passed_tests == total_tests:
        print("[SUCCESS] All tests passed!")
        print()
        print("Your CA Lab application is working correctly!")
        print()
        print("Access the application:")
        print(f"  Landing:    {base_url}/landing")
        print(f"  Dashboard:  {base_url}/dashboard")
        print(f"  Simulation: {base_url}/simulation")
        print(f"  API Docs:   {base_url}/api/docs")
        print()
        return 0
    else:
        print("[ERROR] Some tests failed!")
        print()
        print("Please check the server logs and ensure:")
        print("  1. Server is running (python start.py)")
        print("  2. No errors in terminal output")
        print("  3. Database is initialized (ca_lab.db exists)")
        print()
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
