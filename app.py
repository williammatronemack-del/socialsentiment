import os
from flask import Flask, request, jsonify
from utils import (
    fetch_reddit_sentiment,
    fetch_stocktwits_sentiment,
    fetch_eodhd_news_sentiment,
    build_time_series
)

app = Flask(__name__)

EODHD_API_KEY = os.getenv("EODHD_API_KEY", "")
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "mackresearch-sentiment/0.1")

@app.route("/")
def home():
    return {"status": "ok", "service": "sentiment-api"}

@app.route("/sentiment/reddit")
def reddit_sentiment():
    ticker = request.args.get("ticker", "NVDA")
    score = fetch_reddit_sentiment(
        ticker,
        REDDIT_CLIENT_ID,
        REDDIT_CLIENT_SECRET,
        REDDIT_USER_AGENT
    )
    return jsonify({"ticker": ticker, "source": "reddit", "score": score})

@app.route("/sentiment/stocktwits")
def stocktwits_sentiment():
    ticker = request.args.get("ticker", "NVDA")
    score = fetch_stocktwits_sentiment(ticker)
    return jsonify({"ticker": ticker, "source": "stocktwits", "score": score})

@app.route("/sentiment/news")
def news_sentiment():
    ticker = request.args.get("ticker", "NVDA")
    score = fetch_eodhd_news_sentiment(ticker, EODHD_API_KEY)
    return jsonify({"ticker": ticker, "source": "news", "score": score})

@app.route("/sentiment/timeseries")
def sentiment_timeseries():
    ticker = request.args.get("ticker", "NVDA")
    # Dummy example for time series
    dummy_data = [
        {"date": "2025-01-01", "score": 6.0},
        {"date": "2025-01-03", "score": 7.0},
        {"date": "2025-01-10", "score": 4.0},
        {"date": "2025-01-15", "score": 8.0},
    ]
    series = build_time_series(dummy_data)
    return jsonify({"ticker": ticker, "time_series": series})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
