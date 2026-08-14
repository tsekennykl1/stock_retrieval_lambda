import json
import time
import yfinance as yf

def fetch_ticker(symbol, max_retries=3):
    """Fetch single ticker with retry + exponential backoff"""
    for attempt in range(max_retries):
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.history(period="1d", interval="1m")
            ticker_info = ticker.info  # ✅ fetch once, reuse below

            if not info.empty:
                latest_datetime = info.index[-1]
                latest_data = info.iloc[-1]
                return {
                    "datetime": latest_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                    "high": round(latest_data["High"], 2),
                    "low": round(latest_data["Low"], 2),
                    "open": round(latest_data["Open"], 2),
                    "price": round(latest_data["Close"], 2),
                    "volume": int(latest_data["Volume"]),
                    "shortName_en": ticker_info.get("shortName", "N/A"),
                    "longName_en": ticker_info.get("longName", "N/A"),
                    "previousClose": round(ticker_info.get("previousClose", 0), 2),
                    "sector": ticker_info.get("sector", "N/A"),
                    "industry": ticker_info.get("industry", "N/A"),
                    "peRatio": round(ticker_info.get("trailingPE", 0), 2),
                    "bookValue": round(ticker_info.get("bookValue", 0), 2)
                }
            else:
                return {"error": "No data available"}

        except Exception as e:
            err = str(e)
            if any(x in err for x in ["429", "Too Many Requests", "Rate", "rate"]):
                wait = 2 ** attempt  # 1s → 2s → 4s
                print(f"[RATE LIMIT] {symbol} attempt {attempt+1}/{max_retries}, retrying in {wait}s")
                time.sleep(wait)
            else:
                print(f"[ERROR] {symbol}: {err}")
                return {"error": err}

    return {"error": "Rate limited after retries. Try again later."}


def lambda_handler(event, context):
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
        "Content-Type": "application/json"
    }

    # Handle preflight OPTIONS
    if event.get("requestContext", {}).get("http", {}).get("method") == "OPTIONS":
        return {"statusCode": 200, "headers": headers, "body": ""}

    try:
        params = event.get("queryStringParameters") or {}
        stocks_param = params.get("stocks", "")
        if not stocks_param:
            return {
                "statusCode": 400,
                "headers": headers,
                "body": json.dumps({"error": "Missing required parameter: stocks"})
            }

        symbols = [s.strip() for s in stocks_param.split(",")]

        results = {}
        for i, symbol in enumerate(symbols):
            if i > 0:
                time.sleep(0.5)  # ✅ 500ms between symbols to avoid burst
            print(f"Fetching {symbol} ({i+1}/{len(symbols)})")
            results[symbol] = fetch_ticker(symbol)

        return {
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps(results)
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps({"error": str(e)})
        }
