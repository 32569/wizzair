import csv
import datetime
import re
import requests
from bs4 import BeautifulSoup

# ─── KONFIGŪRACIJA ────────────────────────────────────────────────────────────
ORIGIN      = "VIE"          # Išvykimo oro uostas
DEST        = "EVN"          # Atvykimo oro uostas
OUT_DATE    = "2025-08-23"   # Išvykimo data YYYY-MM-DD
RETURN_DATE = "2025-08-28"   # Grįžimo data YYYY-MM-DD
PAX         = 1              # Keleivių skaičius
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

    soup = BeautifulSoup(resp.text, "html.parser")
    # pagrindinis bilieto kainos elementas
    price_div = soup.find("div", class_="current-price")
    if not price_div:
        # arba su tėviniu .price bloku
        price_div = soup.select_one("div.price div.current-price")
    if not price_div:
        raise RuntimeError("Price element not found in HTML")

    text = price_div.get_text(strip=True)  # pvz. "€69.99"
    m = re.search(r"[\d.,]+", text)
    if not m:
        raise RuntimeError(f"Cannot parse number from '{text}'")

    # € ženklą ir tūkst. kablelius
    price_str = m.group(0).replace(",", "")
    return float(price_str)

def append_to_csv(date_str, price):
    # jei failas neegzistuoja – sukuriam su header'iu
    try:
        open("prices.csv", "r").close()
    except FileNotFoundError:
        with open("prices.csv", "w", newline="") as f:
            csv.writer(f).writerow(["date", "price"])

    # rašom naują eilutę
    with open("prices.csv", "a", newline="") as f:
        csv.writer(f).writerow([date_str, f"{price:.2f}"])
    print(f"{date_str} ⇒ €{price:.2f}")

if __name__ == "__main__":
    today = datetime.date.today().isoformat()
    try:
        price = fetch_price()
        append_to_csv(today, price)
    except Exception as e:
        print("Error fetching or saving price:", e)
        exit(1)
