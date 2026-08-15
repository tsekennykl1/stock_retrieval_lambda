import json
import time
import yfinance as yf


def fetch_tickers(symbols, max_retries=3):
    """Fetch multiple tickers via yf.download (batched) with retry + exponential backoff.
       Returns only OHLCV + datetime (no ticker.info calls).
    """
    # Normalize / dedupe while preserving order
    seen = set()
    symbols = [s.strip().upper() for s in symbols if s and not (s.strip().upper() in seen or seen.add(s.strip().upper()))]

    if not symbols:
        return {}

    tickers_str = " ".join(symbols)

    for attempt in range(max_retries):
        try:
            df = yf.download(
                tickers=tickers_str,
                period="1d",
                interval="1m",
                group_by="ticker",
                threads=False,
                auto_adjust=False,
                progress=False,
            )

            results = {}

            is_multi = hasattr(df.columns, "levels") and len(df.columns.levels) == 2

            for sym in symbols:
                try:
                    if is_multi:
                        # columns like (AAPL, 'Open')...
                        if sym not in df.columns.get_level_values(0):
                            results[sym] = {"error": "No data available"}
                            continue
                        sym_df = df[sym]
                    else:
                        # single symbol case
                        sym_df = df

                    sym_df = sym_df.dropna(how="all")
                    if sym_df.empty:
                        results[sym] = {"error": "No data available"}
                        continue

                    latest_dt = sym_df.index[-1]
                    latest = sym_df.iloc[-1]

                    results[sym] = {
                        "datetime": latest_dt.strftime("%Y-%m-%d %H:%M:%S"),
                        "high": round(float(latest.get("High", 0) or 0), 2),
                        "low": round(float(latest.get("Low", 0) or 0), 2),
                        "open": round(float(latest.get("Open", 0) or 0), 2),
                        "price": round(float(latest.get("Close", 0) or 0), 2),
                        "volume": int(latest.get("Volume", 0) or 0),
                    }

                except Exception as e:
                    results[sym] = {"error": str(e)}

            return results

        except Exception as e:
            err = str(e)
            if any(x in err for x in ["429", "Too Many Requests", "Rate", "rate"]):
                wait = 2 ** attempt  # 1s → 2s → 4s
                print(f"[RATE LIMIT] attempt {attempt+1}/{max_retries}, retrying in {wait}s")
                time.sleep(wait)
            else:
                print(f"[ERROR]: {err}")
                return {sym: {"error": err} for sym in symbols}

    return {sym: {"error": "Rate limited after retries. Try again later."} for sym in symbols}


def lambda_handler(event, context):
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
        "Content-Type": "application/json"
    }

    # Handle preflight OPTIONS (API Gateway HTTP API v2)
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

        symbols = [s.strip() for s in stocks_param.split(",") if s.strip()]
        print(f"Fetching {len(symbols)} symbols via yf.download (no ticker.info)")

        results = fetch_tickers(symbols)

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