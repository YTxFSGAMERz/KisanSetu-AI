import os
import time
from playwright.sync_api import sync_playwright

def main():
    out_dir = r"C:\Users\Admin\.gemini\antigravity\brain\87793f70-d8f5-48df-9246-a03ae8283b2e\test_screenshots"
    os.makedirs(out_dir, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        page = context.new_page()

        print("1. Opening login page...")
        page.goto("http://localhost:3000/login", wait_until="networkidle")
        page.wait_for_timeout(1000)

        print("2. Clicking Farmer Demo button...")
        farmer_btn = page.locator("button:has-text('Farmer')").first
        farmer_btn.click()
        page.wait_for_url("**/farmer**", timeout=10000)
        page.wait_for_timeout(2500)

        print("3. Capturing Farmer Dashboard...")
        dash_screenshot = os.path.join(out_dir, "verified_farmer_dashboard.png")
        page.screenshot(path=dash_screenshot, full_page=True)
        print(f"✅ Dashboard saved: {dash_screenshot}")

        print("4. Navigating to Procurements...")
        page.goto("http://localhost:3000/farmer/procurements", wait_until="networkidle")
        page.wait_for_timeout(2000)
        proc_screenshot = os.path.join(out_dir, "verified_procurements.png")
        page.screenshot(path=proc_screenshot, full_page=True)
        print(f"✅ Procurements saved: {proc_screenshot}")

        print("5. Navigating to Payments...")
        page.goto("http://localhost:3000/farmer/payments", wait_until="networkidle")
        page.wait_for_timeout(2000)
        pay_screenshot = os.path.join(out_dir, "verified_payments.png")
        page.screenshot(path=pay_screenshot, full_page=True)
        print(f"✅ Payments saved: {pay_screenshot}")

        browser.close()
        print("🎉 Verification completed!")

if __name__ == "__main__":
    main()
