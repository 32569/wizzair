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
        # 1) eikime į puslapį, laukiame network idle
        page.goto(url, wait_until="networkidle")

        # 2) papildomas delay, kad įsijungtų visi JS-popup’ai / dinamika
        page.wait_for_timeout(5000)

        # 3) mėginame rasti div.current-price
        if page.locator("div.current-price").count() > 0:
            text = page.inner_text("div.current-price")
        # 4) arba paimame data-test atributą iš pirmo .price > div
        elif page.locator("div.price [data-test]").count() > 0:
            text = page.get_attribute("div.price [data-test]", "data-test")
            # jei tik skaitom skaičius, uždedam €
            text = "€" + text
        else:
            browser.close()
            raise RuntimeError("Kainos elemento nerasta puslapyje")

        browser.close()

    # parse "€69.99" → 69.99
    m = re.search(r"[\d,.]+", text)
    if not m:
        raise RuntimeError(f"Klaida, negalima išskaityti skaičiaus iš '{text}'")
    return float(m.group(0).replace(",", ""))

def append_to_csv(date_str: str, price: float):
    # jeigu CSV neegzistuoja – sukuriam jį su headeriu
    try:
        open("prices.csv", "r").close()
    except FileNotFoundError:
        with open("prices.csv", "w", newline="") as f:
            csv.writer(f).writerow(["date", "price"])

    # pridedam eilutę
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
