import json
import time
import os
import yfinance as yf

CACHE_FILE = "/tmp/stock_cache.json"
CACHE_TTL  = 60  # seconds

# ── Cache helpers ──────────────────────────────────────────────────────────────

def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {}

def save_cache(cache):
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(cache, f)
    except:
        pass

# ── Fetch ──────────────────────────────────────────────────────────────────────

def fetch_tickers(symbols):
    """
    Fetch multiple tickers via yf.download (batched).
    NO retry loop — fail fast to avoid timeout.
    """
    seen    = set()
    symbols = [
        s.strip().upper() for s in symbols
        if s and not (s.strip().upper() in seen or seen.add(s.strip().upper()))
    ]
    if not symbols:
        return {}

    tickers_str = " ".join(symbols)

    df = yf.download(
        tickers     = tickers_str,
        period      = "1d",
        interval    = "1m",
        group_by    = "ticker",
        threads     = False,
        auto_adjust = False,
        progress    = False,
    )

    results  = {}
    is_multi = hasattr(df.columns, "levels") and len(df.columns.levels) == 2

    for sym in symbols:
        try:
            if is_multi:
                if sym not in df.columns.get_level_values(0):
                    results[sym] = {"error": "No data available"}
                    continue
                sym_df = df[sym]
            else:
                sym_df = df  # single symbol

            sym_df = sym_df.dropna(how="all")
            if sym_df.empty:
                results[sym] = {"error": "No data available"}
                continue

            latest_dt = sym_df.index[-1]
            latest    = sym_df.iloc[-1]

            results[sym] = {
                "datetime": latest_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "high":     round(float(latest.get("High",   0) or 0), 2),
                "low":      round(float(latest.get("Low",    0) or 0), 2),
                "open":     round(float(latest.get("Open",   0) or 0), 2),
                "price":    round(float(latest.get("Close",  0) or 0), 2),
                "volume":   int(latest.get("Volume", 0) or 0),
            }

        except Exception as e:
            results[sym] = {"error": str(e)}

    return results

# ── Handler ────────────────────────────────────────────────────────────────────

def lambda_handler(event, context):
    headers = {
        "Access-Control-Allow-Origin":  "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
        "Content-Type":                 "application/json"
    }

    # Handle preflight OPTIONS
    if event.get("requestContext", {}).get("http", {}).get("method") == "OPTIONS":
        return {"statusCode": 200, "headers": headers, "body": ""}

    try:
        # ✅ Safe parameter extraction
        params       = event.get("queryStringParameters") or {}
        stocks_param = params.get("stocks") or ""

        if not stocks_param:
            return {
                "statusCode": 400,
                "headers": headers,
                "body": json.dumps({
                    "error":   "Missing required parameter: stocks",
                    "example": "?stocks=0700.HK,9988.HK"
                })
            }

        symbols = [s.strip() for s in stocks_param.split(",") if s.strip()]
        cache   = load_cache()
        now     = time.time()

        # ── Split symbols into cache hits vs needs fetch ───────────────────────
        fresh_symbols  = []
        results        = {}

        for sym in symbols:
            cached = cache.get(sym)
            if cached and (now - cached.get("_ts", 0)) < CACHE_TTL:
                print(f"[CACHE HIT] {sym}")
                results[sym] = {k: v for k, v in cached.items() if k != "_ts"}
            else:
                fresh_symbols.append(sym)

        # ── Fetch only stale / uncached symbols ───────────────────────────────
        if fresh_symbols:
            print(f"[FETCH] {len(fresh_symbols)} symbols: {fresh_symbols}")
            try:
                fetched = fetch_tickers(fresh_symbols)

                for sym, data in fetched.items():
                    if "error" not in data:
                        # ✅ Store in cache with timestamp
                        cache[sym]  = {**data, "_ts": now}
                        results[sym] = data
                    else:
                        # ✅ Rate limited — fall back to stale cache if available
                        stale = cache.get(sym)
                        if stale:
                            print(f"[STALE CACHE] {sym} — fetch failed, serving stale")
                            results[sym] = {k: v for k, v in stale.items() if k != "_ts"}
                            results[sym]["stale"] = True
                        else:
                            results[sym] = data  # propagate error

            except Exception as e:
                err = str(e)
                is_rate_limit = any(
                    x in err for x in ["429", "Too Many Requests", "Rate", "YFRateLimitError"]
                )
                print(f"[{'RATE LIMIT' if is_rate_limit else 'ERROR'}] {err}")

                for sym in fresh_symbols:
                    stale = cache.get(sym)
                    if stale:
                        print(f"[STALE CACHE] {sym} — batch failed, serving stale")
                        results[sym] = {k: v for k, v in stale.items() if k != "_ts"}
                        results[sym]["stale"] = True
                    else:
                        results[sym] = {
                            "error": "Rate limited. No cached data available. Try again shortly."
                        }

        save_cache(cache)

        return {
            "statusCode": 200,
            "headers":    headers,
            "body":       json.dumps(results)
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers":    headers,
            "body":       json.dumps({"error": str(e)})
        }
