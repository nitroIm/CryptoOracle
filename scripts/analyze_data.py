import json
import os
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LATEST_DIR = os.path.join(BASE_DIR, "data", "latest")
HISTORY_DIR = os.path.join(BASE_DIR, "data", "history")
ANALYTICS_DIR = os.path.join(BASE_DIR, "data", "analytics")

ANOMALY_THRESHOLD = 3.0  # % за 1 час
RSI_PERIOD = 14

def load_latest():
    path = os.path.join(LATEST_DIR, "prices.json")
    return json.load(open(path, encoding="utf-8")) if os.path.exists(path) else None

def load_history():
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path = os.path.join(HISTORY_DIR, f"{date_str}.json")
    return json.load(open(path, encoding="utf-8")) if os.path.exists(path) else []

def change(current, past):
    if not past: return 0
    return round((current - past) / past * 100, 2)

def calc_rsi(prices, period=RSI_PERIOD):
    if len(prices) < period + 1: return None
    gains = losses = 0
    for i in range(1, period + 1):
        diff = prices[-i] - prices[-i - 1]
        if diff > 0: gains += diff
        else: losses -= diff
    if losses == 0: return 100
    rs = gains / losses
    return round(100 - (100 / (1 + rs)), 2)

def make_signal(rsi, change_1h, change_24h):
    if rsi is None: return "NO_DATA"
    if rsi >= 70: return "OVERBOUGHT"
    if rsi <= 30: return "OVERSOLD"
    if change_1h >= 2: return "PUMP"
    if change_1h <= -2: return "DUMP"
    if change_24h >= 5: return "BULLISH"
    if change_24h <= -5: return "BEARISH"
    return "NEUTRAL"

def analyze():
    latest = load_latest()
    if not latest:
        print("Нет данных"); return
    history = load_history()
    print(f"Анализ: {len(history)} точек, {latest['count']} монет")
    
    result = {"generated_at": latest["updated_at"], "analysis": {}}
    
    for symbol, data in latest["prices"].items():
        current = data["price"]
        ph = [p["data"][symbol]["price"] for p in history if symbol in p.get("data", {})]
        
        change_1h = change(current, ph[-5]) if len(ph) >= 5 else 0
        rsi = calc_rsi(ph)
        anomaly = abs(change_1h) >= ANOMALY_THRESHOLD
        signal = make_signal(rsi, change_1h, data["change_24h"])
        
        result["analysis"][symbol] = {
            "price": current,
            "change_24h": data["change_24h"],
            "change_1h": change_1h,
            "rsi": rsi,
            "signal": signal,
            "anomaly": anomaly,
            "source": data.get("source", "?")
        }
    
    os.makedirs(ANALYTICS_DIR, exist_ok=True)
    with open(os.path.join(ANALYTICS_DIR, "signals.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    anomalies = [s for s, d in result["analysis"].items() if d["anomaly"]]
    pumps = [s for s, d in result["analysis"].items() if d["signal"] == "PUMP"]
    dumps = [s for s, d in result["analysis"].items() if d["signal"] == "DUMP"]
    
    print(f"✅ Анализ готов")
    if anomalies: print(f"⚠️  Аномалии: {', '.join(anomalies)}")
    if pumps: print(f"🚀 Pump: {', '.join(pumps)}")
    if dumps: print(f"💥 Dump: {', '.join(dumps)}")

if __name__ == "__main__":
    analyze()