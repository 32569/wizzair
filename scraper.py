import csv
import datetime
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
        f"https://wizzair.com/en-GB/booking/select-flight/"
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
        page.goto(url)
        # palaukiam, kol atsiras “Select” mygtukas ir kaina
        page.wait_for_selector("div.current-price", timeout=15000)
        price_text = page.inner_text("div.current-price")
        browser.close()

    # išvalom, pavyzdžiui "€69.99"
    return float(price_text.replace("€", "").replace(",", "").strip())

def append_to_csv(date_str: str, price: float):
    # jei failo dar nėra – sukuriam header'į
    try:
        open("prices.csv", "r").close()
    except FileNotFoundError:
        with open("prices.csv", "w", newline="") as f:
            csv.writer(f).writerow(["date", "price"])
    # pridedam naują eilutę
    with open("prices.csv", "a", newline="") as f:
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
