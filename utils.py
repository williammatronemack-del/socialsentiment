import praw
import requests
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
