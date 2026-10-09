"""Fetch TAIFEX FCM daily data (current + previous month) and build site/index.html."""
import csv, io, json, os, datetime, urllib.request

BASE = "https://www.taifex.com.tw/enl/eng7"
URLS = {"daily": [], "monthly": []}
for kind in ("Daily", "Monthly"):
    for endpoint in ("getFCMFileOpen", "getFCMFilePreOpen"):
        for prod, src in (("FUT", "F"), ("OPT", "O")):
            URLS[kind.lower()].append((f"{BASE}/{endpoint}?filename={kind}_{prod}_OpenData.csv", src))

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8-sig")

brokers = {}
def load(url_list):
    rows, seen = [], set()
    for url, src in url_list:
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
    return rows

daily = load(URLS["daily"])
monthly = load(URLS["monthly"])
if not daily or not monthly:
    raise SystemExit("No data fetched - aborting so the old site stays up")

tw_today = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=8)).date().isoformat()
data = json.dumps({"brokers": brokers, "daily": daily, "monthly": monthly, "fetched": tw_today},
                  ensure_ascii=False, separators=(",", ":"))

template = open("template.html", encoding="utf-8").read()
os.makedirs("site", exist_ok=True)
open("site/index.html", "w", encoding="utf-8").write(template.replace("__DATA__", data))
d = sorted({r[1] for r in daily}); m = sorted({r[1] for r in monthly})
print(f"Built site/index.html: daily {d[0]}->{d[-1]} ({len(d)} sessions), monthly {m[0]}->{m[-1]} ({len(m)} months)")
