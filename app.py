import os
from flask import Flask, request, jsonify
from utils import (
    fetch_reddit_sentiment,
    fetch_stocktwits_sentiment,
    fetch_eodhd_news_sentiment,
    fetch_reddit_timeseries,
    validate_ticker
)

app = Flask(__name__)

# API Keys from Render env variables
EODHD_API_KEY = os.getenv("EODHD_API_KEY", "")
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "mackresearch-sentiment/0.1")

@app.route("/")
def home():
    return {"status": "ok", "service": "sentiment-api"}

@app.route("/health")
def health():
    return {"status": "healthy"}, 200

@app.route("/sentiment/reddit")
def reddit_sentiment():
    try:
        ticker = validate_ticker(request.args.get("ticker", "NVDA"))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    score = fetch_reddit_sentiment(
        ticker,
        REDDIT_CLIENT_ID,
        REDDIT_CLIENT_SECRET,
        REDDIT_USER_AGENT
    )
    return jsonify({"ticker": ticker, "source": "reddit", "score": score})

@app.route("/sentiment/stocktwits")
def stocktwits_sentiment():
    try:
        ticker = validate_ticker(request.args.get("ticker", "NVDA"))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    score = fetch_stocktwits_sentiment(ticker)
    return jsonify({"ticker": ticker, "source": "stocktwits", "score": score})

@app.route("/sentiment/news")
def news_sentiment():
    try:
        ticker = validate_ticker(request.args.get("ticker", "NVDA"))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    score = fetch_eodhd_news_sentiment(ticker, EODHD_API_KEY)
    return jsonify({"ticker": ticker, "source": "news", "score": score})

@app.route("/sentiment/blend")
def blended_sentiment():
    try:
        ticker = validate_ticker(request.args.get("ticker", "NVDA"))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    reddit_score = fetch_reddit_sentiment(
        ticker,
        REDDIT_CLIENT_ID,
        REDDIT_CLIENT_SECRET,
        REDDIT_USER_AGENT
    )
    stocktwits_score = fetch_stocktwits_sentiment(ticker)
    news_score = fetch_eodhd_news_sentiment(ticker, EODHD_API_KEY)

    scores = [s for s in [reddit_score, stocktwits_score, news_score] if s is not None]
    avg = round(sum(scores) / len(scores), 1) if scores else None

    return jsonify({
        "ticker": ticker,
        "reddit": reddit_score,
        "stocktwits": stocktwits_score,
        "news": news_score,
        "blended": avg
    })

@app.route("/sentiment/reddit/weekly")
def reddit_weekly():
    try:
        ticker = validate_ticker(request.args.get("ticker", "NVDA"))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    weeks = int(request.args.get("weeks", 52))
    series = fetch_reddit_timeseries(
        ticker,
        REDDIT_CLIENT_ID,
        REDDIT_CLIENT_SECRET,
        REDDIT_USER_AGENT,
        weeks=weeks
    )
    return jsonify({"ticker": ticker, "source": "reddit", "weekly": series})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
