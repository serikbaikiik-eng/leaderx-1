"""Команда мүшелері (SQLite, visits.db ішіндегі `team` кестесі). Сурет — BLOB ретінде сол базада сақталады,
сондықтан деректер мен суреттер бірге сақталады (Render-де файлдар өшіп қалмайды)."""
import io, json, re, sqlite3, time

import analytics

LANGS = ("kk", "ru", "en")
FIELDS = ("role", "short", "about", "education", "achievements")
MAX_PHOTO = 6 * 1024 * 1024
MAX_MEMBERS = 60


def _db():
    import os
    os.makedirs(os.path.dirname(analytics.DB_PATH), exist_ok=True)
    con = sqlite3.connect(analytics.DB_PATH, timeout=5)
    con.row_factory = sqlite3.Row
    con.execute("""CREATE TABLE IF NOT EXISTS team(
        id INTEGER PRIMARY KEY AUTOINCREMENT, pos INTEGER NOT NULL DEFAULT 0, name TEXT NOT NULL,
        i18n TEXT NOT NULL DEFAULT '{}', skills TEXT NOT NULL DEFAULT '[]',
        instagram TEXT, telegram TEXT, whatsapp TEXT, email TEXT,
        photo BLOB, photo_mime TEXT, updated INTEGER NOT NULL DEFAULT 0)""")
    con.execute("CREATE TABLE IF NOT EXISTS team_meta(k TEXT PRIMARY KEY, v TEXT)")
    return con


# ---------------------------------------------------------------- тазалау
def clean_text(v, n, multiline=False):
    if not isinstance(v, str):
        return ""
    v = v.replace("\r\n", "\n").replace("\r", "\n")
    v = re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", " ", v)
    if multiline:
        lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in v.split("\n")]
        v = re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()
    else:
        v = re.sub(r"\s+", " ", v).strip()
    return v[:n]


def clean_handle(v, pattern, prefixes):
    v = clean_text(v, 200)
    for p in prefixes:
        v = re.sub(r"^(https?://)?(www\.)?" + re.escape(p) + r"/?", "", v, flags=re.I)
    v = v.lstrip("@").split("?")[0].strip("/ ")
    return v if re.fullmatch(pattern, v) else ""


def clean_contacts(form):
    wa = re.sub(r"\D", "", form.get("whatsapp", ""))
    email = clean_text(form.get("email", ""), 120)
    return {
        "instagram": clean_handle(form.get("instagram", ""), r"[A-Za-z0-9._]{1,30}", ["instagram.com"]),
        "telegram": clean_handle(form.get("telegram", ""), r"[A-Za-z0-9_]{3,32}", ["t.me", "telegram.me"]),
        "whatsapp": wa if 7 <= len(wa) <= 15 else "",
        "email": email if re.fullmatch(r"[^@\s<>]{1,64}@[^@\s<>]{1,200}\.[^@\s<>]{2,}", email) else "",
    }


def clean_skills(v):
    parts = re.split(r"[,\n;]+", v if isinstance(v, str) else "")
    out = []
    for p in parts:
        p = clean_text(p, 40)
        if p and p not in out:
            out.append(p)
    return out[:15]


LIMITS = {"role": 80, "short": 160, "about": 1500, "education": 800, "achievements": 1500}


def clean_i18n(form):
    out = {}
    for lg in LANGS:
        out[lg] = {f: clean_text(form.get(f"{f}_{lg}", ""), LIMITS[f], multiline=f in ("about", "education", "achievements"))
                   for f in FIELDS}
    return out


# ---------------------------------------------------------------- сурет
def process_photo(raw):
    """-> (bytes, mime) немесе None. Тек JPEG/PNG/WEBP. Pillow болса: кішірейтіп, EXIF-ті өшіреді."""
    if not raw or len(raw) > MAX_PHOTO:
        return None
    if raw[:3] == b"\xff\xd8\xff":
        mime = "image/jpeg"
    elif raw[:8] == b"\x89PNG\r\n\x1a\n":
        mime = "image/png"
    elif raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
        mime = "image/webp"
    else:
        return None
    try:
        from PIL import Image, ImageOps
        im = ImageOps.exif_transpose(Image.open(io.BytesIO(raw)))
        im.thumbnail((900, 1100))
        if im.mode not in ("RGB", "L"):
            bg = Image.new("RGB", im.size, (10, 20, 40))
            bg.paste(im, mask=im.split()[-1] if im.mode in ("RGBA", "LA") else None)
            im = bg
        buf = io.BytesIO()
        im.convert("RGB").save(buf, "JPEG", quality=86, optimize=True)
        return buf.getvalue(), "image/jpeg"
    except ImportError:
        return (raw, mime) if len(raw) <= 2 * 1024 * 1024 else None
    except Exception:
        return None


# ---------------------------------------------------------------- база
def _row(r, with_updated=True):
    return {
        "id": r["id"], "pos": r["pos"], "name": r["name"], "i18n": json.loads(r["i18n"] or "{}"),
        "skills": json.loads(r["skills"] or "[]"), "instagram": r["instagram"] or "", "telegram": r["telegram"] or "",
        "whatsapp": r["whatsapp"] or "", "email": r["email"] or "", "has_photo": bool(r["has_photo"]),
        "updated": r["updated"],
    }


_COLS = "id,pos,name,i18n,skills,instagram,telegram,whatsapp,email,(photo IS NOT NULL) AS has_photo,updated"


def list_members():
    ensure_seed()
    con = _db()
    try:
        return [_row(r) for r in con.execute(f"SELECT {_COLS} FROM team ORDER BY pos, id")]
    finally:
        con.close()


def get(mid):
    con = _db()
    try:
        r = con.execute(f"SELECT {_COLS} FROM team WHERE id=?", (mid,)).fetchone()
        return _row(r) if r else None
    finally:
        con.close()


def photo(mid):
    con = _db()
    try:
        r = con.execute("SELECT photo, photo_mime FROM team WHERE id=?", (mid,)).fetchone()
        return (bytes(r["photo"]), r["photo_mime"] or "image/jpeg") if r and r["photo"] else None
    finally:
        con.close()


def save(mid, name, i18n, skills, contacts, photo_data=None, remove_photo=False):
    now = int(time.time())
    con = _db()
    try:
        if mid is None:
            if con.execute("SELECT COUNT(*) FROM team").fetchone()[0] >= MAX_MEMBERS:
                raise ValueError("too many")
            pos = (con.execute("SELECT COALESCE(MAX(pos),0)+1 FROM team").fetchone()[0])
            cur = con.execute(
                "INSERT INTO team(pos,name,i18n,skills,instagram,telegram,whatsapp,email,updated) VALUES(?,?,?,?,?,?,?,?,?)",
                (pos, name, json.dumps(i18n, ensure_ascii=False), json.dumps(skills, ensure_ascii=False),
                 contacts["instagram"], contacts["telegram"], contacts["whatsapp"], contacts["email"], now))
            mid = cur.lastrowid
        else:
            con.execute("UPDATE team SET name=?,i18n=?,skills=?,instagram=?,telegram=?,whatsapp=?,email=?,updated=? WHERE id=?",
                        (name, json.dumps(i18n, ensure_ascii=False), json.dumps(skills, ensure_ascii=False),
                         contacts["instagram"], contacts["telegram"], contacts["whatsapp"], contacts["email"], now, mid))
        if photo_data:
            con.execute("UPDATE team SET photo=?, photo_mime=?, updated=? WHERE id=?", (photo_data[0], photo_data[1], now, mid))
        elif remove_photo:
            con.execute("UPDATE team SET photo=NULL, photo_mime=NULL, updated=? WHERE id=?", (now, mid))
        con.commit()
        return mid
    finally:
        con.close()


def delete(mid):
    con = _db()
    try:
        con.execute("DELETE FROM team WHERE id=?", (mid,))
        con.commit()
    finally:
        con.close()


def move(mid, direction):
    """Орнын бір қадам жоғары/төмен ауыстыру."""
    con = _db()
    try:
        rows = [r["id"] for r in con.execute("SELECT id FROM team ORDER BY pos, id")]
        if mid not in rows:
            return
        i = rows.index(mid)
        j = i - 1 if direction == "up" else i + 1
        if 0 <= j < len(rows):
            rows[i], rows[j] = rows[j], rows[i]
        for pos, rid in enumerate(rows, 1):
            con.execute("UPDATE team SET pos=? WHERE id=?", (pos, rid))
        con.commit()
    finally:
        con.close()


_SEED = [
    ("Сабырбай Бекболат Еділбайұлы", {
        "kk": {"role": "Ұйым жетекшісі", "short": "PhD докторына кандидат, магистр, сеньор-лектор"},
        "ru": {"role": "Руководитель организации", "short": "Кандидат в доктора PhD, магистр, старший преподаватель"},
        "en": {"role": "Head of the organization", "short": "PhD candidate, master’s degree, senior lecturer"}}),
    ("Мөлдіржан Сағынжанқызы", {
        "kk": {"role": "Жетекші орынбасары", "short": "Командаға қосылу бойынша барлық сұрақтарға жауап береді"},
        "ru": {"role": "Заместитель руководителя", "short": "Отвечает на все вопросы о вступлении в команду"},
        "en": {"role": "Deputy head", "short": "Answers all questions about joining the team"}}),
]


def ensure_seed():
    """Бірінші іске қосқанда екі бастапқы мүшені қосады (бір рет)."""
    con = _db()
    try:
        if con.execute("SELECT v FROM team_meta WHERE k='seeded'").fetchone():
            return
        con.execute("INSERT OR REPLACE INTO team_meta(k,v) VALUES('seeded','1')")
        if con.execute("SELECT COUNT(*) FROM team").fetchone()[0] == 0:
            now = int(time.time())
            for pos, (name, tr) in enumerate(_SEED, 1):
                full = {lg: {f: tr[lg].get(f, "") for f in FIELDS} for lg in LANGS}
                con.execute("INSERT INTO team(pos,name,i18n,skills,updated) VALUES(?,?,?,?,?)",
                            (pos, name, json.dumps(full, ensure_ascii=False), "[]", now))
        con.commit()
    finally:
        con.close()


# ---------------------------------------------------------------- сайтқа арналған көрініс
def _pick(i18n, lang, field):
    for lg in (lang, "kk", "ru", "en"):
        v = (i18n.get(lg) or {}).get(field, "")
        if v:
            return v
    return ""


def public_list(lang):
    out = []
    for m in list_members():
        i = m["i18n"]
        words = [w for w in re.split(r"\s+", m["name"]) if w]
        contacts = []
        if m["telegram"]:
            contacts.append({"label": "Telegram", "url": "https://t.me/" + m["telegram"], "text": "@" + m["telegram"]})
        if m["instagram"]:
            contacts.append({"label": "Instagram", "url": "https://instagram.com/" + m["instagram"], "text": "@" + m["instagram"]})
        if m["whatsapp"]:
            contacts.append({"label": "WhatsApp", "url": "https://wa.me/" + m["whatsapp"], "text": "+" + m["whatsapp"]})
        if m["email"]:
            contacts.append({"label": "Email", "url": "mailto:" + m["email"], "text": m["email"]})
        out.append({
            "id": m["id"], "name": m["name"], "initials": "".join(w[0] for w in words[:2]).upper(),
            "photo": ("/team/photo/%d?v=%d" % (m["id"], m["updated"])) if m["has_photo"] else "",
            "role": _pick(i, lang, "role"), "short": _pick(i, lang, "short"), "about": _pick(i, lang, "about"),
            "education": _pick(i, lang, "education"), "achievements": _pick(i, lang, "achievements"),
            "skills": m["skills"], "contacts": contacts,
        })
    return out
