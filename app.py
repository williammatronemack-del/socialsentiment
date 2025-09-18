from datetime import datetime, timedelta

@app.route("/sentiment/timeseries")
def sentiment_timeseries():
    ticker = request.args.get("ticker", "NVDA")
    period = request.args.get("period", "12w")  # default lookback is 12 weeks

    # --- translate `period` into days ---
    now = datetime.utcnow()
    if period.endswith("w"):
        days = int(period[:-1]) * 7
    elif period.endswith("m"):
        days = int(period[:-1]) * 30
    elif period.endswith("y"):
        days = int(period[:-1]) * 365
    else:
        days = 90  # fallback (approx. 3 months)

    start_date = now - timedelta(days=days)

    # --- fetch news from EODHD ---
    url = (
        f"https://eodhd.com/api/news?"
        f"s={ticker}&api_token={EODHD_API_KEY}"
        f"&from={start_date.date()}&to={now.date()}&fmt=json"
    )
    r = requests.get(url)
    if r.status_code != 200:
        return jsonify({"error": "failed to fetch news", "status": r.status_code})

    try:
        articles = r.json()
    except Exception:
        return jsonify({"error": "failed to parse EODHD response"})

    if not articles:
        return jsonify({"ticker": ticker, "period": period, "time_series": {"date": [], "avg_score": []}})

    # --- bucket articles by week starting Monday ---
    buckets = {}
    for a in articles:
        try:
            pub = datetime.strptime(a["date"], "%Y-%m-%d %H:%M:%S")
        except Exception:
            continue
        week_start = pub - timedelta(days=pub.weekday())
        week_key = week_start.strftime("%Y-%m-%d")
        buckets.setdefault(week_key, []).append(a["title"])

    # --- score each week ---
    dates, scores = [], []
    for week in sorted(buckets.keys()):
        avg_score = vader_score(buckets[week])
        dates.append(week)
        scores.append(avg_score)

    return jsonify({
        "ticker": ticker,
        "period": period,
        "time_series": {
            "date": dates,
            "avg_score": scores
        }
    })

