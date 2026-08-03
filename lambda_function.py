import json
import yfinance as yf


def handler(event, context):
    """
    AWS Lambda handler for stock data retrieval.

    Expected event format:
    {
        "tickers": ["AAPL", "MSFT"],   # list of ticker symbols
        "period": "1d"                  # optional, default "1d"
    }
    """
    tickers = event.get("tickers", [])
    period = event.get("period", "1d")

    if not tickers:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "No tickers provided"}),
        }

    results = {}
    for ticker_symbol in tickers:
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period=period)

        if hist.empty:
            results[ticker_symbol] = {"error": "No data found"}
        else:
            latest = hist.iloc[-1]
            results[ticker_symbol] = {
                "open": round(float(latest["Open"]), 4),
                "high": round(float(latest["High"]), 4),
                "low": round(float(latest["Low"]), 4),
                "close": round(float(latest["Close"]), 4),
                "volume": int(latest["Volume"]),
                "date": str(hist.index[-1].date()),
            }

    return {
        "statusCode": 200,
        "body": json.dumps(results),
    }
