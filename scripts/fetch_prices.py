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
    print(">>> Got", len(raw), "coins")
except Exception as e:
    print(">>> ERROR fetching:", e)
    sys.exit(1)

now = datetime.now(timezone.utc)
updated = now.isoformat()

prices_dict = {}
for c in raw:
    sym = (c.get("symbol") or "").upper()
    if not sym:
        continue
    prices_dict[sym] = {
        "price": c.get("current_price"),
        "change_24h": round(c.get("price_change_percentage_24h") or 0, 2),
        "source": "coingecko",
    }

# === 1. data/latest/prices.json — для analyze_data.py и бота ===
os.makedirs("data/latest", exist_ok=True)
latest = {
    "updated_at": updated,
    "count": len(prices_dict),
    "prices": prices_dict,
}
with open("data/latest/prices.json", "w", encoding="utf-8") as f:
    json.dump(latest, f, ensure_ascii=False, indent=2)
print(">>> WROTE data/latest/prices.json, count:", len(prices_dict))

# === 2. data/history/YYYY-MM-DD.json — история для RSI ===
os.makedirs("data/history", exist_ok=True)
date_str = now.strftime("%Y-%m-%d")
hist_path = os.path.join("data", "history", date_str + ".json")

history = []
if os.path.exists(hist_path):
    try:
        with open(hist_path, encoding="utf-8") as f:
            history = json.load(f)
    except Exception as e:
        print(">>> history load error:", e)
        history = []

history.append({"ts": updated, "data": prices_dict})
history = history[-288:]  # максимум 288 снимков (24ч при 5-мин интервале)

with open(hist_path, "w", encoding="utf-8") as f:
    json.dump(history, f, ensure_ascii=False, indent=2)
print(">>> WROTE", hist_path, "points:", len(history))

# === 3. data/prices.json — плоская копия для бота (опционально) ===
flat = []
for sym, d in prices_dict.items():
    flat.append({
        "symbol": sym,
        "price_usd": d["price"],
        "change_24h": d["change_24h"],
    })
with open("data/prices.json", "w", encoding="utf-8") as f:
    json.dump({
        "updated_at": updated,
        "source": "coingecko",
        "prices": flat,
    }, f, ensure_ascii=False, indent=2)
print(">>> WROTE data/prices.json")

print(">>> fetch_prices.py DONE")