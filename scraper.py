import re
import csv
import datetime
import requests

# ─── KONFIGŪRACIJA ────────────────────────────────────────────────────────────
ORIGIN      = "VIE"          # išvykimo kodas
DEST        = "EVN"          # atvykimo kodas
OUT_DATE    = "2025-08-23"   # YYYY-MM-DD
RETURN_DATE = "2025-08-30"   # YYYY-MM-DD
PAX         = 1              # keleivių skaičius
# ────────────────────────────────────────────────────────────────────────────

def get_build_id(html: str) -> str:
    # 1) ieškome JSON endpoint matomos nuorodos
    m = re.search(r'/_next/data/([^/]+)/en-GB/flight-search', html)
    if m:
        return m.group(1)
    # 2) fallback į SSG manifest
    m = re.search(r'/_next/static/([^/]+)/_ssgManifest\.js', html)
    if m:
        return m.group(1)
    # 3) fallback į build manifest
    m = re.search(r'/_next/static/([^/]+)/_buildManifest\.js', html)
    if m:
        return m.group(1)
    raise RuntimeError("NEXT buildId nerastas")

def fetch_price() -> float:
    # 1) Nusikrauname initial HTML (redirects=TRUE)
    url_html = (
        f"https://wizzair.com/en-GB/booking/select-flight/"
        f"{ORIGIN}/{DEST}/{OUT_DATE}/{RETURN_DATE}/{PAX}/0/0/null"
    )
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/115.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-GB,en;q=0.9"
    }
    resp_html = requests.get(url_html, headers=headers, allow_redirects=True)
    resp_html.raise_for_status()

    build_id = get_build_id(resp_html.text)

    # 2) JSON su kainomis
    url_json = (
        f"https://wizzair.com/_next/data/{build_id}/en-GB/flight-search"
        f"?departureStation={ORIGIN}"
        f"&arrivalStation={DEST}"
        f"&departureDate={OUT_DATE}"
        f"&ADT={PAX}"
    )
    resp_json = requests.get(url_json, headers={**headers, "Accept": "application/json"})
    resp_json.raise_for_status()
    data = resp_json.json()

    # 3) pirmos grupės pirmo fare kaina
    fg = data["pageProps"]["searchResults"]["fareGroups"]
    if not fg or not fg[0]["fares"]:
        raise RuntimeError("Nėra tarifų JSON’e")
    return float(fg[0]["fares"][0]["price"]["total"])

def append_to_csv(date_str: str, price: float):
    # CSV su header jei dar nėra
    try:
        open("prices.csv","r").close()
    except FileNotFoundError:
        with open("prices.csv","w",newline="") as f:
            csv.writer(f).writerow(["date","price"])

    # pridedam eilutę
    with open("prices.csv","a",newline="") as f:
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
