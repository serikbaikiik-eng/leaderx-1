"""Тест нәтижелерін сақтау (SQLite, visits.db ішіндегі `results` кестесі)."""
import csv, io, json, math, os, re, sqlite3, time
from datetime import datetime

import analytics
import quizzes

TEST_NAMES = {"leadership": "Көшбасшылық (LeaderX)"}
TEST_NAMES.update(quizzes.names_kk())  # өз тесттері (quizzes.py)
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


def save(test, lang, name, grp, contact, ans, total=None, scales=None):
    if scales is None:  # ескі тәртіп: көшбасшылық тесті
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
                "answers": json.loads(r["answers"] or "[]"),
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
        return [(r[0], r[1], (round(r[2]) if r[2] is not None else None)) for r in con.execute(
            f"SELECT grp, COUNT(*), AVG(total) FROM results{where} GROUP BY grp ORDER BY COUNT(*) DESC LIMIT 50", args)]
    finally:
        con.close()


def test_counts():
    """[(test_id, атауы, саны)] — нәтижесі барлары."""
    con = _db()
    try:
        n = {r[0]: r[1] for r in con.execute("SELECT test, COUNT(*) FROM results GROUP BY test")}
    finally:
        con.close()
    return [(k, v, n.get(k, 0)) for k, v in TEST_NAMES.items()]


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


def table(rows, scale_names, q_count=0):
    """Excel/CSV кестесі: (тақырып, жолдар). Аты-жөні, топ, байланыс, нәтиже + (қалауынша) әр сұраққа жауап."""
    head = ["Уақыт", "Аты-жөні", "Топ", "Байланыс", "Тест", "Тіл", "Жалпы %"] + list(scale_names) + \
           ["С%d" % (i + 1) for i in range(q_count)]
    out = []
    for r in rows:
        sc = list(r["scores"])[:len(scale_names)]
        sc += [""] * (len(scale_names) - len(sc))
        an = list(r.get("answers", []))[:q_count]
        an += [""] * (q_count - len(an))
        out.append([r["time"], r["name"], r["grp"], r["contact"], TEST_NAMES.get(r["test"], r["test"]), r["lang"],
                    "" if r["total"] is None else r["total"]] + sc + an)
    return head, out


def csv_bytes(rows, scale_names, q_count=0):
    head, body = table(rows, scale_names, q_count)
    out = io.StringIO()
    w = csv.writer(out, delimiter=";")  # қазақстандық Excel үшін ";"
    w.writerow(head)
    for line in body:
        w.writerow([_safe(x) for x in line])
    return ("\ufeff" + out.getvalue()).encode("utf-8")  # BOM: Excel қазақша әріптерді дұрыс көрсетсін


def xlsx_bytes(sheets):
    """sheets = [(парақ атауы, тақырып, жолдар)]. Нағыз .xlsx (openpyxl)."""
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter
    wb = Workbook()
    wb.remove(wb.active)
    used = set()
    for title, head, body in sheets:
        t = re.sub(r"[\\/*?:\[\]]", " ", title).strip()[:31] or "Sheet"
        while t in used:
            t = (t[:28] + "_" + str(len(used)))[:31]
        used.add(t)
        ws = wb.create_sheet(t)
        ws.append(list(head))
        for line in body:
            ws.append([None] * len(line))
            for c, v in enumerate(line, 1):
                cell = ws.cell(row=ws.max_row, column=c)
                cell.value = v
                if isinstance(v, str):
                    cell.data_type = "s"  # "=..." формула болып кетпесін
        for c in range(1, len(head) + 1):
            cell = ws.cell(row=1, column=c)
            cell.font = Font(bold=True, color="F6E4A6")
            cell.fill = PatternFill("solid", fgColor="0A1428")
            cell.alignment = Alignment(vertical="center", wrap_text=True)
            width = max([len(str(head[c - 1]))] + [len(str(l[c - 1])) for l in body[:200]] + [6])
            ws.column_dimensions[get_column_letter(c)].width = min(width + 3, 45)
        ws.freeze_panes = "A2"
        if body:
            ws.auto_filter.ref = ws.dimensions
    bio = io.BytesIO()
    wb.save(bio)
    return bio.getvalue()
