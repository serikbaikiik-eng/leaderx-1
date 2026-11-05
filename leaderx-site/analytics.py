"""Келушілер статистикасы (SQLite). Толық IP, шамамен орны (ел/қала), құрылғы және қайдан келгені сақталады."""
import hashlib, ipaddress, os, re, sqlite3, time
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

DB_PATH = os.environ.get("VISITS_DB", os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "visits.db"))
SALT = os.environ.get("VISIT_SALT", "leaderx-change-me")
TZ = timezone(timedelta(hours=int(os.environ.get("ADMIN_TZ_OFFSET", "5"))))  # Қазақстан UTC+5
RETENTION_DAYS = int(os.environ.get("VISITS_RETENTION_DAYS", "180"))
GEO_DB = os.environ.get("GEOIP_DB", os.path.join(os.path.dirname(DB_PATH), "GeoLite2-City.mmdb"))
_geo = {"r": None, "tried": False}
_clean = {"t": 0}
BOT_RE = re.compile(r"bot|spider|crawl|slurp|preview|monitor|uptime|curl|wget|python-requests|facebookexternalhit|headless", re.I)


def _db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    con = sqlite3.connect(DB_PATH, timeout=5)
    con.row_factory = sqlite3.Row
    con.execute("""CREATE TABLE IF NOT EXISTS visits(
        id INTEGER PRIMARY KEY AUTOINCREMENT, ts INTEGER NOT NULL, path TEXT, lang TEXT,
        ip_mask TEXT, ip_hash TEXT, device TEXT, browser TEXT, os TEXT, referrer TEXT)""")
    cols = {r[1] for r in con.execute("PRAGMA table_info(visits)")}
    for c in ("country", "city", "ip", "ref_url"):
        if c not in cols:
            con.execute(f"ALTER TABLE visits ADD COLUMN {c} TEXT")
    con.execute("CREATE INDEX IF NOT EXISTS idx_ts ON visits(ts)")
    return con


def _geo_lookup(req, ip):
    """(ел, қала). 1) Cloudflare тақырыбы, 2) MaxMind GeoLite2 файлы (болса). Болмаса бос."""
    try:
        a = ipaddress.ip_address(ip)
        if a.is_private or a.is_loopback:
            return "local", ""  # өз компьютеріңізден тексергенде
    except ValueError:
        pass
    cc = (req.headers.get("CF-IPCountry") or "").upper()
    if cc and cc not in ("XX", "T1"):
        return cc, (req.headers.get("CF-IPCity") or "")
    if not _geo["tried"]:
        _geo["tried"] = True
        try:
            import geoip2.database
            if os.path.exists(GEO_DB):
                _geo["r"] = geoip2.database.Reader(GEO_DB)
        except Exception:
            _geo["r"] = None
    if _geo["r"] and ip:
        try:
            r = _geo["r"].city(ip)
            return (r.country.iso_code or ""), (r.city.name or "")
        except Exception:
            pass
    return "", ""


def _mask(ip):
    if ":" in ip:  # IPv6: алғашқы 3 блок
        return ":".join(ip.split(":")[:3]) + "::"
    p = ip.split(".")
    return ".".join(p[:3] + ["0"]) if len(p) == 4 else "?"


def _ua(ua):
    low = ua.lower()
    device = "tablet" if ("ipad" in low or "tablet" in low) else ("mobile" if ("mobi" in low or "android" in low or "iphone" in low) else "desktop")
    browser = next((n for k, n in (("edg", "Edge"), ("opr", "Opera"), ("yabrowser", "Yandex"), ("firefox", "Firefox"), ("chrome", "Chrome"), ("safari", "Safari")) if k in low), "Other")
    os_ = next((n for k, n in (("windows", "Windows"), ("android", "Android"), ("iphone", "iOS"), ("ipad", "iOS"), ("mac os", "macOS"), ("linux", "Linux")) if k in low), "Other")
    return device, browser, os_


def log_visit(req, lang):
    ua = req.headers.get("User-Agent", "")
    if not ua or BOT_RE.search(ua):
        return
    ip = (req.headers.get("True-Client-IP") or req.headers.get("CF-Connecting-IP")
          or req.headers.get("X-Forwarded-For", "").split(",")[0].strip() or req.remote_addr or "").strip()
    ref = (req.args.get("src") or "")[:40]
    ref_url = ""
    if req.referrer:
        host = urlparse(req.referrer).netloc
        if host != req.host:
            ref_url = req.referrer[:300]  # толық сілтеме (қайдан келгені)
            ref = ref or host
    device, browser, os_ = _ua(ua)
    country, city = _geo_lookup(req, ip)
    h = hashlib.sha256((SALT + ip).encode()).hexdigest()[:16]
    try:
        con = _db()
        con.execute("INSERT INTO visits(ts,path,lang,ip_mask,ip_hash,device,browser,os,referrer,country,city,ip,ref_url) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (int(time.time()), req.path, lang, _mask(ip), h, device, browser, os_, ref, country, city, ip, ref_url))
        if time.time() - _clean["t"] > 86400:  # күніне бір рет ескі жазбаларды автоматты өшіру
            _clean["t"] = time.time()
            con.execute("DELETE FROM visits WHERE ts < ?", (int(time.time()) - RETENTION_DAYS * 86400,))
        con.commit(); con.close()
    except sqlite3.Error:
        pass  # статистика сайтты құлатпауы керек


def _top(con, col, since, limit=8):
    return [(r[0] or "—", r[1]) for r in con.execute(
        f"SELECT {col}, COUNT(*) c FROM visits WHERE ts>=? GROUP BY {col} ORDER BY c DESC LIMIT ?", (since, limit))]


def stats(days=14):
    con = _db()
    now = datetime.now(TZ)
    start_today = int(now.replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
    since = start_today - (days - 1) * 86400
    q = lambda sql, *a: con.execute(sql, a).fetchone()[0]
    out = {
        "total": q("SELECT COUNT(*) FROM visits"),
        "unique_total": q("SELECT COUNT(DISTINCT ip_hash) FROM visits"),
        "today": q("SELECT COUNT(*) FROM visits WHERE ts>=?", start_today),
        "unique_today": q("SELECT COUNT(DISTINCT ip_hash) FROM visits WHERE ts>=?", start_today),
        "period_days": days, "keep": RETENTION_DAYS,
        "pages": _top(con, "path", since), "langs": _top(con, "lang", since, 3),
        "devices": _top(con, "device", since, 3), "browsers": _top(con, "browser", since, 6),
        "oses": _top(con, "os", since, 6), "countries": _top(con, "country", since, 8), "cities": _top(con, "city", since, 8), "referrers": _top(con, "referrer", since, 8),
    }
    per = {}
    for r in con.execute("SELECT ts, ip_hash FROM visits WHERE ts>=?", (since,)):
        d = datetime.fromtimestamp(r["ts"], TZ).strftime("%d.%m")
        v = per.setdefault(d, [0, set()]); v[0] += 1; v[1].add(r["ip_hash"])
    series = []
    for i in range(days):
        d = (now - timedelta(days=days - 1 - i)).strftime("%d.%m")
        series.append({"day": d, "views": per.get(d, [0, set()])[0], "uniq": len(per.get(d, [0, set()])[1])})
    mx = max([s["views"] for s in series] + [1])
    for s in series:
        s["h"] = round(s["views"] / mx * 100)
    out["series"] = series
    out["recent"] = [dict(r, time=datetime.fromtimestamp(r["ts"], TZ).strftime("%d.%m %H:%M"))
                     for r in con.execute("SELECT * FROM visits ORDER BY id DESC LIMIT 100")]
    con.close()
    return out
