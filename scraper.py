import csv
import datetime
import requests

# 1) Konfigūracija – pakeisk ORIGIN, DEST, DATE pagal savo maršrutą
ORIGIN = "VIE"         # Vienna
DEST   = "EVN"         # Yerevan
DATE   = "2025-08-23"  # flight date in YYYY-MM-DD

def fetch_price():
    """
    Čia turi įrašyti tą URL, kurį matai naršyklės Network skiltyje,
    kai puslapis kraunasi. Dažnai būna JSON API kaip:
      https://wizzair.com/_next/data/.../en-GB/flight-search?departureStation=VIE&arrivalStation=EVN&departureDate=2025-08-23&ADT=1
    """
    url = (
        "https://wizzair.com/_next/data/abcd1234/en-GB/flight-search"
        f"?departureStation={ORIGIN}"
        f"&arrivalStation={DEST}"
        f"&departureDate={DATE}"
        "&ADT=1"
    )

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; FlightPriceBot/1.0)",
        "Accept": "application/json"
    }

    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    data = resp.json()

    # 2) Priklausomai nuo JSON struktūros – rask, kur saugoma kaina.
    #    Pvz., kartais tai:
    #      data["pageProps"]["results"]["fares"][0]["price"]["total"]
    #    Žemiau – tik pavyzdys, pakeisk pagal tikrą struktūrą.
    price = data["pageProps"]["results"]["fares"][0]["price"]["total"]

    return float(price)

def append_to_csv(date_str, price):
    file_exists = False
    try:
        with open("prices.csv", "r", newline="") as f:
            file_exists = True
    except FileNotFoundError:
        file_exists = False

    with open("prices.csv", "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["date", "price"])
        writer.writerow([date_str, f"{price:.2f}"])
    print(f"Recorded: {date_str}, €{price:.2f}")

if __name__ == "__main__":
    today = datetime.date.today().isoformat()
    try:
        price = fetch_price()
        append_to_csv(today, price)
    except Exception as e:
        print("Error fetching or saving price:", e)
        exit(1)
