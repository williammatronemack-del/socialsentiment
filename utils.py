import praw
import requests
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import polars as pl

analyzer = SentimentIntensityAnalyzer()

def normalize_score(raw):
    return round(((raw + 1) / 2) * 9 + 1, 1)

def vader_score(texts):
    if not texts:
        return 5.0
    scores = [analyzer.polarity_scores(t)["compound"] for t in texts]
    avg = sum(scores) / len(scores)
    return normalize_score(avg)

def fetch_reddit_sentiment(ticker, client_id, client_secret, user_agent, limit=50):
    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent
    )
    texts = []
    subreddits = ["stocks", "wallstreetbets", "investing"]
    for sub in subreddits:
        subreddit = reddit.subreddit(sub)
        for post in subreddit.search(ticker, limit=limit, sort="new"):
            texts.append(post.title)
            if post.selftext:
                texts.append(post.selftext)
    return vader_score(texts)

def fetch_stocktwits_sentiment(ticker):
    url = f"https://api.stocktwits.com/api/2/streams/symbol/{ticker}.json"
    r = requests.get(url)
    if r.status_code != 200:
        return 5.0
    data = r.json()
    messages = [m["body"] for m in data.get("messages", [])]
    return vader_score(messages)

def fetch_eodhd_news_sentiment(ticker, api_key):
    url = f"https://eodhd.com/api/news?s={ticker}&api_token={api_key}&fmt=json"
    r = requests.get(url)
    if r.status_code != 200:
        return 5.0
    data = r.json()
    headlines = [a["title"] for a in data]
    return vader_score(headlines)

def build_time_series(data):
    df = pl.DataFrame(data)
    df = df.with_columns([pl.col("date").str.strptime(pl.Date, "%Y-%m-%d")])
    weekly = df.group_by_dynamic("date", every="1w").agg([
        pl.col("score").mean().alias("avg_score")
    ])
    return weekly.to_dict(as_series=False)
import requests
from datetime import datetime, timedelta
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

analyzer = SentimentIntensityAnalyzer()


def normalize_score(raw):
    return round(((raw + 1) / 2) * 9 + 1, 1)


def vader_score(texts):
    if not texts:
        return 5.0
    scores = [analyzer.polarity_scores(t)["compound"] for t in texts]
    avg = sum(scores) / len(scores)
    return normalize_score(avg)


# Existing fetch_eodhd_news_sentiment (leave as-is)
def fetch_eodhd_news_sentiment(ticker, api_key):
    url = f"https://eodhd.com/api/news?s={ticker}&api_token={api_key}&fmt=json"
    r = requests.get(url)
    if r.status_code != 200:
        return 5.0
    data = r.json()
    headlines = [a["title"] for a in data]
    return vader_score(headlines)


# 🆕 Time-series version
def fetch_eodhd_news_timeseries(ticker, api_key, months=12, interval_days=7):
    url = f"https://eodhd.com/api/news?s={ticker}&api_token={api_key}&fmt=json"
    r = requests.get(url)
    if r.status_code != 200:
        return {"avg_score": [], "date": []}

    data = r.json()
    results = []

    # Collect (headline, published date)
    for article in data:
        try:
            dt = datetime.strptime(article["date"], "%Y-%m-%d %H:%M:%S")
        except:
            continue
        results.append((dt, article["title"]))

    if not results:
        return {"avg_score": [], "date": []}

    # Sort oldest → newest
    results.sort(key=lambda x: x[0])

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=months * 30)

    scores = []
    dates = []

    current = start_date
    while current < end_date:
        bucket_end = current + timedelta(days=interval_days)
        bucket_texts = [t for (d, t) in results if current <= d < bucket_end]

        if bucket_texts:
            score = vader_score(bucket_texts)
            scores.append(score)
            dates.append(current.strftime("%Y-%m-%d"))

        current = bucket_end

    return {"avg_score": scores, "date": dates}

