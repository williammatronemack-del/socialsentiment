import requests
from datetime import datetime, timedelta
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

analyzer = SentimentIntensityAnalyzer()

def normalize_score(raw):
    return round(((raw + 1) / 2) * 9 + 1, 1)

def vader_score(texts):
    if not texts:
        return 5.0
    scores = [analyzer.polarity_scores(t)["compound"] for t in texts if t]
    if not scores:
        return 5.0
    avg = sum(scores) / len(scores)
    return normalize_score(avg)

def fetch_eodhd_news_sentiment(ticker, api_key):
    """Single snapshot sentiment."""
    url = f"https://eodhd.com/api/news?s={ticker}&api_token={api_key}&fmt=json"
    r = requests.get(url)
    if r.status_code != 200:
        return 5.0
    data = r.json()
    headlines = [a.get("title", "") for a in data]
    return vader_score(headlines)

def fetch_eodhd_news_timeseries(ticker, api_key, months=12, interval_days=7):
    """Time series sentiment from news headlines (weekly by default)."""
    url = f"https://eodhd.com/api/news?s={ticker}&api_token={api_key}&fmt=json"
    r = requests.get(url)
    if r.status_code != 200:
        return {"avg_score": [], "date": []}

    data = r.json()
    results = []

    for article in data:
        raw_date = article.get("date")
        if not raw_date:
            continue
        try:
            # Handles ISO8601, e.g. 2025-09-18T15:46:00+00:00
            dt = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
        except Exception:
            continue
        results.append((dt, article.get("title", "")))

    if not results:
        return {"avg_score": [], "date": []}

    results.sort(key=lambda x: x[0])

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=months * 30)

    scores, dates = [], []
    current = start_date
    while current < end_date:
        bucket_end = current + timedelta(days=interval_days)
        bucket_texts = [t for (d, t) in results if current <= d < bucket_end]

        if bucket_texts:
            scores.append(vader_score(bucket_texts))
            dates.append(current.strftime("%Y-%m-%d"))

        current = bucket_end

    return {"avg_score": scores, "date": dates}

