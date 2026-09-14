import json
import os
import sys
import urllib.request
from datetime import datetime, timezone

print(">>> fetch_prices.py START")
print(">>> CWD:", os.getcwd())

COINS = ["bitcoin", "ethereum", "toncoin", "solana", "binancecoin"]
URL = (
    "https://api.coingecko.com/api/v3/coins/markets"
    "?vs_currency=usd&ids=" + ",".join(COINS) +
    "&order=market_cap_desc&price_change_percentage=24h"
)

try:
    req = urllib.request.Request(URL, headers={"User-Agent": "CryptoOracle/1.0"})
    with urllib.request.urlopen(req, timeout=25) as r:
        raw = json.loads(r.read().decode())
    print(">>> Got", len(raw), "coins from CoinGecko")
except Exception as e:
    print(">>> ERROR fetching:", e)
    sys.exit(1)

prices = []
for c in raw:
    prices.append({
        "symbol": (c.get("symbol") or "").upper(),
        "name": c.get("name"),
        "price_usd": c.get("current_price"),
        "change_24h": c.get("price_change_percentage_24h"),
        "market_cap": c.get("market_cap"),
    })

out = {
    "updated_at": datetime.now(timezone.utc).isoformat(),
    "source": "coingecko",
    "prices": prices,
}

os.makedirs("data", exist_ok=True)
path = os.path.join("data", "prices.json")
with open(path, "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2, ensure_ascii=False)

print(">>> WROTE:", path, "size:", os.path.getsize(path), "bytes")
print(">>> exists:", os.path.exists(path))
print(">>> fetch_prices.py DONE")