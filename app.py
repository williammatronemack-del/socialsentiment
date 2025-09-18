from datetime import datetime, timedelta
from collections import defaultdict
from flask import Flask, request, jsonify
from flask_cors import CORS
import os, time

import praw
import nltk
import requests
import feedparser

# Ensure VADER lexicon is available in project-local nltk_data folder
nltk_data_path = os.path.join(os.path.dirname(__file__), "nltk_data")
os.makedirs(nltk_data_path, exist_ok=True)
nltk.data.path.append(nltk_data_path)

def get_analyzer():
    try:
        from nltk.sentiment.vader import SentimentIntensityAnalyzer
        return SentimentIntensityAnalyzer()
    except LookupError:
        nltk.download("vader_lexicon", download_dir=nltk_data_path)
        from nltk.sentiment.vader import SentimentIntensityAnalyzer
        return SentimentIntensityAnalyzer()

app = Flask(__name__)
CORS(app)

# Reddit client (needs env vars set in Render)
reddit = praw.Reddit(
    client_id=os.environ.get("REDDIT_CLIENT_ID"),
    client_secret=os.environ.get("REDDIT_CLIENT_SECRET"),
    user_agent=os.environ.get("REDDIT_USER_AGENT", "social-sentiment-app")
)

analyzer = get_analyzer()

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
            text = f"{submission.title} {submission.selftext or ''}"
            score = analyzer.polarity_scores(text)["compound"]
            results.append({"date": created.isoformat() + "Z", "score": score})
    return results

def fetch_news_data_newsapi(ticker, cutoff):
    api_key = os.environ.get("NEWSAPI_KEY")
    if not api_key:
        return None  # fall back to RSS

    url = "https://newsapi.org/v2/everything"
    params = {
        "q": ticker,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 100,
        "from": (cutoff).strftime("%Y-%m-%d")
    }
    headers = {"X-Api-Key": api_key}
    r = requests.get(url, params=params, headers=headers, timeout=30)
    if r.status_code != 200:
        return None

    data = r.json()
    results = []
    for art in data.get("articles", []):
        dt_str = art.get("publishedAt")
        if not dt_str:
            continue
        try:
            # publishedAt like "2025-05-12T10:30:00Z"
            d = datetime.fromisoformat(dt_str.replace("Z",""))
        except Exception:
            continue
        if d < cutoff:
            continue
        text = " ".join(filter(None, [art.get("title"), art.get("description"), art.get("content")]))
        if not text.strip():
            continue
        score = analyzer.polarity_scores(text)["compound"]
        results.append({"date": d.isoformat() + "Z", "score": score})
    return results

def fetch_news_data_rss(ticker, cutoff):
    # Google News RSS search. Note: returns recent news; may not cover full 6 months depending on availability.
    query = f"{ticker}"
    rss_url = f"https://news.google.com/rss/search?q={requests.utils.quote(query)}&hl=en-US&gl=US&ceid=US:en"
    feed = feedparser.parse(rss_url)
    results = []
    for entry in feed.entries:
        # published_parsed is a time.struct_time
        tt = entry.get("published_parsed")
        if not tt:
            continue
        d = datetime.utcfromtimestamp(time.mktime(tt))
        if d < cutoff:
            continue
        text = " ".join(filter(None, [entry.get("title", ""), entry.get("summary", "")]))
        if not text.strip():
            continue
        score = analyzer.polarity_scores(text)["compound"]
        results.append({"date": d.isoformat() + "Z", "score": score})
    return results

def fetch_news_data(ticker):
    cutoff = datetime.utcnow() - timedelta(days=180)
    # Try NewsAPI first (if key provided), else RSS fallback
    newsapi_results = fetch_news_data_newsapi(ticker, cutoff)
    if newsapi_results is not None and len(newsapi_results) > 0:
        return newsapi_results
    return fetch_news_data_rss(ticker, cutoff)

def aggregate_weekly(raw_scores):
    buckets = defaultdict(list)
    cutoff = datetime.utcnow() - timedelta(days=180)
    for row in raw_scores:
        try:
            d = datetime.fromisoformat(row["date"].replace("Z", ""))
        except Exception:
            continue
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
    return "Social Sentiment API – Reddit + News (real) VADER weekly averages (6M)"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
