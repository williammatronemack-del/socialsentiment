from flask import Flask, request, jsonify
from utils import fetch_eodhd_news_sentiment, fetch_eodhd_news_timeseries
import os

app = Flask(__name__)

EODHD_API_KEY = os.getenv("EODHD_API_KEY", "")

@app.route("/")
def home():
    return "✅ Social Sentiment API is running"

@app.route("/sentiment/news")
def news_sentiment():
    ticker = request.args.get("ticker")
    if not ticker:
        return jsonify({"error": "ticker required"}), 400
    score = fetch_eodhd_news_sentiment(ticker, EODHD_API_KEY)
    return jsonify({"ticker": ticker, "score": score})

@app.route("/sentiment/news/timeseries")
def news_timeseries():
    ticker = request.args.get("ticker")
    if not ticker:
        return jsonify({"error": "ticker required"}), 400
    ts = fetch_eodhd_news_timeseries(ticker, EODHD_API_KEY)
    return jsonify({"ticker": ticker, "time_series": ts})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

