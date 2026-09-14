import requests
import json
import os
import time
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
LATEST_DIR = os.path.join(BASE_DIR, "data", "latest")
HISTORY_DIR = os.path.join(BASE_DIR, "data", "history")

DEFAULT_SYMBOLS = ["BTC", "ETH", "SOL"]

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f).get("crypto_symbols", DEFAULT_SYMBOLS)
        except Exception as e:
            print(f"Config error: {e}")
    return DEFAULT_SYMBOLS

def fetch_binance(symbol):
    pair = symbol + "USDT"
    url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={pair}"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return None
        d = r.json()
        if "lastPrice" in d:
            return {
                "price": float(d["lastPrice"]),
                "change_24h": float(d["priceChangePercent"]),
                "high_24h": float(d["highPrice"]),
                "low_24h": float(d["lowPrice"]),
                "volume": float(d["volume"]),
                "source": "binance"
            }
    except Exception as e:
        print(f"[Binance] {symbol}: {e}")
    return None

def fetch_bybit(symbol):
    pair = symbol + "USDT"
    url = f"https://api.bybit.com/v5/market/tickers?category=spot&symbol={pair}"
    try:
        r = requests.get(url, timeout=10)
        d = r.json()
        if d.get("retCode") == 0 and d.get("result", {}).get("list"):
            t = d["result"]["list"][0]
            price = float(t["lastPrice"])
            prev = float(t.get("prevPrice24h", price))
            change = ((price - prev) / prev * 100) if prev else 0
            return {
                "price": price,
                "change_24h": round(change, 2),
                "high_24h": float(t.get("highPrice24h", price)),
                "low_24h": float(t.get("lowPrice24h", price)),
                "volume": float(t.get("volume24h", 0)),
                "source": "bybit"
            }
    except Exception as e:
        print(f"[Bybit] {symbol}: {e}")
    return None

def fetch_prices(symbols):
    prices = {}
    for symbol in symbols:
        data = fetch_binance(symbol)
        if not data:
            print(f"⚠️ Binance не ответил для {symbol}, пробуем Bybit...")
            data = fetch_bybit(symbol)
        if data:
            prices[symbol] = data
        else:
            print(f"❌ Все источники не дали данные для {symbol}")
        time.sleep(0.15)
    return prices

def save_data(prices):
    os.makedirs(LATEST_DIR, exist_ok=True)
    os.makedirs(HISTORY_DIR, exist_ok=True)
    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S UTC")
    date_str = now.strftime("%Y-%m-%d")
    
    with open(os.path.join(LATEST_DIR, "prices.json"), "w", encoding="utf-8") as f:
        json.dump({"updated_at": timestamp, "count": len(prices), "prices": prices}, f, ensure_ascii=False, indent=2)
    
    history_file = os.path.join(HISTORY_DIR, f"{date_str}.json")
    history = []
    if os.path.exists(history_file):
        try:
            with open(history_file, "r", encoding="utf-8") as f:
                history = json.load(f)
        except: history = []
    
    history.append({"time": timestamp, "data": prices})
    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    
    sources = {}
    for d in prices.values():
        sources[d.get("source", "?")] = sources.get(d.get("source", "?"), 0) + 1
    print(f"✅ Сохранено: {len(prices)} монет. Источники: {sources}. История: {len(history)} записей.")

def main():
    symbols = load_config()
    print(f"Сбор данных: {len(symbols)} монет")
    save_data(fetch_prices(symbols))

if __name__ == "__main__":
    main()