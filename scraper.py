import csv
import datetime
import json
import re
import requests
from bs4 import BeautifulSoup

# ─── KONFIGŪRACIJA ────────────────────────────────────────────────────────────
ORIGIN      = "VIE"          # išvykimo oro uostas
DEST        = "EVN"          # atvykimo oro uostas
OUT_DATE    = "2025-08-23"   # yyyy-mm-dd
RETURN_DATE = "2025-08-30"   # yyyy-mm-dd (jei vienpusis, pakarto OUT_DATE)
PAX         = 1              # keleivių skaičius
# ────────────────────────────────────────────────────────────────────────────

def get_build_id(html: str) -> str:
    """
    Iš HTML ištraukia Next.js buildId, reikalingą JSON endpoint URL sudarymui.
    """
    m = re.search(r'/_next/static/([^/]+)/_buildManifest\.js', html)
    if not m:
        raise RuntimeError("NEXT buildId nerastas")
    return m.group(1)

def fetch_price() -> float:
    # 1) Pirmas GET – nusikrauname puslapį, kad sužinotume buildId
    url_html = (
        f"https://wizzair.com/en-GB/booking/select-flight/"
        f"{ORIGIN}/{DEST}/{OUT_DATE}/{RETURN_DATE}/{PAX}/0/0/null"
    )
    headers_html = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/115.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-GB,en;q=0.9",
    }
    resp_html = requests.get(url_html, headers=headers_html)
    resp_html.raise_for_status()

    build_id = get_build_id(resp_html.text)

    # 2) Antras GET – JSON endpoint'as su kainomis
    url_json = (
        f"https://wizzair.com/_next/data/{build_id}/en-GB/flight-search"
        f"?departureStation={ORIGIN}"
        f"&arrivalStation={DEST}"
        f"&departureDate={OUT_DATE}"
        f"&ADT={PAX}"
    )
    headers_json = {
        "User-Agent": headers_html["User-Agent"],
        "Accept": "application/json"
    }
    resp_json = requests.get(url_json, headers=headers_json)
    resp_json.raise_for_status()
    data = resp_json.json()

    # 3) Iš JSON ištraukiam pirmos grupės pirmą fare total
    fg = data["pageProps"]["searchResults"]["fareGroups"]
    if not fg or not fg[0]["fares"]:
        raise RuntimeError("Nerasta jokių tarifų JSON’e")
    price = fg[0]["fares"][0]["price"]["total"]
    return float(price)

def append_to_csv(date_str: str, price: float):
    # jei dar nėra – sukuriam su header'iu
    try:
        open("prices.csv", "r").close()
    except FileNotFoundError:
        with open("prices.csv", "w", newline="") as f:
            csv.writer(f).writerow(["date", "price"])

    # papildom nauja eilute
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
