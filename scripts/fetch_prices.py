import requests
import json
import os
from datetime import datetime, timezone

CONFIG_FILE = "config.json"
DATA_DIR = "data"

DEFAULT_SYMBOLS = ["BTC", "ETH", "SOL"]

def load_config():
    """Читает список монет из config.json. Если файла нет, берет дефолтный."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
                return config.get("crypto_symbols", DEFAULT_SYMBOLS)
        except Exception as e:
            print(f"Ошибка чтения config.json: {e}. Используем дефолт.")
            return DEFAULT_SYMBOLS
    return DEFAULT_SYMBOLS

def fetch_prices(symbols):
    """Собирает данные по каждой монете."""
    prices = {}
    for symbol in symbols:
        pair = symbol + "USDT"
        url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={pair}"
        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()  # Проверка на ошибки HTTP (404, 500 и т.д.)
            data = r.json()
            if "lastPrice" in data:
                prices[symbol] = {
                    "price": float(data["lastPrice"]),
                    "change_24h": float(data["priceChangePercent"]),
                    "high_24h": float(data["highPrice"]),
                    "low_24h": float(data["lowPrice"]),
                    "volume": float(data["volume"])
                }
            else:
                print(f"Нет данных по {symbol} (возможно, неверный тикер).")
        except Exception as e:
            print(f"Ошибка при запросе {symbol}: {e}")
    return prices

def save_data(prices):
    """Сохраняет данные в JSON. Обновляет общий файл и пишет в историю за день."""
    os.makedirs(DATA_DIR, exist_ok=True)
    now_utc = datetime.now(timezone.utc)
    timestamp = now_utc.strftime("%Y-%m-%d %H:%M:%S UTC")
    date_str = now_utc.strftime("%Y-%m-%d")

    # 1. Сохраняем "последний снимок" (для быстрого доступа бота)
    latest_output = {
        "updated_at": timestamp,
        "count": len(prices),
        "prices": prices
    }
    with open(f"{DATA_DIR}/prices.json", "w", encoding="utf-8") as f:
        json.dump(latest_output, f, ensure_ascii=False, indent=2)

    # 2. Пишем историю в файл за текущий день (например, data/history_2026-09-14.json)
    history_file = f"{DATA_DIR}/history_{date_str}.json"
    history_data = []
    
    if os.path.exists(history_file):
        try:
            with open(history_file, "r", encoding="utf-8") as f:
                history_data = json.load(f)
        except:
            pass # Если файл битый, начинаем заново
            
    history_data.append({
        "time": timestamp,
        "data": prices
    })
    
    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(history_data, f, ensure_ascii=False, indent=2)
    print(f"Данные сохранены. Снапшот: {len(prices)} монет. История за {date_str}: {len(history_data)} записей.")

def main():
    symbols = load_config()
    print(f"Начинаем сбор: {symbols}")
    prices = fetch_prices(symbols)
    save_data(prices)

if __name__ == "__main__":
    main()