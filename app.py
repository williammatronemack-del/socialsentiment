from flask import Flask, request, jsonify
from flask_cors import CORS
from utils import (
    fetch_eodhd_news_timeseries,
    fetch_reddit_timeseries,
)

app = Flask(__name__)
CORS(app)  # allow requests from your WP site

@app.route("/")
def home():
    return jsonify({"status": "ok", "message": "Social Sentiment API running"})

@app.route("/sentiment/news/timeseries")
def news_timeseries():
    ticker = request.args.get("ticker")
    try:
        data = fetch_eodhd_news_timeseries(ticker)
        return jsonify({"ticker": ticker, "time_series": data})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/sentiment/reddit/timeseries")
def reddit_timeseries():
    ticker = request.args.get("ticker")
    try:
        data = fetch_reddit_timeseries(ticker)
        return jsonify({"ticker": ticker, "time_series": data})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)


