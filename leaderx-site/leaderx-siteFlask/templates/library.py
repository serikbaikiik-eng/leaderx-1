"""LeaderX кітапханасы: конспектілер (lesson), кітаптар (book), көшбасшылар (leader).
Мәтін — SQLite (visits.db ішіндегі `lib_items`), жүктелген файлдар — сол дерек папкасындағы `library_files/`.
Бірінші іске қосқанда library_seed.json-дағы бастапқы материалдар базаға бір рет қосылады."""
import json, os, re, secrets, sqlite3, time

import analytics
from team import clean_text

KINDS = ("lesson", "book", "leader")
MAX_FILE = 30 * 1024 * 1024
LIB_DIR = os.path.join(os.path.dirname(analytics.DB_PATH), "library_files")
SEED = os.path.join(os.path.dirname(os.path.abspath(__file__)), "library_seed.json")
LEVELS = ("Бастапқы", "Орта")


def _db():
    os.makedirs(os.path.dirname(analytics.DB_PATH), exist_ok=True)
    con = sqlite3.connect(analytics.DB_PATH, timeout=5)
    con.row_factory = sqlite3.Row
    con.execute("""CREATE TABLE IF NOT EXISTS lib_items(
        id TEXT PRIMARY KEY, kind TEXT NOT NULL, pos INTEGER NOT NULL DEFAULT 0, active INTEGER NOT NULL DEFAULT 1,
        title TEXT NOT NULL, author TEXT NOT NULL DEFAULT '', category TEXT NOT NULL DEFAULT '', level TEXT NOT NULL DEFAULT '',
        course INTEGER NOT NULL DEFAULT 1, minutes INTEGER NOT NULL DEFAULT 5, description TEXT NOT NULL DEFAULT '',
        lead TEXT NOT NULL DEFAULT '', body TEXT NOT NULL DEFAULT '', tags TEXT NOT NULL DEFAULT '[]', extra TEXT NOT NULL DEFAULT '{}',
        file_ext TEXT, file_name TEXT, file_size INTEGER, updated INTEGER NOT NULL DEFAULT 0)""")
    con.execute("CREATE INDEX IF NOT EXISTS idx_lib_kind ON lib_items(kind, pos)")
    con.execute("CREATE TABLE IF NOT EXISTS lib_meta(k TEXT PRIMARY KEY, v TEXT)")
    return con


def _row(r):
    d = {k: r[k] for k in r.keys()}
    d["tags"] = json.loads(d["tags"] or "[]")
    d["extra"] = json.loads(d["extra"] or "{}")
    d["active"] = bool(d["active"])
    d["has_file"] = bool(d["file_ext"])
    return d


# ------------------------------------------------------------- бастапқы деректер
def ensure_seed():
    con = _db()
    try:
        if con.execute("SELECT v FROM lib_meta WHERE k='seeded'").fetchone():
            return
        con.execute("INSERT OR REPLACE INTO lib_meta(k,v) VALUES('seeded','1')")
        if con.execute("SELECT COUNT(*) FROM lib_items").fetchone()[0] == 0 and os.path.exists(SEED):
            with open(SEED, encoding="utf-8") as f:
                d = json.load(f)
            now = int(time.time())
            for pos, a in enumerate(d.get("lessons", []), 1):
                con.execute("INSERT OR IGNORE INTO lib_items(id,kind,pos,active,title,category,level,course,minutes,description,lead,body,updated) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                            (a["id"], "lesson", pos, int(a.get("active", True)), a["title"], a.get("category", ""), a.get("level", ""),
                             int(a.get("course", 1)), int(a.get("time", 5)), a.get("description", ""), a.get("lead", ""), a.get("body", ""), now))
            for pos, a in enumerate(d.get("books", []), 1):
                author = "" if a["id"].endswith("-leaders-timeline") else a.get("author", "")
                extra = {"source_name": a.get("source_name", ""), "source_url": a.get("source_url", "")}
                con.execute("INSERT OR IGNORE INTO lib_items(id,kind,pos,active,title,author,category,description,lead,tags,extra,updated) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                            (a["id"], "book", pos, int(a.get("active", True)), a["title"], author, a.get("category", ""),
                             a.get("description", ""), a.get("lead", ""), json.dumps(a.get("tags", []), ensure_ascii=False),
                             json.dumps(extra, ensure_ascii=False), now))
            for pos, a in enumerate(d.get("leaders", []), 1):
                extra = {k: a.get(k, "") for k in ("country", "group", "years", "role", "photo", "wiki")}
                con.execute("INSERT OR IGNORE INTO lib_items(id,kind,pos,active,title,description,body,lead,extra,updated) VALUES(?,?,?,?,?,?,?,?,?,?)",
                            (a["id"], "leader", pos, 1, a["name"], a.get("summary", ""), a.get("bio", ""), a.get("lesson", ""),
                             json.dumps(extra, ensure_ascii=False), now))
        con.commit()
    finally:
        con.close()


# ------------------------------------------------------------- оқу
def list_items(kind, hidden=False, q=""):
    """hidden=True: жасырынды да қоса (админ үшін)."""
    ensure_seed()
    con = _db()
    try:
        sql, args = "SELECT * FROM lib_items WHERE kind=?", [kind]
        if not hidden:
            sql += " AND active=1"
        if q:
            sql += " AND (title LIKE ? OR author LIKE ?)"
            like = "%" + q.replace("%", "").replace("_", "") + "%"
            args += [like, like]
        sql += " ORDER BY pos, rowid"
        return [_row(r) for r in con.execute(sql, args)]
    finally:
        con.close()


def get(iid, kind=None, only_active=False):
    ensure_seed()
    con = _db()
    try:
        r = con.execute("SELECT * FROM lib_items WHERE id=?", (iid,)).fetchone()
        if not r:
            return None
        d = _row(r)
        if (kind and d["kind"] != kind) or (only_active and not d["active"]):
            return None
        return d
    finally:
        con.close()


def counts():
    ensure_seed()
    con = _db()
    try:
        n = {r[0]: r[1] for r in con.execute("SELECT kind, COUNT(*) FROM lib_items WHERE active=1 GROUP BY kind")}
    finally:
        con.close()
    return {k: n.get(k, 0) for k in KINDS}


def public_json(d):
    """Сайтқа JSON ретінде беру үшін тегістелген көрініс."""
    o = {"id": d["id"], "title": d["title"], "category": d["category"], "description": d["description"], "lead": d["lead"]}
    if d["kind"] == "lesson":
        o.update(course=d["course"], level=d["level"], time=d["minutes"], body=d["body"])
    elif d["kind"] == "book":
        o.update(author=d["author"], tags=d["tags"], has_file=d["has_file"], ext=d["file_ext"] or "",
                 source_name=d["extra"].get("source_name", ""), source_url=d["extra"].get("source_url", ""))
    else:
        o.update(d["extra"]); o.update(name=d["title"], summary=d["description"], bio=d["body"], lesson=d["lead"])
    return o


# ------------------------------------------------------------- тазалау
def _url(v):
    v = clean_text(v, 500)
    return v if re.match(r"^https?://[^\s<>\"']+$", v, re.I) else ""


def clean_fields(kind, f):
    """Форма деректерін тазалау -> (негізгі өрістер, extra, tags). Қате: ValueError(хабарлама)."""
    t = lambda k, n, ml=False: clean_text(f.get(k, ""), n, multiline=ml)
    title = t("title", 300)
    if len(title) < 2:
        raise ValueError("Атауын толтырыңыз.")
    out = {"title": title, "description": t("description", 1500, True), "lead": t("lead", 600, True), "category": t("category", 80),
           "author": "", "level": "", "course": 1, "minutes": 5, "body": ""}
    extra, tags = {}, []
    if kind == "lesson":
        out["course"] = 2 if f.get("course") == "2" else 1
        out["level"] = t("level", 40) if t("level", 40) in LEVELS else LEVELS[0]
        try:
            out["minutes"] = min(max(int(f.get("minutes", 5)), 1), 180)
        except (TypeError, ValueError):
            out["minutes"] = 5
        out["body"] = t("body", 20000, True)
        if len(out["body"]) < 10:
            raise ValueError("Материал мәтінін толтырыңыз.")
    elif kind == "book":
        out["author"] = t("author", 300)
        tags = [x for x in (clean_text(p, 40) for p in re.split(r"[,;\n]+", f.get("tags", ""))) if x][:10]
        extra = {"source_name": t("source_name", 100), "source_url": _url(f.get("source_url", ""))}
    else:
        grp = f.get("group")
        extra = {"country": t("country", 80), "group": grp if grp in ("kz", "world") else "world", "years": t("years", 40),
                 "role": t("role", 160), "photo": t("photo", 200), "wiki": t("wiki", 120).replace(" ", "_")}
        out["body"] = t("bio", 4000, True)
    return out, extra, tags


# ------------------------------------------------------------- файл
def check_file(raw):
    """-> (кеңейтім, байттар) немесе None. Тек PDF / EPUB / TXT (мазмұны бойынша тексеріледі)."""
    if not raw or len(raw) > MAX_FILE:
        return None
    if raw[:5] == b"%PDF-":
        return "pdf", raw
    if raw[:4] == b"PK\x03\x04" and b"application/epub+zip" in raw[:300]:
        return "epub", raw
    for enc in ("utf-8-sig", "cp1251"):
        try:
            text = raw.decode(enc)
        except UnicodeDecodeError:
            continue
        if "\x00" not in text[:4000]:
            return "txt", text.encode("utf-8")
    return None


def file_path(iid, ext):
    return os.path.join(LIB_DIR, "%s.%s" % (re.sub(r"[^A-Za-z0-9_-]", "_", iid), ext))


MIMES = {"pdf": "application/pdf", "epub": "application/epub+zip", "txt": "text/plain; charset=utf-8"}


# ------------------------------------------------------------- жазу
def save(kind, iid, f, file_data=None, original_name="", remove_file=False):
    """Жаңа (iid=None) немесе бар жазбаны сақтау. -> id."""
    ensure_seed()
    fields, extra, tags = clean_fields(kind, f)
    now = int(time.time())
    con = _db()
    try:
        if iid is None:
            iid = "%s-%s" % (kind[0], secrets.token_hex(4))
            pos = con.execute("SELECT COALESCE(MAX(pos),0)+1 FROM lib_items WHERE kind=?", (kind,)).fetchone()[0]
            con.execute("""INSERT INTO lib_items(id,kind,pos,active,title,author,category,level,course,minutes,description,lead,body,tags,extra,updated)
                           VALUES(?,?,?,1,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (iid, kind, pos, fields["title"], fields["author"], fields["category"], fields["level"], fields["course"],
                         fields["minutes"], fields["description"], fields["lead"], fields["body"],
                         json.dumps(tags, ensure_ascii=False), json.dumps(extra, ensure_ascii=False), now))
        else:
            old = con.execute("SELECT extra FROM lib_items WHERE id=? AND kind=?", (iid, kind)).fetchone()
            if not old:
                raise ValueError("Жазба табылмады.")
            con.execute("""UPDATE lib_items SET title=?,author=?,category=?,level=?,course=?,minutes=?,description=?,lead=?,body=?,tags=?,extra=?,updated=? WHERE id=?""",
                        (fields["title"], fields["author"], fields["category"], fields["level"], fields["course"], fields["minutes"],
                         fields["description"], fields["lead"], fields["body"], json.dumps(tags, ensure_ascii=False),
                         json.dumps(extra, ensure_ascii=False), now, iid))
        if kind == "book":
            cur = con.execute("SELECT file_ext FROM lib_items WHERE id=?", (iid,)).fetchone()["file_ext"]
            if file_data or remove_file:
                if cur:
                    try:
                        os.remove(file_path(iid, cur))
                    except OSError:
                        pass
                    con.execute("UPDATE lib_items SET file_ext=NULL, file_name=NULL, file_size=NULL WHERE id=?", (iid,))
            if file_data:
                os.makedirs(LIB_DIR, exist_ok=True)
                ext, data = file_data
                with open(file_path(iid, ext), "wb") as fh:
                    fh.write(data)
                name = clean_text(os.path.basename(original_name or ""), 120) or ("book." + ext)
                con.execute("UPDATE lib_items SET file_ext=?, file_name=?, file_size=?, updated=? WHERE id=?", (ext, name, len(data), now, iid))
        con.commit()
        return iid
    finally:
        con.close()


def set_active(iid, flag):
    con = _db()
    try:
        con.execute("UPDATE lib_items SET active=?, updated=? WHERE id=?", (1 if flag else 0, int(time.time()), iid))
        con.commit()
    finally:
        con.close()


def delete(iid):
    d = get(iid)
    if not d:
        return
    if d["file_ext"]:
        try:
            os.remove(file_path(iid, d["file_ext"]))
        except OSError:
            pass
    con = _db()
    try:
        con.execute("DELETE FROM lib_items WHERE id=?", (iid,))
        con.commit()
    finally:
        con.close()
