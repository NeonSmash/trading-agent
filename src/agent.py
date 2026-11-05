
import os
import requests
from datetime import datetime, timezone


API_KEY = os.environ.get("TWELVE_DATA_API_KEY")
BASE_URL = "https://api.twelvedata.com/time_series"

SYMBOL = "EUR/USD"


def get_market_data(interval):
    params = {
        "symbol": SYMBOL,
        "interval": interval,
        "outputsize": 5,
        "apikey": API_KEY,
        "timezone": "UTC"
    }

    response = requests.get(
        BASE_URL,
        params=params,
        timeout=20
    )

    response.raise_for_status()
    data = response.json()

    if data.get("status") == "error" or "values" not in data:
        raise RuntimeError(
            f"Twelve Data API error: {data}"
        )

    return data["values"]


def main():
    if not API_KEY:
        raise RuntimeError("API key is missing!")

    print("=" * 45)
    print("TRADING AGENT - MARKET DATA")
    print("=" * 45)

    print(f"Execution: {datetime.now(timezone.utc)}")
    print(f"Symbol: {SYMBOL}")

    for interval in ["1h", "15min"]:
        print(f"\n--- {interval} DATA ---")

        candles = get_market_data(interval)

        for candle in reversed(candles):
            print(
                f"Time: {candle['datetime']} | "
                f"O: {candle['open']} | "
                f"H: {candle['high']} | "
                f"L: {candle['low']} | "
                f"C: {candle['close']}"
            )

    print("\nMarket data successfully retrieved.")


if __name__ == "__main__":
    main()
