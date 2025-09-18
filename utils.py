import os
import requests
import pandas as pd
from datetime import datetime
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import praw

# --- Global setup ---
analyzer = SentimentIntensityAnalyzer()

# Reddit client
reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent=os.getenv("REDDIT_USER_AGENT", "social-sentiment-app")
)

# ---------- NEWS ----------
def fetch_eodhd_news_timeseries(ticker, limit=50):
    """
    Pulls recent news from EODHD API, aggregates sentiment weekly.
    """
    api_key = os.getenv("EODHD_API_KEY")
    url = f"https://eodhd.com/api/news?s={ticker}&limit={limit}&api_token={api_key}&fmt=json"

    resp = requests.get(url, timeout=15)
    if resp.status_code != 200:
        return {"avg_score": [], "date": []}

    articles = resp.json()
    rows = []
    for art in articles:
        text = art.get("title", "") + " " + art.get("content", "")
        score = analyzer.polarity_scores(text)["compound"]
        dt = datetime.fromisoformat(art["date"].replace("Z", "+00:00"))
        rows.append({"date": dt, "score": score})

    if not rows:
        return {"avg_score": [], "date": []}

    df = pd.DataFrame(rows)
    ts = df.resample("W", on="date")["score"].mean().reset_index()

    return {
        "avg_score": ts["score"].round(2).tolist(),
        "date": ts["date"].dt.strftime("%a, %d %b %Y %H:%M:%S GMT").tolist()
    }

# ---------- REDDIT ----------
def fetch_reddit_timeseries(ticker, limit=50):
    """
    Searches Reddit for ticker mentions, aggregates sentiment weekly.
    """
    results = []
    try:
        for submission in reddit.subreddit("all").search(ticker, limit=limit, sort="new"):
            text = submission.title + " " + submission.selftext
            score = analyzer.polarity_scores(text)["compound"]
            dt = datetime.utcfromtimestamp(submission.created_utc)
            results.append({"date": dt, "score": score})
    except Exception as e:
        return {"avg_score": [], "date": [], "error": str(e)}

    if not results:
        return {"avg_score": [], "date": []}

    df = pd.DataFrame(results)
    ts = df.resample("W", on="date")["score"].mean().reset_index()

    return {
        "avg_score": ts["score"].round(2).tolist(),
        "date": ts["date"].dt.strftime("%a, %d %b %Y %H:%M:%S GMT").tolist()
    }
