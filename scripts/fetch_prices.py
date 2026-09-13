import requests
import json
import os
from datetime import datetime, timezone

SYMBOLS = [
    "BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "DOGE",
    "AVAX", "DOT", "MATIC", "LINK", "TRX", "LTC", "SHIB",
    "UNI", "ATOM", "ETC", "XLM", "NEAR", "APT", "ARB"
]

def fetch_prices():
    prices = {}
    for symbol in SYMBOLS:
        pair = symbol + "USDT"
        url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={pair}"
        try:
            r = requests.get(url, timeout=10)
            data = r.json()
            if "lastPrice" in data:
                prices[symbol] = {
                    "price": float(data["lastPrice"]),
                    "change_24h": float(data["priceChangePercent"]),
                    "high_24h": float(data["highPrice"]),
                    "low_24h": float(data["lowPrice"]),
                    "volume": float(data["volume"])
                }
                print(f"OK {symbol}: {prices[symbol]['price']}")
        except Exception as e:
            print(f"ERR {symbol}: {str(e)[:50]}")
    return prices

def main():
    print("Start...")
    prices = fetch_prices()
    output = {
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "count": len(prices),
        "prices": prices
    }
    os.makedirs("data", exist_ok=True)
    with open("data/prices.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(prices)} coins")

if __name__ == "__main__":
    main()
