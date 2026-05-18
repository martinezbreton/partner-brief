#!/usr/bin/env python3
"""Regenerate archive/manifest.json + manifest.md + archive/index.html from archive/*.html."""
import re, json, os, glob
from datetime import date

ARCHIVE = "/tmp/partner-brief/archive"

WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
MONTHS = ["January","February","March","April","May","June","July","August","September","October","November","December"]

def parse_html(path):
    html = open(path).read()
    fn = os.path.basename(path)
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})\.html", fn)
    if not m:
        return None
    y, mo, d = map(int, m.groups())
    dt = date(y, mo, d)

    h1 = re.search(r"<h1>([^<]+)</h1>", html)
    sub = re.search(r'<div class="sub">([^<]+)</div>', html)
    alert = re.search(r'<div class="alert critical">([\s\S]*?)</div>', html)

    title = h1.group(1).strip() if h1 else "Partner Brief"
    subtitle = sub.group(1).strip() if sub else ""
    top_alert = ""
    if alert:
        raw = alert.group(1)
        raw = re.sub(r"<[^>]+>", "", raw)
        raw = re.sub(r"\s+", " ", raw).strip()
        top_alert = raw

    return {
        "date": dt.isoformat(),
        "weekday": WEEKDAYS[dt.weekday()],
        "title": title,
        "subtitle": subtitle,
        "top_alert": top_alert,
        "file": fn,
        "url": f"https://martinezbreton.github.io/partner-brief/archive/{fn}",
        "_y": y, "_m": mo, "_d": d,
    }

entries = []
for path in sorted(glob.glob(f"{ARCHIVE}/*.html")):
    if path.endswith("index.html"):
        continue
    parsed = parse_html(path)
    if parsed:
        entries.append(parsed)
entries.sort(key=lambda e: (e["_y"], e["_m"], e["_d"]))

# manifest.json
json_entries = [{k:v for k,v in e.items() if not k.startswith("_")} for e in entries]
with open(f"{ARCHIVE}/manifest.json", "w") as f:
    json.dump(json_entries, f, indent=2, ensure_ascii=False)

# manifest.md
lines = [
    "# Partner Brief Archive — Manifest",
    "",
    f"_{len(entries)} entries · {entries[0]['date']} → {entries[-1]['date']}_",
    "",
    "Each row is one daily brief. The subtitle is the at-a-glance theme; the top alert is what was most urgent that day.",
    "",
]
current_month = None
for e in entries:
    mkey = (e["_y"], e["_m"])
    if mkey != current_month:
        current_month = mkey
        lines.append("")
        lines.append(f"## {MONTHS[e['_m']-1]} {e['_y']}")
        lines.append("")
    line = f"- **{e['date']}** ({e['weekday']}) — {e['title']}"
    if e['subtitle']:
        line += f" · _{e['subtitle']}_"
    if e['top_alert']:
        line += f"\n  - ⚠️ {e['top_alert']}"
    lines.append(line)
with open(f"{ARCHIVE}/manifest.md", "w") as f:
    f.write("\n".join(lines) + "\n")

# archive/index.html — browse page grouped by month, newest first
html_parts = ["""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Partner Brief Archive</title>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f4f5f7; color: #1a1a2e; margin: 0; padding: 24px 32px; max-width: 980px; }
  h1 { font-size: 24px; margin-bottom: 4px; }
  .sub { color: #777; font-size: 13px; margin-bottom: 24px; }
  h2 { font-size: 14px; text-transform: uppercase; letter-spacing: 1px; color: #555; margin-top: 28px; margin-bottom: 12px; }
  .entry { display: block; padding: 12px 14px; background: white; border-radius: 6px; margin-bottom: 6px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); text-decoration: none; color: inherit; border-left: 3px solid #0f2027; }
  .entry:hover { background: #fafbff; }
  .entry .d { font-weight: 700; font-size: 13px; }
  .entry .day { color: #888; font-size: 11px; }
  .entry .t { font-size: 12px; color: #555; margin-top: 2px; }
</style>
</head>
<body>
<h1>📁 Partner Brief Archive</h1>
<div class="sub">""" + f"{len(entries)} entries · {entries[0]['date']} → {entries[-1]['date']} · " + """<a href="../">live brief</a> · <a href="manifest.md">manifest.md</a> · <a href="manifest.json">manifest.json</a></div>
"""]
rev = list(reversed(entries))
current_month = None
for e in rev:
    mkey = (e["_y"], e["_m"])
    if mkey != current_month:
        current_month = mkey
        html_parts.append(f"<h2>{MONTHS[e['_m']-1]} {e['_y']}</h2>")
    sub = e['subtitle'].replace("<","&lt;").replace(">","&gt;")
    html_parts.append(
        f'<a class="entry" href="{e["file"]}">'
        f'<span class="d">{e["date"]}</span> <span class="day">({e["weekday"]})</span>'
        f'<div class="t">{sub}</div></a>'
    )
html_parts.append("</body></html>")
with open(f"{ARCHIVE}/index.html", "w") as f:
    f.write("\n".join(html_parts))

print(f"Regenerated: {len(entries)} entries → manifest.json, manifest.md, index.html")
print(f"Latest: {entries[-1]['date']} — {entries[-1]['title']}")
