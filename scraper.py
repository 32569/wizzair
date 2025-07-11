# scraper.py
import csv
import datetime
import re
from playwright.sync_api import sync_playwright

# ─── KONFIGŪRACIJA ────────────────────────────────────────────────────────────
ORIGIN      = "VIE"
DEST        = "EVN"
OUT_DATE    = "2025-08-23"
RETURN_DATE = "2025-08-30"
PAX         = 1
# ────────────────────────────────────────────────────────────────────────────

def fetch_price() -> float:
    url = (
        f"https://wizzair.com/en-gb/booking/select-flight/"
        f"{ORIGIN}/{DEST}/{OUT_DATE}/{RETURN_DATE}/{PAX}/0/0/null"
    )

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/115.0.0.0 Safari/537.36"
            )
        )
        # 1) Nuvežame į puslapį, laukiame DOMContentLoaded
        page.goto(url, wait_until="domcontentloaded", timeout=60000)

        # 2) Palaukiame, kad React prisisemtų elementus
        page.wait_for_timeout(5000)

        # 3) Jei iššoko session-expire modalas, paspaudžiam “START A NEW SEARCH”
        if page.locator('text="START A NEW SEARCH"').count() > 0:
            page.click('text="START A NEW SEARCH"')
            page.wait_for_timeout(2000)

        # 4) Dabar ieškom kainos
        if page.locator("div.current-price").count() > 0:
            text = page.inner_text("div.current-price")
        elif page.locator("div.price [data-test]").count() > 0:
            val = page.get_attribute("div.price [data-test]", "data-test")
            text = f"€{val}"
        else:
            browser.close()
            raise RuntimeError("Kainos elemento nerasta puslapyje")

        browser.close()

    # 5) Išvalom tekstą ir paverčiam float’u
    m = re.search(r"[\d.,]+", text)
    if not m:
        raise RuntimeError(f"Negaliu išskaityti kainos iš '{text}'")
    return float(m.group(0).replace(",", ""))

def append_to_csv(date_str: str, price: float):
    # jei CSV dar neegzistuoja – sukuriam su header’iu
    try:
        open("prices.csv", "r").close()
    except FileNotFoundError:
        with open("prices.csv", "w", newline="") as f:
            csv.writer(f).writerow(["date","price"])

    # pridedam eilutę
    with open("prices.csv","a",newline="") as f:
        csv.writer(f).writerow([date_str, f"{price:.2f}"])
    print(f"{date_str} ⇒ €{price:.2f}")

if __name__ == "__main__":
    today = datetime.date.today().isoformat()
    try:
        price = fetch_price()
        append_to_csv(today, price)
    except Exception as e:
        print("ERROR:", e)
        exit(1)
