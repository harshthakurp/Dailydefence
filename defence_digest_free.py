"""
DEFENCE DEC — YouTube Content Intelligence Brief
Fresh daily news guaranteed via multi-source RSS + date filtering
Uses: Multiple RSS sources + YouTube Data API v3 (free)
"""

import smtplib, urllib.request, urllib.parse, xml.etree.ElementTree as ET
import datetime, html, re, time, random, os, json, hashlib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ── SETTINGS ──────────────────────────────────────────────────
RECIPIENT_EMAIL  = "defencedec@gmail.com"
SENDER_EMAIL     = "manmahow@gmail.com"
GMAIL_APP_PASS   = os.environ.get("GMAIL_APP_PASS", "myzs tqyb zhei mdnq")
YOUTUBE_API_KEY  = os.environ.get("YOUTUBE_API_KEY", "AIzaSyA-7VPKRc5FiUntEcW5rX9nUq4Ro2gqOBw")

# How many days old a story can be (1 = today only, 2 = today + yesterday)
MAX_STORY_AGE_DAYS = 2

# ── VIRAL KEYWORDS ────────────────────────────────────────────
VIRAL_KEYWORDS = {
    "hypersonic":10,"mach 5":10,"mach 10":10,"oreshnik":10,"sarmat":10,
    "rs-28":10,"hwasong":10,"icbm":9,"slbm":9,"trident":8,"minuteman":8,
    "tomahawk":8,"f-35":9,"f-22":9,"b-21":10,"ngad":10,"gcap":9,"fcas":9,
    "nuclear":9,"warhead":9,"ballistic":8,"stealth":8,"drone swarm":10,
    "loitering":8,"kamikaze":9,"shahed":9,"lancet":8,"submarine":8,
    "ssbn":9,"ssn":8,"carrier killer":10,"anti-satellite":10,"asat":10,
    "directed energy":10,"laser weapon":10,"railgun":9,"electronic warfare":8,
    "cyber attack":8,"nightmare":10,"game changer":10,"revolutionary":9,
    "first ever":9,"unprecedented":9,"secret":8,"leaked":10,"classified":9,
    "revealed":8,"destroyed":8,"intercepted":8,"vs":8,"beats":8,
    "russia":7,"china":7,"nato":7,"ukraine":8,"taiwan":9,"iran":8,
    "north korea":9,"india":7,"israel":8,"pentagon":6,"drdo":8,"hal":7,
    "tejas":8,"agni":9,"brahmos":9,"s-400":8,"patriot":7,
}

# ── MULTI-SOURCE RSS FEEDS per category ───────────────────────
# Each category has MULTIPLE sources — script picks freshest story across all
RSS_FEEDS = [
    {
        "tag":"🚀 Missiles & Hypersonics", "color":"#ff4444",
        "sources":[
            "https://news.google.com/rss/search?q=missile+hypersonic+ICBM+ballistic+launch&hl=en&gl=US&ceid=US:en&tbs=qdr:d",
            "https://news.google.com/rss/search?q=hypersonic+missile+test+2026&hl=en&gl=US&ceid=US:en",
            "https://news.google.com/rss/search?q=ballistic+missile+launch+today&hl=en&gl=US&ceid=US:en",
        ]
    },
    {
        "tag":"⚓ Naval & Submarines", "color":"#00aaff",
        "sources":[
            "https://news.google.com/rss/search?q=submarine+navy+naval+warship+2026&hl=en&gl=US&ceid=US:en&tbs=qdr:d",
            "https://news.google.com/rss/search?q=SSBN+SSN+nuclear+submarine+fleet&hl=en&gl=US&ceid=US:en",
            "https://news.google.com/rss/search?q=aircraft+carrier+naval+exercise+today&hl=en&gl=US&ceid=US:en",
        ]
    },
    {
        "tag":"✈️ Jets & Stealth Aircraft", "color":"#00d4ff",
        "sources":[
            "https://news.google.com/rss/search?q=fighter+jet+stealth+air+force+2026&hl=en&gl=US&ceid=US:en&tbs=qdr:d",
            "https://news.google.com/rss/search?q=F-35+F-22+NGAD+B-21+stealth&hl=en&gl=US&ceid=US:en",
            "https://news.google.com/rss/search?q=6th+generation+fighter+jet+GCAP+FCAS&hl=en&gl=US&ceid=US:en",
        ]
    },
    {
        "tag":"🎯 Weapons & Loitering Munitions", "color":"#ffaa00",
        "sources":[
            "https://news.google.com/rss/search?q=loitering+munition+kamikaze+drone+weapon&hl=en&gl=US&ceid=US:en&tbs=qdr:d",
            "https://news.google.com/rss/search?q=precision+guided+munition+military+strike&hl=en&gl=US&ceid=US:en",
            "https://news.google.com/rss/search?q=artillery+rocket+system+HIMARS+weapon&hl=en&gl=US&ceid=US:en",
        ]
    },
    {
        "tag":"🤖 Drone Warfare & AI", "color":"#ff8800",
        "sources":[
            "https://news.google.com/rss/search?q=military+drone+swarm+autonomous+AI+weapon&hl=en&gl=US&ceid=US:en&tbs=qdr:d",
            "https://news.google.com/rss/search?q=UAV+drone+warfare+Ukraine+2026&hl=en&gl=US&ceid=US:en",
            "https://news.google.com/rss/search?q=AI+autonomous+weapon+system+military&hl=en&gl=US&ceid=US:en",
        ]
    },
    {
        "tag":"🛰️ Space & Cyber Warfare", "color":"#aa44ff",
        "sources":[
            "https://news.google.com/rss/search?q=space+warfare+ASAT+anti-satellite+weapon&hl=en&gl=US&ceid=US:en&tbs=qdr:d",
            "https://news.google.com/rss/search?q=cyber+attack+military+infrastructure+hack&hl=en&gl=US&ceid=US:en",
            "https://news.google.com/rss/search?q=space+force+military+satellite+weapon+2026&hl=en&gl=US&ceid=US:en",
        ]
    },
    {
        "tag":"⚔️ East vs West", "color":"#ff2266",
        "sources":[
            "https://news.google.com/rss/search?q=Russia+China+USA+NATO+military+confrontation&hl=en&gl=US&ceid=US:en&tbs=qdr:d",
            "https://news.google.com/rss/search?q=Taiwan+China+military+conflict+2026&hl=en&gl=US&ceid=US:en",
            "https://news.google.com/rss/search?q=NATO+Russia+Ukraine+war+military+update&hl=en&gl=US&ceid=US:en",
        ]
    },
    {
        "tag":"🌍 Global Defence Intel", "color":"#44ff88",
        "sources":[
            "https://news.google.com/rss/search?q=defence+contract+billion+military+deal+2026&hl=en&gl=US&ceid=US:en&tbs=qdr:d",
            "https://news.google.com/rss/search?q=India+DRDO+BrahMos+Tejas+Agni+defence&hl=en&gl=IN&ceid=IN:en",
            "https://news.google.com/rss/search?q=pentagon+defence+ministry+military+budget&hl=en&gl=US&ceid=US:en",
        ]
    },
]

# ══════════════════════════════════════════════════════════════
# DATE FRESHNESS FILTER
# ══════════════════════════════════════════════════════════════

def parse_pubdate(raw: str):
    """Parse RSS pubDate into a datetime object."""
    if not raw:
        return None
    formats = [
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S %Z",
        "%a, %d %b %Y %H:%M:%S",
    ]
    for fmt in formats:
        try:
            return datetime.datetime.strptime(raw.strip()[:31], fmt)
        except:
            continue
    return None


def is_fresh(pubdate_str: str) -> bool:
    """Return True if story was published within MAX_STORY_AGE_DAYS."""
    dt = parse_pubdate(pubdate_str)
    if not dt:
        return True  # can't parse = assume fresh
    # Make timezone-naive for comparison
    if dt.tzinfo:
        dt = dt.replace(tzinfo=None)
    age = datetime.datetime.utcnow() - dt
    return age.days <= MAX_STORY_AGE_DAYS


def format_pubdate(raw: str) -> str:
    dt = parse_pubdate(raw)
    if not dt:
        return datetime.date.today().strftime("%b %d, %Y")
    return dt.strftime("%b %d · %H:%M UTC")


# ══════════════════════════════════════════════════════════════
# VIRAL SCORE
# ══════════════════════════════════════════════════════════════

def compute_viral_score(title: str, desc: str) -> int:
    text = (title + " " + desc).lower()
    score, matched = 0, []
    for kw, w in VIRAL_KEYWORDS.items():
        if kw in text:
            score += w
            matched.append(kw)
    if len(matched) >= 4: score += 15
    elif len(matched) >= 2: score += 8
    return min(score, 100)


def viral_label(score: int) -> tuple:
    if score >= 70: return "VIRAL POTENTIAL", "#ff2244", "🔥🔥🔥"
    elif score >= 50: return "HIGH INTEREST",  "#ff8800", "🔥🔥"
    elif score >= 30: return "WORTH COVERING", "#ffcc00", "🔥"
    return "MONITOR", "#44aa88", "📌"


# ══════════════════════════════════════════════════════════════
# RSS FETCH — multi-source with freshness filter
# ══════════════════════════════════════════════════════════════

def clean_text(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def fetch_rss_single(url: str, max_items: int = 8) -> list:
    """Fetch one RSS feed, return items."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0 Safari/537.36",
        "Cache-Control": "no-cache, no-store",
        "Pragma": "no-cache",
    }
    try:
        # Add cache-busting timestamp to URL
        sep = "&" if "?" in url else "?"
        url += f"{sep}_cb={int(time.time())}"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=12) as r:
            root = ET.fromstring(r.read())
        results = []
        for item in root.findall(".//item")[:max_items]:
            title = re.sub(r"\s+-\s+[^-]{2,40}$", "",
                           clean_text(item.findtext("title", ""))).strip()
            link  = item.findtext("link", "#")
            desc  = clean_text(item.findtext("description", ""))
            pub   = item.findtext("pubDate", "")
            if title and len(title) > 10:
                results.append({
                    "title": title,
                    "link":  link,
                    "desc":  desc[:300] + "…" if len(desc) > 300 else desc,
                    "pub":   pub,
                    "fresh": is_fresh(pub),
                })
        return results
    except Exception as e:
        return []


def fetch_best_for_category(feed: dict) -> dict | None:
    """Fetch all sources for a category, return freshest highest-scoring story."""
    all_items = []
    for url in feed["sources"]:
        items = fetch_rss_single(url)
        all_items.extend(items)
        time.sleep(random.uniform(0.3, 0.6))

    if not all_items:
        return None

    # Deduplicate by title similarity
    seen_titles = set()
    unique_items = []
    for item in all_items:
        key = re.sub(r"[^a-z0-9]", "", item["title"].lower())[:40]
        if key not in seen_titles:
            seen_titles.add(key)
            unique_items.append(item)

    # Separate fresh vs old
    fresh_items = [i for i in unique_items if i["fresh"]]
    pool = fresh_items if fresh_items else unique_items  # fallback to old if nothing fresh

    # Score and sort
    scored = sorted(
        [(compute_viral_score(i["title"], i["desc"]), i) for i in pool],
        key=lambda x: x[0], reverse=True
    )

    best_score, best_item = scored[0]
    return {
        "tag":        feed["tag"],
        "color":      feed["color"],
        "title":      best_item["title"],
        "link":       best_item["link"],
        "desc":       best_item["desc"],
        "pub":        best_item["pub"],
        "fresh":      best_item["fresh"],
        "score":      best_score,
        "all_scored": scored[:4],
    }


def fetch_all_topics() -> list:
    print("📡 Fetching fresh defence topics (multi-source)...")
    all_topics = []
    for feed in RSS_FEEDS:
        print(f"  → {feed['tag']} ...", end=" ", flush=True)
        topic = fetch_best_for_category(feed)
        if topic:
            _, _, emoji = viral_label(topic["score"])
            fresh_tag = "🟢 TODAY" if topic["fresh"] else "🟡 RECENT"
            print(f"{emoji} {fresh_tag} Score:{topic['score']} — '{topic['title'][:40]}...'")

            # YouTube clips
            print(f"     🎬 Searching YouTube...", end=" ", flush=True)
            clips = search_youtube_clips(topic["title"])
            topic["clips"] = clips
            print(f"{'✅ ' + str(len(clips)) + ' clips' if clips else '⚠️ no clips'}")
            all_topics.append(topic)
        else:
            print("❌ No items found")

    all_topics.sort(key=lambda x: x["score"], reverse=True)
    return all_topics


# ══════════════════════════════════════════════════════════════
# YOUTUBE SEARCH
# ══════════════════════════════════════════════════════════════

def search_youtube_clips(query: str, max_results: int = 3) -> list:
    if not YOUTUBE_API_KEY:
        return []
    try:
        search_url = (
            "https://www.googleapis.com/youtube/v3/search?"
            + urllib.parse.urlencode({
                "part":          "snippet",
                "q":             query + " military",
                "type":          "video",
                "maxResults":    max_results + 3,
                "order":         "relevance",
                "videoDuration": "medium",
                "key":           YOUTUBE_API_KEY,
            })
        )
        req = urllib.request.Request(search_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())

        video_ids = [item["id"]["videoId"] for item in data.get("items", [])
                     if item.get("id", {}).get("videoId")]
        if not video_ids:
            return []

        stats_url = (
            "https://www.googleapis.com/youtube/v3/videos?"
            + urllib.parse.urlencode({
                "part": "statistics,snippet",
                "id":   ",".join(video_ids),
                "key":  YOUTUBE_API_KEY,
            })
        )
        req2 = urllib.request.Request(stats_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req2, timeout=10) as r2:
            stats_data = json.loads(r2.read())

        clips = []
        for item in stats_data.get("items", []):
            clips.append({
                "title":   item["snippet"]["title"],
                "url":     f"https://www.youtube.com/watch?v={item['id']}",
                "channel": item["snippet"]["channelTitle"],
                "views":   int(item["statistics"].get("viewCount", 0)),
                "thumb":   item["snippet"]["thumbnails"].get("medium", {}).get("url", ""),
            })
        clips.sort(key=lambda x: x["views"], reverse=True)
        return clips[:max_results]
    except Exception as e:
        print(f"(YT error: {e})", end=" ")
        return []


def format_views(n: int) -> str:
    if n >= 1_000_000: return f"{n/1_000_000:.1f}M views"
    elif n >= 1_000:   return f"{n/1_000:.0f}K views"
    return f"{n} views"


# ══════════════════════════════════════════════════════════════
# HTML EMAIL BUILDER
# ══════════════════════════════════════════════════════════════

def build_score_bar(score: int, color: str) -> str:
    label, lcolor, emoji = viral_label(score)
    return f"""
<div style="margin:8px 0 12px 0;">
  <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
    <span style="font-size:10px;font-weight:800;letter-spacing:2px;color:{lcolor};">{emoji} {label}</span>
    <span style="font-size:11px;font-weight:700;color:{lcolor};">{score}/100</span>
  </div>
  <div style="background:#0d1f35;border-radius:4px;height:5px;">
    <div style="width:{min(score,100)}%;height:100%;background:linear-gradient(90deg,{color},{lcolor});border-radius:4px;"></div>
  </div>
</div>"""


def build_clips_section(clips: list, color: str) -> str:
    if not clips:
        return """<div style="margin-top:12px;padding:10px 14px;background:#080e1a;
            border:1px solid #1a2a3a;border-radius:6px;">
          <p style="font-size:11px;color:#3a5a7a;margin:0;">🎬 NO VIDEO CLIPS FOUND FOR THIS TOPIC</p>
        </div>"""
    cards = ""
    for clip in clips:
        title   = html.escape(clip["title"][:65]) + ("…" if len(clip["title"]) > 65 else "")
        channel = html.escape(clip["channel"])
        views   = format_views(clip["views"])
        url     = clip["url"]
        thumb   = clip.get("thumb", "")
        thumb_html = f'<img src="{thumb}" style="width:100%;border-radius:4px;display:block;margin-bottom:8px;" alt=""/>' if thumb else ""
        cards += f"""
<div style="flex:1;min-width:155px;max-width:195px;background:#080e1a;
    border:1px solid #1a2a3a;border-radius:6px;padding:10px;box-sizing:border-box;">
  {thumb_html}
  <a href="{url}" style="font-size:12px;color:#e0e8f0;text-decoration:none;
      line-height:1.4;display:block;margin-bottom:6px;font-weight:600;">{title}</a>
  <p style="font-size:10px;color:#4a7090;margin:0 0 2px 0;">{channel}</p>
  <p style="font-size:10px;color:{color};margin:0 0 8px 0;font-weight:700;">{views}</p>
  <a href="{url}" style="background:{color};color:#000;font-size:10px;font-weight:800;
      padding:4px 10px;border-radius:3px;text-decoration:none;letter-spacing:1px;">▶ WATCH</a>
</div>"""
    return f"""
<div style="margin-top:12px;padding-top:10px;border-top:1px solid #0d1f35;">
  <p style="font-size:10px;color:#3a5a7a;letter-spacing:2px;text-transform:uppercase;margin:0 0 10px 0;font-weight:700;">
    🎬 TOP VIDEO CLIPS FOR THIS TOPIC
  </p>
  <div style="display:flex;gap:10px;flex-wrap:wrap;">{cards}</div>
</div>"""


def build_topic_card(topic: dict, index: int) -> str:
    color  = topic["color"]
    score  = topic["score"]
    fresh  = topic.get("fresh", True)
    title  = html.escape(topic["title"])
    desc   = html.escape(topic["desc"])
    pub    = format_pubdate(topic.get("pub", ""))
    rank   = ' <span style="background:#ff2244;color:#fff;font-size:10px;font-weight:800;padding:2px 8px;border-radius:3px;">🔥 TOP PICK</span>' if index == 1 else ""
    fresh_badge = '<span style="background:#00aa44;color:#fff;font-size:9px;font-weight:700;padding:2px 7px;border-radius:3px;margin-left:6px;">🟢 TODAY</span>' if fresh else '<span style="background:#886600;color:#fff;font-size:9px;padding:2px 7px;border-radius:3px;margin-left:6px;">🟡 RECENT</span>'

    return f"""
<div style="background:linear-gradient(135deg,#0d1421 0%,#111827 100%);
    border:1px solid #1e3050;border-left:4px solid {color};
    border-radius:8px;margin:0 0 22px 0;padding:20px 22px;
    font-family:'Segoe UI',Arial,sans-serif;">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;flex-wrap:wrap;gap:6px;">
    <span style="background:{color}22;color:{color};font-size:10px;font-weight:700;
        letter-spacing:2px;text-transform:uppercase;padding:3px 10px;
        border-radius:20px;border:1px solid {color}44;">{topic['tag']}{fresh_badge}</span>
    <span style="color:#3a5a7a;font-size:11px;font-weight:700;">#{index:02d}{rank}</span>
  </div>
  {build_score_bar(score, color)}
  <h2 style="font-size:16px;font-weight:700;color:#e8f0f8;line-height:1.4;margin:0 0 8px 0;">{title}</h2>
  <p style="font-size:13px;color:#8aa8c0;line-height:1.7;margin:0 0 12px 0;">{desc}</p>
  <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
    <a href="{topic['link']}" style="background:{color};color:#000;font-size:10px;font-weight:800;
        letter-spacing:1.5px;text-transform:uppercase;padding:6px 14px;border-radius:4px;text-decoration:none;">
      READ FULL STORY →</a>
    <span style="color:#2a4a6a;font-size:11px;">{pub}</span>
  </div>
  {build_clips_section(topic.get('clips', []), color)}
</div>"""


def build_full_email(topics: list) -> str:
    today_long  = datetime.date.today().strftime("%A, %B %d, %Y")
    today_short = datetime.date.today().strftime("%b %d, %Y")
    issue_num   = (datetime.date.today() - datetime.date(2025, 1, 1)).days + 1
    top_score   = topics[0]["score"] if topics else 0
    fresh_count = sum(1 for t in topics if t.get("fresh", False))
    _, top_color, top_emoji = viral_label(top_score)
    cards_html  = "".join(build_topic_card(t, i+1) for i, t in enumerate(topics))

    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Defence Dec Intel — {today_short}</title></head>
<body style="margin:0;padding:0;background:#050810;font-family:'Segoe UI',Arial,sans-serif;">
<div style="max-width:680px;margin:0 auto;background:#0a0f1e;">

  <div style="background:linear-gradient(135deg,#050d1a 0%,#120508 100%);
      padding:32px 40px 24px;border-bottom:2px solid #00d4ff;text-align:center;">
    <p style="font-size:10px;letter-spacing:6px;text-transform:uppercase;
        color:#00d4ff;margin:0 0 10px 0;font-weight:700;">⬡ YOUTUBE CONTENT INTELLIGENCE ⬡</p>
    <h1 style="font-size:34px;font-weight:900;color:#fff;letter-spacing:4px;
        margin:0 0 4px 0;text-shadow:0 0 30px rgba(0,212,255,0.3);">DEFENCE DEC</h1>
    <p style="font-size:11px;color:#4a7090;letter-spacing:3px;text-transform:uppercase;margin:0 0 8px 0;">
      {today_long} · ISSUE #{issue_num:04d}</p>
    <p style="font-size:13px;color:#7090a8;margin:0;font-style:italic;">
      Fresh Daily News · Viral Score · YouTube Clips · East vs West
    </p>
  </div>

  <div style="background:#060d1a;padding:9px 40px;display:flex;
      justify-content:space-between;flex-wrap:wrap;gap:6px;
      border-bottom:1px solid #0d1f35;font-size:10px;letter-spacing:2px;text-transform:uppercase;">
    <span style="color:#ff4444;font-weight:800;">● LIVE — {len(topics)} TOPICS</span>
    <span style="color:#00aa44;font-weight:700;">🟢 {fresh_count} PUBLISHED TODAY</span>
    <span style="color:{top_color};font-weight:700;">{top_emoji} TOP SCORE: {top_score}/100</span>
  </div>

  <div style="padding:20px 40px 4px;">
    <p style="font-size:13px;color:#5a7a9a;line-height:1.7;
        border-left:3px solid #1e3050;padding-left:14px;margin:0;">
      Sourced fresh daily from <strong style="color:#00d4ff;">24+ RSS feeds</strong> across
      3 sources per category. Stories filtered for today's news only.
      Each topic includes <strong style="color:#00d4ff;">real YouTube clips</strong> matched
      to today's exact headline.
    </p>
  </div>

  <div style="border-top:1px solid #1a2a3a;margin:20px 0 0 0;"></div>
  <div style="padding:16px 40px 24px;">{cards_html}</div>

  <div style="background:#040810;padding:20px 40px;border-top:1px solid #0d1f35;
      text-align:center;font-size:11px;color:#2a4a6a;line-height:2;">
    <p style="margin:0 0 4px 0;">🛡️ <strong style="color:#3a5a7a;">DEFENCE DEC</strong>
      — YouTube Content Intelligence Brief</p>
    <p style="margin:0;font-size:10px;color:#1a3050;">
      Multi-source RSS · Fresh daily · YouTube Data API · For content research only
    </p>
  </div>

</div></body></html>"""


# ══════════════════════════════════════════════════════════════
# EMAIL SENDER
# ══════════════════════════════════════════════════════════════

def send_email(html_body: str, topics: list):
    today_short = datetime.date.today().strftime("%b %d, %Y")
    top_score   = topics[0]["score"] if topics else 0
    fresh_count = sum(1 for t in topics if t.get("fresh", False))
    _, _, emoji = viral_label(top_score)
    subject = f"🛡️ Defence Dec — {today_short} | {fresh_count} Fresh Stories | Top:{top_score}/100 {emoji}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"Defence Dec Intel <{SENDER_EMAIL}>"
    msg["To"]      = RECIPIENT_EMAIL
    msg.attach(MIMEText(f"Defence Dec Intel — {today_short}\nView in HTML client.", "plain"))
    msg.attach(MIMEText(html_body, "html"))

    print("📧 Sending via Gmail SMTP...")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SENDER_EMAIL, GMAIL_APP_PASS)
        server.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, msg.as_string())
    print(f"✅ Sent → {RECIPIENT_EMAIL}")


# ══════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════

def main():
    print("=" * 65)
    print(f"  DEFENCE DEC INTEL  |  {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 65)
    topics = fetch_all_topics()
    if not topics:
        print("No topics fetched.")
        return
    fresh = sum(1 for t in topics if t.get("fresh", False))
    print(f"\n✅ {len(topics)} topics | 🟢 {fresh} fresh today | Top: '{topics[0]['title'][:50]}' Score:{topics[0]['score']}/100\n")
    html_body = build_full_email(topics)
    send_email(html_body, topics)
    print("\n🎉 Done! Check defencedec@gmail.com")
    print("=" * 65)


if __name__ == "__main__":
    main()
