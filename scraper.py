import csv
import datetime
import requests

# ─── KONFIGŪRACIJA ────────────────────────────────────────────────────────────
ORIGIN      = "VIE"          # IATA kodas išvykimo oro uosto
DEST        = "EVN"          # IATA kodas atvykimo oro uosto
OUT_DATE    = "2025-08-23"   # Išvykimo data YYYY-MM-DD
RETURN_DATE = "2025-08-30"   # Grįžimo data YYYY-MM-DD
PAX_ADULT   = 1
PAX_CHILD   = 0
PAX_INFANT  = 0
CURRENCY    = "EUR"
LANGUAGE    = "en-GB"
# ────────────────────────────────────────────────────────────────────────────

def fetch_price() -> float:
    """
    Kreipiamės į viešą Wizz Air backend API:
      https://be.wizzair.com/<versija>/Api/search/search
    ir gauname JSON su itineraries kainomis.
    """
    url = "https://be.wizzair.com/8.12.2/Api/search/search"
    params = {
        "DepartureStation":        ORIGIN,
        "ArrivalStation":          DEST,
        "DepartureDate":           OUT_DATE,
        "ReturnDate":              RETURN_DATE,
        "AdultCount":              PAX_ADULT,
        "ChildCount":              PAX_CHILD,
        "InfantCount":             PAX_INFANT,
        "IncludeConnectingFlights": False,
        "Currency":                CURRENCY,
        "Language":                LANGUAGE
    }
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/115.0.0.0 Safari/537.36"
        )
    }

    resp = requests.get(url, params=params, headers=headers)
    resp.raise_for_status()
    data = resp.json()

    # Iš HTML inspection (Network → XHR) matau, 
    # kad JSON turi raktą "Itineraries":
    itineraries = data.get("Itineraries") or data.get("SearchResult", {}).get("Itineraries")
    if not itineraries:
        raise RuntimeError("Nepavyko gauti jokių kelionių iš API")

    # Pažeria kelias kainų opcijas, imam pigiausią
    first = itineraries[0]
    # Gali būti raktas "PricingOptions" arba "FareOptionList"
    pricing = first.get("PricingOptions") or first.get("FareOptions")
    if not pricing:
        raise RuntimeError("Nepavyko rasti pricing block JSON'e")

    # Imam pirmą opciją ir jos kainą
    # Dažniausiai: pricing[0]["Price"] arba pricing[0]["TotalPrice"]
    price = pricing[0].get("Price") or pricing[0].get("TotalPrice")
    if price is None:
        raise RuntimeError("Kainos laukas nerastas pricing opcijoje")

    return float(price)

def append_to_csv(date_str: str, price: float):
    # jeigu failas neegzistuoja, sukuriam su headeriu
    try:
        open("prices.csv","r").close()
    except FileNotFoundError:
        with open("prices.csv","w",newline="") as f:
            csv.writer(f).writerow(["date","price"])
    # pridedam naują eilutę
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
