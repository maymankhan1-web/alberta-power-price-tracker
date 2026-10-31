#!/usr/bin/env python3
"""Check saved AESO data for price spikes or drops. Stdlib only. Sends nothing.

Usage: python3 alert.py [--high 200] [--low 10] [--jump 100]
Writes data/alerts.json and exits 1 if any alert fired (handy for CI).
"""
import argparse, json, sys

ap = argparse.ArgumentParser()
ap.add_argument("--high", type=float, default=200.0, help="alert if projected/last price >= this ($/MWh)")
ap.add_argument("--low", type=float, default=10.0, help="alert if projected/last price <= this ($/MWh)")
ap.add_argument("--jump", type=float, default=100.0, help="alert if price moved this much vs previous hour ($/MWh)")
a = ap.parse_args()

d = json.load(open("data/latest.json"))
hourly = [h for h in d["hourly"] if h["price"] is not None]
proj = d.get("projected")
cur = proj["price"] if proj else (hourly[-1]["price"] if hourly else None)
prev = hourly[-1]["price"] if hourly else None
alerts = []
if cur is not None and cur >= a.high:
    alerts.append(f"SPIKE: Alberta pool price ${cur:.2f}/MWh is at or above ${a.high:.2f}")
if cur is not None and cur <= a.low:
    alerts.append(f"DROP: Alberta pool price ${cur:.2f}/MWh is at or below ${a.low:.2f}")
if cur is not None and prev is not None and abs(cur - prev) >= a.jump:
    alerts.append(f"JUMP: price moved ${cur - prev:+.2f}/MWh vs last settled hour (${prev:.2f})")
out = {"checked": d["updated"], "current": cur, "previous_hour": prev,
       "thresholds": vars(a), "alerts": alerts, "source": "AESO"}
json.dump(out, open("data/alerts.json", "w"), indent=1)
print(json.dumps(out, indent=1))
sys.exit(1 if alerts else 0)
