from datetime import datetime, timedelta
from collections import defaultdict
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# 🔹 Replace this with your real data fetcher
def fetch_sentiment_data(source, ticker):
    """
    Fetch raw VADER sentiment for given source + ticker.
    Must return list of dicts:
      [{"date": "2025-05-01T12:00:00Z", "score": 0.85}, ...]
    """
    # EXAMPLE dummy data – replace with your pipeline
    now = datetime.utcnow()
    dummy = []
    for i in range(200):  # 200 raw points over ~6 months
        d = now - timedelta(days=i)
        score = (i % 10 - 5) / 10.0  # fake -0.5 to 0.5
        dummy.append({"date": d.isoformat() + "Z", "score": score})
    return dummy

@app.route("/sentiment/<source>/timeseries")
def sentiment_timeseries(source):
    ticker = request.args.get("ticker")
    if not ticker:
        return jsonify({"error": "Missing ticker"}), 400

    # 1️⃣ Fetch raw scores
    raw_scores = fetch_sentiment_data(source, ticker)

    # 2️⃣ Filter last 6 months
    cutoff = datetime.utcnow() - timedelta(days=180)
    filtered = [
        row for row in raw_scores
        if datetime.fromisoformat(row["date"].replace("Z", "")) >= cutoff
    ]

    # 3️⃣ Bucket by ISO week
    buckets = defaultdict(list)
    for row in filtered:
        d = datetime.fromisoformat(row["date"].replace("Z", ""))
        year, week, _ = d.isocalendar()
        key = f"{year}-W{week}"
        buckets[key].append(row["score"])

    # 4️⃣ Average per week
    weeks = sorted(buckets.keys())
    avg_scores = [sum(buckets[w]) / len(buckets[w]) for w in weeks]

    # 5️⃣ Return JSON in your plugin format
    return jsonify({
        "ticker": ticker.upper(),
        "time_series": {
            "avg_score": avg_scores,
            "date": weeks
        }
    })

@app.route("/")
def home():
    return "Social Sentiment API – Weekly Avg, 6M trailing"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

