import csv
import datetime
import re
import requests
from bs4 import BeautifulSoup

# ─── KONFIGŪRACIJA ──────────────────────────────────────────────────────────
ORIGIN      = "VIE"          # Kaip VIE (Vienna)
DEST        = "EVN"          # Kaip EVN (Yerevan)
OUT_DATE    = "2025-08-23"   # Išvykimo data
RETURN_DATE = "2025-08-28"   # Grįžimo data (jei tik vienpusis, palik tą patį)
PAX         = 1              # Keleivių skaičius
# ────────────────────────────────────────────────────────────────────────────

def fetch_price():
    # 1) Puslapio URL
    url = (
        f"https://wizzair.com/en-GB/booking/select-flight/"
        f"{ORIGIN}/{DEST}/"
        f"{OUT_DATE}/{RETURN_DATE}/"
        f"{PAX}/0/0/null"
    )
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; FlightPriceBot/1.0)",
        "Accept": "text/html,application/xhtml+xml",
        # Užblokuojame automatinį redirect, kad galėtume rankiniu būdu sekti į wizzair.com (be www)
    }

    # 2) Pirmas GET be redirect
    resp = requests.get(url, headers=headers, allow_redirects=False)
    # jeigu 301/302 -> nueiname į non-www versiją
    if resp.status_code in (301, 302, 307, 308):
        redirect_to = resp.headers.get("Location")
        resp = requests.get(redirect_to, headers=headers)
    resp.raise_for_status()

    # 3) Parsinam HTML ir ieškome <div class="current-price">
    soup = BeautifulSoup(resp.text, "html.parser")
    price_div = soup.find("div", class_="current-price")
    if not price_div:
        raise RuntimeError("Price element not found in HTML")

    text = price_div.get_text(strip=True)  # pvz. "€69.99"
    m = re.search(r"[\d.,]+", text)
    if not m:
        raise RuntimeError(f"Cannot parse number from '{text}'")
    return float(m.group(0).replace(",", ""))

def append_to_csv(date_str, price):
    # jeigu failo nėra – sukuriam su headeriu
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
