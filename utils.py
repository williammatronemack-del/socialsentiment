import os
import requests
from datetime import datetime, timedelta
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import praw
from collections import defaultdict

analyzer = SentimentIntensityAnalyzer()

# Reddit client
reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent=os.getenv("REDDIT_USER_AGENT", "social-sentiment-app")
)

def week_start(dt: datetime):
    """Normalize to Monday of that week."""
    return dt - timedelta(days=dt.weekday())

# ---------- NEWS ----------
def fetch_eodhd_news_timeseries(ticker, limit=50):
    api_key = os.getenv("EODHD_API_KEY")
    url = f"https://eodhd.com/api/news?s={ticker}&limit={limit}&api_token={api_key}&fmt=json"

    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        articles = resp.json()
    except Exception as e:
        return {"avg_score": [], "date": [], "error": str(e)}

    buckets = defaultdict(list)
    for art in articles:
        text = (art.get("title", "") or "") + " " + (art.get("content", "") or "")
        if not text.strip():
            continue
        score = analyzer.polarity_scores(text)["compound"]
        dt = datetime.fromisoformat(art["date"].replace("Z", "+00:00"))
        buckets[week_start(dt)].append(score)

    dates, avgs = [], []
    for wk, scores in sorted(buckets.items()):
        dates.append(wk.strftime("%a, %d %b %Y %H:%M:%S GMT"))
        avgs.append(round(sum(scores) / len(scores), 2))

    return {"avg_score": avgs, "date": dates}

# ---------- REDDIT ----------
def fetch_reddit_timeseries(ticker, limit=50):
    results = []
    try:
        for submission in reddit.subreddit("all").search(ticker, limit=limit, sort="new"):
            text = (submission.title or "") + " " + (submission.selftext or "")
            if not text.strip():
                continue
            score = analyzer.polarity_scores(text)["compound"]
            dt = datetime.utcfromtimestamp(submission.created_utc)
            results.append((week_start(dt), score))
    except Exception as e:
        return {"avg_score": [], "date": [], "error": str(e)}

    buckets = defaultdict(list)
    for dt, score in results:
        buckets[dt].append(score)

    dates, avgs = [], []
    for wk, scores in sorted(buckets.items()):
        dates.append(wk.strftime("%a, %d %b %Y %H:%M:%S GMT"))
        avgs.append(round(sum(scores) / len(scores), 2))

    return {"avg_score": avgs, "date": dates}

