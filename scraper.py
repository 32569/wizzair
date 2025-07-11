# scraper.py
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
    price_json = None

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/115.0.0.0 Safari/537.36"
            )
        )

        # 1) Intercept'insime visus JSON atsakymus, kurių URL turi "flight-search"
        def handle_response(resp):
            nonlocal price_json
            if "flight-search" in resp.url and "application/json" in (resp.headers.get("content-type") or ""):
                try:
                    j = resp.json()
                except:
                    return
                # raktai gali būti šiek tiek kitokie, bet toks tas pagrindas:
                fg = j.get("pageProps", {})\
                      .get("searchResults", {})\
                      .get("fareGroups", [])
                if fg and fg[0].get("fares"):
                    price_json = fg

        page.on("response", handle_response)

        # 2) Eikime į puslapį
        url = (
            f"https://wizzair.com/en-gb/booking/select-flight/"
            f"{ORIGIN}/{DEST}/{OUT_DATE}/{RETURN_DATE}/{PAX}/0/0/null"
        )
        page.goto(url, wait_until="domcontentloaded", timeout=60000)

        # 3) Palaukiame kelias sekundes, kad XHR’ai suspustųsi
        page.wait_for_timeout(8000)

        browser.close()

    if not price_json:
        raise RuntimeError("Netikėtai nepagauta jokio flight-search JSON")

    # 4) Iš price_json traukiam pirmos grupės pirmą tarifą
    total = price_json[0]["fares"][0]["price"]["total"]
    return float(total)

def append_to_csv(date_str: str, price: float):
    # jei CSV dar neegzistuoja – sukuriam su header’iu
    try:
        open("prices.csv", "r").close()
    except FileNotFoundError:
        with open("prices.csv", "w", newline="") as f:
            csv.writer(f).writerow(["date","price"])

    # pridedam datą+kainą
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
