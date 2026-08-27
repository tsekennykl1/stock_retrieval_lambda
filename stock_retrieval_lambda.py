import json
import yfinance as yf
from datetime import datetime

def lambda_handler(event, context):
    # CORS headers
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
        "Content-Type": "application/json"
    }

    # Handle preflight OPTIONS request
    if event.get("requestContext", {}).get("http", {}).get("method") == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": headers,
            "body": ""
        }

    try:
        # Get stock symbols from query params
        params = event.get("queryStringParameters") or {}
        stocks_param = params.get("stocks", "")        # ✅ safe default
        if not stocks_param:                            # ✅ guard clause
            return {
                "statusCode": 400,
                "headers": headers,
                "body": json.dumps({"error": "Missing required parameter: stocks"})
            }
        symbols = stocks_param.split(",")              # ✅ safe split

        # Fetch stock data for each symbol
        tickers = yf.Tickers(symbols)
        results = {}
        results['retrieval_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Add retrieval time
        for symbol in symbols:
            symbol = symbol.strip()
            ticker = tickers.tickers.get(symbol)

            if ticker:
                info = ticker.history(period="1d", interval="1m")

                if not info.empty:
                    latest_datetime = info.index[-1]
                    latest_data = info.iloc[-1]
                    results[symbol] = {
                    "datetime": latest_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                    "high": round(latest_data["High"], 2),
                    "low": round(latest_data["Low"], 2),
                    "open": round(latest_data["Open"], 2),
                    "price": round(latest_data["Close"], 2),
                    "volume": int(latest_data["Volume"]),
                    "shortName_en": ticker.info.get("shortName", "N/A"),
                    "longName_en": ticker.info.get("longName", "N/A"),
                    "previousClose": round(ticker.info.get("previousClose", 0), 2),
                    "sector": ticker.info.get("sector", "N/A"),
                    "industry": ticker.info.get("industry", "N/A")
                    }
                else:
                    results[symbol] = {"error": "No data available"}
            else:
                results[symbol] = {"error": "Ticker not found"}

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