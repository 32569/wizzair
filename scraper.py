import csv
import datetime
import requests

# 1) Nustatome užklausos parametrus
ORIGIN = "VIE"       # Vienna
DEST   = "EVN"       # Yerevan
DATE   = "2025-08-23"

# 2) Išsiaiškini per Developer Tools, kokiu URL WizzAir siunčia užklausą kainai gauti.
#    Dažnai jie naudoja viešą JSON API – tarkim:
url = f"https://wizzair.com/_next/data/.../en-GB/flight-search?departureStation={ORIGIN}&arrivalStation={DEST}&departureDate={DATE}&ADT=1"

# 3) Atlieki užklausą
resp = requests.get(url)
data = resp.json()

# 4) Išrenki kainą (žr. JSON struktūrą – čia tik pavyzdys)
price = data["price"]["total"]   # ar panašiai

# 5) Įrašai į CSV (jei dar neturi – susikuri antrą eilutę su header‘iais)
today = datetime.date.today().isoformat()
with open("prices.csv", "a", newline="") as f:
    writer = csv.writer(f)
    writer.writerow([today, price])
print(f"{today} → €{price}")
