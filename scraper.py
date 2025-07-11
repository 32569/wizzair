import re
import csv
import datetime
import requests

# ─── KONFIGŪRACIJA ────────────────────────────────────────────────────────────
ORIGIN      = "VIE"          # Išvykimo (departure) oro uostas
DEST        = "EVN"          # Atvykimo (arrival) oro uostas
OUT_DATE    = "2025-08-23"   # Išvykimo data YYYY-MM-DD
RETURN_DATE = "2025-08-30"   # Grįžimo data YYYY-MM-DD
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
    html = resp.text

    # IEŠKOME data-test="69.99" (ten visada bus serverio‐pateikta kaina)
    m = re.search(r'data-test="([\d\.,]+)"', html)
    if not m:
        # jei norime dar pažiūrėti visą resp.text, galima:
        # print(html); exit(1)
        raise RuntimeError("Kainos elemento nerasta HTML (data-test).")

    # Iš duoto string'o išvalom tūkst. kablelius
    price = float(m.group(1).replace(",", ""))
    return price

def append_to_csv(date_str, price):
    # jei dar nėra – sukuriam CSV su header'iu
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
        print("Klaida:", e)
        exit(1)
