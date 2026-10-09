"""Fetch TAIFEX FCM daily data (current + previous month) and build site/index.html."""
import csv, io, json, os, datetime, urllib.request

BASE = "https://www.taifex.com.tw/enl/eng7"
URLS = [
    (f"{BASE}/getFCMFileOpen?filename=Daily_FUT_OpenData.csv", "F"),
    (f"{BASE}/getFCMFileOpen?filename=Daily_OPT_OpenData.csv", "O"),
    (f"{BASE}/getFCMFilePreOpen?filename=Daily_FUT_OpenData.csv", "F"),
    (f"{BASE}/getFCMFilePreOpen?filename=Daily_OPT_OpenData.csv", "O"),
]

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8-sig")

rows, brokers, seen = [], {}, set()
for url, src in URLS:
    text = fetch(url)
    for rec in csv.reader(io.StringIO(text)):
        if len(rec) < 5 or rec[0].startswith("期貨商"):
            continue
        code, name, date, product, vol = [x.strip() for x in rec[:5]]
        try:
            vol = int(float(vol))
        except ValueError:
            continue
        if vol <= 0:
            continue
        key = (code, date, product, src)
        if key in seen:
            continue
        seen.add(key)
        brokers[code] = name
        rows.append([code, date, product, vol, src])

if not rows:
    raise SystemExit("No data fetched - aborting so the old site stays up")

tw_today = (datetime.datetime.utcnow() + datetime.timedelta(hours=8)).date().isoformat()
data = json.dumps({"brokers": brokers, "rows": rows, "fetched": tw_today},
                  ensure_ascii=False, separators=(",", ":"))

template = open("template.html", encoding="utf-8").read()
os.makedirs("site", exist_ok=True)
open("site/index.html", "w", encoding="utf-8").write(template.replace("__DATA__", data))
dates = sorted({r[1] for r in rows})
print(f"Built site/index.html: {len(rows)} rows, {dates[0]} -> {dates[-1]} ({len(dates)} sessions)")
