"""Тест нәтижелерін сақтау (SQLite, visits.db ішіндегі `results` кестесі)."""
import csv, io, json, math, os, re, sqlite3, time
from datetime import datetime

import analytics

TEST_NAMES = {"leadership": "Көшбасшылық (LeaderX)"}
PER, SCALES, N = 4, 5, 20


def _db():
    os.makedirs(os.path.dirname(analytics.DB_PATH), exist_ok=True)
    con = sqlite3.connect(analytics.DB_PATH, timeout=5)
    con.row_factory = sqlite3.Row
    con.execute("""CREATE TABLE IF NOT EXISTS results(
        id INTEGER PRIMARY KEY AUTOINCREMENT, ts INTEGER NOT NULL, test TEXT NOT NULL, lang TEXT,
        name TEXT NOT NULL, grp TEXT NOT NULL, contact TEXT, total INTEGER, scores TEXT, answers TEXT)""")
    con.execute("CREATE INDEX IF NOT EXISTS idx_res_ts ON results(ts)")
    return con


def clean(v, n):
    """Мәтінді тазалау: басқару таңбаларын алып тастау, бос орындарды біріктіру, ұзындықты шектеу."""
    if not isinstance(v, str):
        return ""
    v = re.sub(r"[\x00-\x1f\x7f]", " ", v)
    return re.sub(r"\s+", " ", v).strip()[:n]


def _round(x):  # JS Math.round-пен бірдей (0.5 жоғары)
    return int(math.floor(x + 0.5))


def score_leadership(ans):
    """Сайттағы JS-пен бірдей формула, бірақ серверде есептеледі (клиентке сенбейміз)."""
    total = _round((sum(ans) - N) / (N * 4) * 100)
    scales = [_round((sum(ans[s * PER:(s + 1) * PER]) - PER) / (PER * 4) * 100) for s in range(SCALES)]
    return total, scales


def save(test, lang, name, grp, contact, ans):
    total, scales = score_leadership(ans)
    con = _db()
    try:
        con.execute("INSERT INTO results(ts,test,lang,name,grp,contact,total,scores,answers) VALUES(?,?,?,?,?,?,?,?,?)",
                    (int(time.time()), test, lang, name, grp, contact, total, json.dumps(scales), json.dumps(ans)))
        con.commit()
    finally:
        con.close()


def _where(test, grp, q):
    cond, args = [], []
    if test:
        cond.append("test=?"); args.append(test)
    if grp:
        cond.append("grp=?"); args.append(grp)
    if q:
        like = "%" + q.replace("%", "").replace("_", "") + "%"
        cond.append("(name LIKE ? OR contact LIKE ?)"); args += [like, like]
    return (" WHERE " + " AND ".join(cond)) if cond else "", args


def list_results(test="", grp="", q="", limit=1000):
    where, args = _where(test, grp, q)
    con = _db()
    try:
        out = []
        for r in con.execute(f"SELECT * FROM results{where} ORDER BY id DESC LIMIT ?", args + [limit]):
            out.append({
                "id": r["id"], "test": r["test"], "lang": r["lang"], "name": r["name"], "grp": r["grp"],
                "contact": r["contact"] or "", "total": r["total"], "scores": json.loads(r["scores"] or "[]"),
                "time": datetime.fromtimestamp(r["ts"], analytics.TZ).strftime("%d.%m.%Y %H:%M"),
            })
        return out
    finally:
        con.close()


def groups(test=""):
    where, args = _where(test, "", "")
    con = _db()
    try:
        return [r[0] for r in con.execute(f"SELECT DISTINCT grp FROM results{where} ORDER BY grp", args)]
    finally:
        con.close()


def group_summary(test="", q=""):
    where, args = _where(test, "", q)
    con = _db()
    try:
        return [(r[0], r[1], round(r[2] or 0)) for r in con.execute(
            f"SELECT grp, COUNT(*), AVG(total) FROM results{where} GROUP BY grp ORDER BY COUNT(*) DESC LIMIT 50", args)]
    finally:
        con.close()


def delete(rid):
    con = _db()
    try:
        con.execute("DELETE FROM results WHERE id=?", (rid,))
        con.commit()
    finally:
        con.close()


_PHONE = re.compile(r"^[+\-]?[\d\s()\-]+$")


def _safe(v):
    """Excel формула-инъекциясынан қорғау (=, @ және т.б. басталатын мәтін)."""
    if isinstance(v, str) and v:
        if v[0] in "=@\t\r" or (v[0] in "+-" and not _PHONE.match(v)):
            return "'" + v
    return v


def csv_bytes(rows, scale_names):
    out = io.StringIO()
    w = csv.writer(out, delimiter=";")  # қазақстандық Excel үшін ";"
    w.writerow(["Уақыт", "Аты-жөні", "Топ", "Байланыс", "Тест", "Тіл", "Жалпы %"] + list(scale_names))
    for r in rows:
        w.writerow([_safe(x) for x in [r["time"], r["name"], r["grp"], r["contact"], TEST_NAMES.get(r["test"], r["test"]), r["lang"], r["total"]] + r["scores"]])
    return ("\ufeff" + out.getvalue()).encode("utf-8")  # BOM: Excel қазақша әріптерді дұрыс көрсетсін
