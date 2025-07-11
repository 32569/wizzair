import re
import csv
import datetime
import requests

# ─── KONFIGŪRACIJA ────────────────────────────────────────────────────────────
ORIGIN      = "VIE"
DEST        = "EVN"
OUT_DATE    = "2025-08-23"
RETURN_DATE = "2025-08-28"
PAX         = 1
# ────────────────────────────────────────────────────────────────────────────

def fetch_price():
    url = (
        f"https://wizzair.com/en-GB/booking/select-flight/"
        f"{ORIGIN}/{DEST}/"
        f"{OUT_DATE}/{RETURN_DATE}/"
        f"{PAX}/0/0/null"
    )
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/115.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-GB,en;q=0.9"
    }
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    html = resp.text

    # Regex: ieškome <div … class="current-price">€69.99</div>
    m = re.search(
        r'<div[^>]*class="current-price"[^>]*>€\s*([\d.,]+)</div>',
        html
    )
    if not m:
        raise RuntimeError("Kainos elemento nerasta HTML")
    # Pašalinam tūkst. kablelius:
    price = float(m.group(1).replace(",", ""))
    return price

def append_to_csv(date_str, price):
    # jei CSV neegzistuoja – sukuriam su headeriu
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
        print("Klaida:", e)
        exit(1)
