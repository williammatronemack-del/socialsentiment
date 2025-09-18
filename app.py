from datetime import datetime, timedelta
from collections import defaultdict
from flask import Flask, request, jsonify
from flask_cors import CORS
import os

import praw
import nltk

# Ensure VADER lexicon is available
try:
    from nltk.sentiment.vader import SentimentIntensityAnalyzer
except LookupError:
    nltk.download('vader_lexicon')
    from nltk.sentiment.vader import SentimentIntensityAnalyzer

app = Flask(__name__)
CORS(app)

# Reddit client (needs env vars set in Render)
reddit = praw.Reddit(
    client_id=os.environ.get("REDDIT_CLIENT_ID"),
    client_secret=os.environ.get("REDDIT_CLIENT_SECRET"),
    user_agent=os.environ.get("REDDIT_USER_AGENT", "social-sentiment-app")
)

analyzer = SentimentIntensityAnalyzer()

FIXED_SUBS = ["stocks", "wallstreetbets", "investing"]

def fetch_reddit_data(ticker):
    results = []
    cutoff = datetime.utcnow() - timedelta(days=180)
    for sub in FIXED_SUBS:
        subreddit = reddit.subreddit(sub)
        for submission in subreddit.search(ticker, time_filter="year", limit=200):
            created = datetime.utcfromtimestamp(submission.created_utc)
            if created < cutoff:
                continue
            text = f"{submission.title} {submission.selftext}"
            score = analyzer.polarity_scores(text)["compound"]
            results.append({"date": created.isoformat() + "Z", "score": score})
    return results

def fetch_news_data(ticker):
    # 🔹 Stub for news sentiment – returns fake values in expected format
    now = datetime.utcnow()
    results = []
    for i in range(26):  # 26 weeks ~ 6 months
        d = now - timedelta(weeks=i)
        score = ((i % 10) - 5) / 10.0  # fake -0.5..0.5
        results.append({"date": d.isoformat() + "Z", "score": score})
    return results

def aggregate_weekly(raw_scores):
    buckets = defaultdict(list)
    cutoff = datetime.utcnow() - timedelta(days=180)
    for row in raw_scores:
        d = datetime.fromisoformat(row["date"].replace("Z", ""))
        if d < cutoff:
            continue
        year, week, _ = d.isocalendar()
        key = f"{year}-W{week}"
        buckets[key].append(row["score"])
    weeks = sorted(buckets.keys())
    avg_scores = [sum(buckets[w]) / len(buckets[w]) for w in weeks]
    return weeks, avg_scores

@app.route("/sentiment/<source>/timeseries")
def sentiment_timeseries(source):
    ticker = request.args.get("ticker")
    if not ticker:
        return jsonify({"error": "Missing ticker"}), 400

    if source == "reddit":
        raw = fetch_reddit_data(ticker)
    elif source == "news":
        raw = fetch_news_data(ticker)
    else:
        return jsonify({"error": "Unknown source"}), 400

    weeks, avg_scores = aggregate_weekly(raw)

    return jsonify({
        "ticker": ticker.upper(),
        "time_series": {
            "avg_score": avg_scores,
            "date": weeks
        }
    })

@app.route("/")
def home():
    return "Social Sentiment API – Reddit + News VADER weekly averages (6M)"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
