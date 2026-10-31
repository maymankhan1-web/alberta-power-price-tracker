#!/usr/bin/env python3
"""Fetch public Alberta pool price data from AESO (no API key). Stdlib only."""
import csv, io, json, re, datetime, urllib.request
import sys, time, socket, urllib.error

RETRY_DELAYS = (5, 15, 30)


def _retryable(err):
    if isinstance(err, urllib.error.HTTPError):
        return err.code == 429 or err.code >= 500
    return isinstance(err, (urllib.error.URLError, TimeoutError, socket.timeout, ConnectionError))


def urlopen_retry(req, timeout=60):
    """Open a URL, retrying temporary upstream errors. Exits cleanly if the source stays down."""
    for attempt in range(len(RETRY_DELAYS) + 1):
        try:
            return urllib.request.urlopen(req, timeout=timeout)
        except Exception as err:
            if not _retryable(err):
                raise
            if attempt == len(RETRY_DELAYS):
                print(f"Source unavailable after {attempt + 1} attempts ({err}); keeping existing data.")
                sys.exit(0)
            print(f"Attempt {attempt + 1} failed ({err}); retrying in {RETRY_DELAYS[attempt]}s")
            time.sleep(RETRY_DELAYS[attempt])

from zoneinfo import ZoneInfo

SMP = "http://ets.aeso.ca/ets_web/ip/Market/Reports/CSMPriceReportServlet?contentType=csv"
HIST = "http://ets.aeso.ca/ets_web/ip/Market/Reports/HistoricalPoolPriceReportServlet?beginDate={b}&endDate={e}&contentType=csv"
TZ = ZoneInfo("America/Edmonton")

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "alberta-power-price-tracker"})
    with urlopen_retry(req, timeout=60) as r:
        return r.read().decode("utf-8", "replace")

def rows(text, header_start):
    lines = text.splitlines()
    i = next(n for n, l in enumerate(lines) if l.startswith(header_start))
    return [r for r in csv.reader(io.StringIO("\n".join(lines[i:]))) if r][1:]

def num(s):
    try: return float(s)
    except ValueError: return None

def main():
    now = datetime.datetime.now(TZ)
    smp_text = get(SMP)
    m = re.search(r"Projected Pool Price for Hour Ending (\d+) is \$([\d.,]+) as of ([\d:]+)", smp_text)
    smp = [{"hour_ending": r[0], "time": r[1], "price": num(r[2]), "volume_mw": num(r[3])}
           for r in rows(smp_text, "Date (HE)") if len(r) >= 4]
    b = (now - datetime.timedelta(days=7)).strftime("%m%d%Y"); e = now.strftime("%m%d%Y")
    hist = [{"hour_ending": r[0], "price": num(r[1]), "avg30": num(r[2]), "ail_mw": num(r[3])}
            for r in rows(get(HIST.format(b=b, e=e)), "Date (HE)") if len(r) >= 4 and num(r[1]) is not None]
    out = {
        "updated": now.isoformat(timespec="seconds"),
        "source": "AESO (Alberta Electric System Operator), ets.aeso.ca",
        "projected": {"hour_ending": int(m.group(1)), "price": float(m.group(2).replace(",", "")), "as_of": m.group(3)} if m else None,
        "smp": smp, "hourly": hist,
    }
    json.dump(out, open("data/latest.json", "w"), indent=1)
    with open("data/hourly_pool_price.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["hour_ending", "price", "avg30", "ail_mw"])
        for h in hist: w.writerow([h["hour_ending"], h["price"], h["avg30"], h["ail_mw"]])
    with open("data/system_marginal_price.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["hour_ending", "time", "price", "volume_mw"])
        for s in smp: w.writerow([s["hour_ending"], s["time"], s["price"], s["volume_mw"]])
    print(f"projected={out['projected']} hourly_rows={len(hist)} smp_rows={len(smp)}")

if __name__ == "__main__":
    main()
