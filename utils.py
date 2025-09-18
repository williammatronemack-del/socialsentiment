import praw
import requests
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from datetime import datetime, timedelta

analyzer = SentimentIntensityAnalyzer()

# --- Helpers ---
def normalize_score(raw):
    return round(((raw + 1) / 2) * 9 + 1, 1)

def vader_score(texts):
    if not texts:
        return 5.0
    scores = [analyzer.polarity_scores(t)["compound"] for t in texts]
    avg = sum(scores) / len(scores)
    return normalize_score(avg)

# --- Reddit Sentiment ---
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

def fetch_reddit_sentiment_timeseries(ticker, client_id, client_secret, user_agent, weeks=12, limit=100):
    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent
    )
    subreddits = ["stocks", "wallstreetbets", "investing"]
    end = datetime.utcnow()
    start = end - timedelta(weeks=weeks)

    # Break into weekly buckets
    buckets = [(start + timedelta(weeks=i), start + timedelta(weeks=i+1)) for i in range(weeks)]
    scores, dates = [], []

    for (b_start, b_end) in buckets:
        texts = []
        for sub in subreddits:
            subreddit = reddit.subreddit(sub)
            for post in subreddit.search(
                ticker,
                limit=limit,
                sort="new",
                time_filter="year"
            ):
                created = datetime.utcfromtimestamp(post.created_utc)
                if b_start <= created < b_end:
                    texts.append(post.title)
                    if post.selftext:
                        texts.append(post.selftext)
        scores.append(vader_score(texts))
        dates.append(b_start.strftime("%Y-%m-%d"))

    return {"avg_score": scores, "date": dates}

# --- Stocktwits Sentiment ---
def fetch_stocktwits_sentiment(ticker):
    url = f"https://api.stocktwits.com/api/2/streams/symbol/{ticker}.json"
    r = requests.get(url)
    if r.status_code != 200:
        return 5.0
    data = r.json()
    messages = [m["body"] for m in data.get("messages", [])]
    return vader_score(messages)

# --- News Sentiment (EODHD) ---
def fetch_eodhd_news_sentiment(ticker, api_key):
    url = f"https://eodhd.com/api/news?s={ticker}&api_token={api_key}&fmt=json"
    r = requests.get(url)
    if r.status_code != 200:
        return 5.0
    data = r.json()
    headlines = [a["title"] for a in data]
    return vader_score(headlines)

def fetch_eodhd_news_timeseries(ticker, api_key, weeks=12):
    url = f"https://eodhd.com/api/news?s={ticker}&api_token={api_key}&fmt=json"
    r = requests.get(url)
    if r.status_code != 200:
        return {"avg_score": [], "date": []}
    data = r.json()

    end = datetime.utcnow()
    start = end - timedelta(weeks=weeks)
    buckets = [(start + timedelta(weeks=i), start + timedelta(weeks=i+1)) for i in range(weeks)]

    scores, dates = [], []
    for (b_start, b_end) in buckets:
        texts = []
        for article in data:
            try:
                adate = datetime.fromisoformat(article["date"].replace("Z", "+00:00"))
            except Exception:
                continue
            if b_start <= adate < b_end:
                texts.append(article.get("title", ""))
                texts.append(article.get("content", ""))
        scores.append(vader_score(texts))
        dates.append(b_start.strftime("%Y-%m-%d"))

    return {"avg_score": scores, "date": dates}


