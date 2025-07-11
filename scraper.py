import csv
import datetime
import json
import requests
from bs4 import BeautifulSoup

# ─── KONFIGŪRACIJA ────────────────────────────────────────────────────────────
ORIGIN      = "VIE"          # IŠSILAIPINIMO ORO UOSTAS
DEST        = "EVN"          # ĮSILAIPINIMO ORO UOSTAS
OUT_DATE    = "2025-08-23"   # IŠVYKIMO DATA YYYY-MM-DD
RETURN_DATE = "2025-08-28"   # GRĮŽIMO DATA YYYY-MM-DD (jei tik vienpusis, palik tą pačią)
PAX         = 1              # Keleivių skaičius
# ────────────────────────────────────────────────────────────────────────────

def fetch_price():
    # 1) Kraunam puslapį
    url = (
        f"https://wizzair.com/en-GB/booking/select-flight/"
        f"{ORIGIN}/{DEST}/"
        f"{OUT_DATE}/{RETURN_DATE}/"
        f"{PAX}/0/0/null"
    )
    headers = {
        "User-Agent": "Mozilla/5.0 (FlightPriceBot)",
        "Accept": "text/html,application/xhtml+xml",
    }
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()

    # 2) Ištraukiam React __NEXT_DATA__ JSON (viduje, bet ne rašom į failą)
    soup   = BeautifulSoup(resp.text, "html.parser")
    script = soup.find("script", id="__NEXT_DATA__")
    data   = json.loads(script.string)

    # 3) Naviguojam iki kainų bloko
    fare_groups = data["props"]["pageProps"]["searchResults"]["fareGroups"]

    # 4) Imam pirmos grupės pirmą tarifą
    total_price = fare_groups[0]["fares"][0]["price"]["total"]
    return float(total_price)

def append_to_csv(date_str, price):
    # Sukuria CSV su headeriu, jeigu dar neegzistuoja
    try:
        open("prices.csv", "r").close()
    except FileNotFoundError:
        with open("prices.csv", "w", newline="") as f:
            csv.writer(f).writerow(["date", "price"])

    # Papildo nauja eilute
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
