
import os
import requests

from datetime import datetime, timezone, timedelta


API_KEY = os.environ.get("TWELVE_DATA_API_KEY")
BASE_URL = "https://api.twelvedata.com/time_series"

SYMBOL = "EUR/USD"


def get_market_data(interval):
    params = {
        "symbol": SYMBOL,
        "interval": interval,
        "outputsize": 250,
        "apikey": API_KEY,
        "timezone": "UTC"
    }

    response = requests.get(
        BASE_URL,
        params=params,
        timeout=30
    )

    response.raise_for_status()
    data = response.json()

    if "values" not in data:
        raise RuntimeError(f"API error: {data}")

    duration = (
        timedelta(hours=1)
        if interval == "1h"
        else timedelta(minutes=15)
    )

    now = datetime.now(timezone.utc)

    candles = []

    for item in data["values"]:
        candle_time = datetime.strptime(
            item["datetime"],
            "%Y-%m-%d %H:%M:%S"
        ).replace(tzinfo=timezone.utc)

        # Only use completed candles
        if candle_time + duration <= now:
            candles.append({
                "time": candle_time,
                "open": float(item["open"]),
                "high": float(item["high"]),
                "low": float(item["low"]),
                "close": float(item["close"])
            })

    candles.sort(key=lambda x: x["time"])

    if len(candles) < 205:
        raise RuntimeError(
            f"Not enough completed candles: {len(candles)}"
        )

    return candles


def calculate_ema(values, period):
    multiplier = 2 / (period + 1)

    ema = sum(values[:period]) / period

    for price in values[period:]:
        ema = (
            price * multiplier
            + ema * (1 - multiplier)
        )

    return ema


def calculate_rsi(values, period=14):
    changes = [
        values[i] - values[i - 1]
        for i in range(1, len(values))
    ]

    gains = [max(change, 0) for change in changes]
    losses = [max(-change, 0) for change in changes]

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    for i in range(period, len(gains)):
        avg_gain = (
            avg_gain * (period - 1) + gains[i]
        ) / period

        avg_loss = (
            avg_loss * (period - 1) + losses[i]
        ) / period

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss

    return 100 - (100 / (1 + rs))


def calculate_macd(values):
    if len(values) < 35:
        raise ValueError("Not enough data for MACD")

    macd_values = []

    for i in range(25, len(values)):
        subset = values[:i + 1]

        ema12 = calculate_ema(subset, 12)
        ema26 = calculate_ema(subset, 26)

        macd_values.append(ema12 - ema26)

    signal = calculate_ema(macd_values, 9)
    macd = macd_values[-1]

    return macd, signal, macd - signal


def analyze_timeframe(interval):
    candles = get_market_data(interval)
    closes = [candle["close"] for candle in candles]

    ema20 = calculate_ema(closes, 20)
    ema50 = calculate_ema(closes, 50)
    ema200 = calculate_ema(closes, 200)

    rsi = calculate_rsi(closes)
    macd, signal, histogram = calculate_macd(closes)

    price = closes[-1]

    print(f"\n========== {interval.upper()} ==========")
    print(f"Last closed candle: {candles[-1]['time']}")
    print(f"Close:       {price:.5f}")
    print(f"EMA 20:      {ema20:.5f}")
    print(f"EMA 50:      {ema50:.5f}")
    print(f"EMA 200:     {ema200:.5f}")
    print(f"RSI 14:      {rsi:.2f}")
    print(f"MACD:        {macd:.6f}")
    print(f"Signal:      {signal:.6f}")
    print(f"Histogram:   {histogram:.6f}")

    return {
        "price": price,
        "ema20": ema20,
        "ema50": ema50,
        "ema200": ema200,
        "rsi": rsi,
        "macd": macd,
        "signal": signal,
        "histogram": histogram
    }


def main():
    if not API_KEY:
        raise RuntimeError("Missing API key")

    print("TRADING AGENT - TECHNICAL ANALYSIS")
    print(f"Execution: {datetime.now(timezone.utc)}")

    h1 = analyze_timeframe("1h")
    m15 = analyze_timeframe("15min")

    print("\n========== ANALYSIS COMPLETE ==========")
    print("H1 and M15 indicators calculated.")
    print("No trades will be executed.")


if __name__ == "__main__":
    main()
