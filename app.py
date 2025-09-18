import os
from flask import Flask, request, jsonify
from utils import (
    fetch_reddit_sentiment,
    fetch_eodhd_news_timeseries
)

# Initialize Flask app
app = Flask(__name__)

# Environment variables (configure in Render dashboard)
EODHD_API_KEY = os.getenv("EODHD_API_KEY", "")
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "mackresearch-sentiment/0.1")


# Root health check
@app.route("/")
def home():
    return {"status": "ok", "service": "social-sentiment-api"}


# Reddit sentiment endpoint
@app.route("/sentiment/reddit")
def sentiment_reddit():
    ticker = request.args.get("ticker", "NVDA")
    limit = int(request.args.get("limit", 50))

    score = fetch_reddit_sentiment(
        ticker,
        REDDIT_CLIENT_ID,
        REDDIT_CLIENT_SECRET,
        REDDIT_USER_AGENT,
        limit=limit
    )
    return jsonify({"ticker": ticker, "source": "reddit", "avg_score": score})


# News time-series endpoint (weekly trailing 12 months)
@app.route("/sentiment/news/timeseries")
def sentiment_news_timeseries():
    ticker = request.args.get("ticker", "NVDA")

    ts = fetch_eodhd_news_timeseries(
        ticker,
        EODHD_API_KEY
    )
    return jsonify({"ticker": ticker, "time_series": ts})


# Run locally (not used on Render — Render runs gunicorn)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

