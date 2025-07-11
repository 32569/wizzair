import csv
import datetime
import json
import requests
from bs4 import BeautifulSoup

# ─── KONFIGŪRACIJA ────────────────────────────────────────────────────────────
ORIGIN      = "VIE"          # Išvykimo oro uostas
DEST        = "EVN"          # Atvykimo oro uostas
OUT_DATE    = "2025-08-23"   # Išvykimo data YYYY-MM-DD
RETURN_DATE = "2025-08-28"   # Grįžimo data YYYY-MM-DD (jei tik vienpusis, pakarto OUT_DATE)
PAX         = 1              # Keleivių skaičius
# ────────────────────────────────────────────────────────────────────────────

def fetch_price():
    # 1) Susikuriam URL, kaip matosi adresų juostoje
    url = (
        f"https://wizzair.com/en-GB/booking/select-flight/"
        f"{ORIGIN}/{DEST}/"
        f"{OUT_DATE}/{RETURN_DATE}/"
        f"{PAX}/0/0/null"
    )

    # 2) Tikras browserio User-Agent ir kalba
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

    # 3) Parsinam HTML, surandam __NEXT_DATA__ JSON
    soup   = BeautifulSoup(resp.text, "html.parser")
    script = soup.find("script", id="__NEXT_DATA__")
    if not script or not script.string:
        raise RuntimeError("NEXT_DATA script not found")

    data = json.loads(script.string)

    # 4) Naviguojam iki kainų bloko
    fares = data["props"]["pageProps"]["searchResults"]["fareGroups"]
    if not fares or not fares[0]["fares"]:
        raise RuntimeError("No fares found in JSON")

    total_price = fares[0]["fares"][0]["price"]["total"]
    return float(total_price)

def append_to_csv(date_str, price):
    # Jei CSV neegzistuoja – sukuriam su headeriu
    try:
        open("prices.csv", "r").close()
    except FileNotFoundError:
        with open("prices.csv", "w", newline="") as f:
            csv.writer(f).writerow(["date", "price"])

    # Pridedam naują eilutę
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
