import hashlib, hmac, os, secrets, time
from datetime import timedelta
from flask import Flask, Response, render_template, redirect, url_for, request, abort, session, jsonify
import analytics
import results
from translations import TRANSLATIONS
from kpi import ROLES, COMMON, UI as KPI_UI
from tests import BLOCKS as TEST_BLOCKS, UI as TESTS_UI
from leadtest import DATA as LEAD_DATA
import quizzes
from quizzes import QUIZZES
import team as team_mod

# Орыс мәтініндегі «Перемены» сөзін «Изменение» деп ауыстыру
for _k, _v in list(TRANSLATIONS.get("ru", {}).items()):
    if isinstance(_v, str):
        TRANSLATIONS["ru"][_k] = _v.replace("Перемены", "Изменение")

app = Flask(__name__)
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 60 * 60 * 24 * 7
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024  # сурет жүктеу үшін (админ)
# Сессия кілті: SECRET_KEY орнатылмаса, ADMIN_PASSWORD негізінде жасалады
app.secret_key = os.environ.get("SECRET_KEY") or hashlib.sha256(("leaderx-session|" + (os.environ.get("ADMIN_PASSWORD") or "off")).encode()).hexdigest()
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=True,  # хостингте (HTTPS) ғана; локалды `python app.py` кезінде төменде өшіріледі
    PERMANENT_SESSION_LIFETIME=timedelta(hours=12),
)

LANGS = ["kk", "ru", "en"]
DEFAULT_LANG = "kk"

FORM_URL = os.environ.get(
    "FORM_URL",
    "https://docs.google.com/forms/d/e/1FAIpQLSezQqGbAKt7CebGqzqrBaav8Dw3n_ljQ15wL3k4fq66abu9zQ/viewform?usp=header",
)


@app.context_processor
def asset_version():
    # style.css жаңарғанда браузер кэшін автоматты түрде айналып өту үшін
    p = os.path.join(app.static_folder, "css", "style.css")
    return {"css_v": int(os.path.getmtime(p)) if os.path.exists(p) else 0}


TRACKED = {"index", "kpi", "tests", "leadership", "quiz"}


@app.before_request
def track():
    if request.method == "GET" and request.endpoint in TRACKED:
        analytics.log_visit(request, (request.view_args or {}).get("lang"))


def csrf_token():
    t = session.get("csrf")
    if not t:
        t = secrets.token_hex(16)
        session["csrf"] = t
    return t


app.jinja_env.globals["csrf_token"] = csrf_token

_fails = {}  # ip -> [сәтсіз әрекеттер уақыты]
MAX_FAILS, BLOCK_SEC = 5, 15 * 60


def _client_ip():
    # Render Cloudflare арқылы жұмыс істейді: True-Client-IP жалған болуы мүмкін емес.
    # X-Forwarded-For-ға сенбейміз (клиент оны өзі жаза алады).
    return (request.headers.get("True-Client-IP") or request.headers.get("CF-Connecting-IP")
            or request.remote_addr or "?").strip()


def _blocked(ip):
    now = time.time()
    recent = [t for t in _fails.get(ip, []) if now - t < BLOCK_SEC]
    _fails[ip] = recent
    return len(recent) >= MAX_FAILS


def _admin_on():
    if not os.environ.get("ADMIN_PASSWORD"):
        abort(404)  # құпиясөз қойылмаса, админ-панель өшірулі


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    _admin_on()
    if session.get("admin"):
        return redirect(url_for("admin"))
    error = None
    if request.method == "POST":
        ip = _client_ip()
        if _blocked(ip):
            error = "Тым көп қате әрекет. 15 минуттан кейін қайталаңыз."
        elif not hmac.compare_digest(request.form.get("csrf", ""), session.get("csrf", "x")):
            error = "Сессия ескірді. Бетті жаңартып, қайталаңыз."
        else:
            user = os.environ.get("ADMIN_USER", "admin")
            ok = hmac.compare_digest(request.form.get("username", ""), user) and \
                 hmac.compare_digest(request.form.get("password", ""), os.environ["ADMIN_PASSWORD"])
            if ok:
                _fails.pop(ip, None)
                session.clear()
                session["admin"] = True
                session.permanent = True
                return redirect(url_for("admin"))
            _fails.setdefault(ip, []).append(time.time())
            error = "Логин немесе құпиясөз қате."
    resp = Response(render_template("login.html", error=error), 401 if error else 200)
    resp.headers["Cache-Control"] = "no-store"
    resp.headers["X-Robots-Tag"] = "noindex, nofollow"
    return resp


@app.route("/admin/logout", methods=["POST"])
def admin_logout():
    if hmac.compare_digest(request.form.get("csrf", ""), session.get("csrf", "x")):
        session.clear()
    return redirect(url_for("admin_login"))


@app.route("/admin")
def admin():
    _admin_on()
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    days = min(max(request.args.get("days", 14, type=int), 1), 90)
    resp = Response(render_template("admin.html", s=analytics.stats(days), tz=analytics.TZ.utcoffset(None).seconds // 3600))
    resp.headers["X-Robots-Tag"] = "noindex, nofollow"
    resp.headers["Cache-Control"] = "no-store"
    return resp


def _admin_gate():
    """Админ емес болса — кіру бетіне бағыттайды, әйтпесе None."""
    _admin_on()
    return None if session.get("admin") else redirect(url_for("admin_login"))


def _test_meta(test):
    """(шкала атаулары, сұрақ мәтіндері) — таңдалған тест үшін; тест таңдалмаса бос."""
    if test == "leadership":
        return LEAD_DATA["kk"]["scales"], LEAD_DATA["kk"]["q"]
    if test in QUIZZES:
        return quizzes.meta(test)
    return [], []


def _res_filters():
    test = request.args.get("test", "")
    if test not in results.TEST_NAMES:
        test = ""
    return {"test": test, "grp": request.args.get("grp", "")[:50], "q": request.args.get("q", "")[:60]}


def _csrf_ok():
    return hmac.compare_digest(request.form.get("csrf", ""), session.get("csrf", "x"))


@app.route("/team/photo/<int:mid>")
def team_photo(mid):
    p = team_mod.photo(mid)
    if not p:
        abort(404)
    resp = Response(p[0], mimetype=p[1])
    resp.headers["Cache-Control"] = "public, max-age=31536000, immutable"  # URL-де ?v=<жаңартылған уақыт>
    resp.headers["X-Content-Type-Options"] = "nosniff"
    return resp


@app.route("/admin/team")
def admin_team():
    gate = _admin_gate()
    if gate:
        return gate
    resp = Response(render_template("admin_team.html", members=team_mod.list_members(), msg=request.args.get("msg", "")))
    resp.headers["Cache-Control"] = "no-store"
    resp.headers["X-Robots-Tag"] = "noindex, nofollow"
    return resp


@app.route("/admin/team/new", methods=["GET", "POST"])
@app.route("/admin/team/<int:mid>", methods=["GET", "POST"])
def admin_team_edit(mid=None):
    gate = _admin_gate()
    if gate:
        return gate
    m = team_mod.get(mid) if mid else None
    if mid and not m:
        abort(404)
    vals = m or {"id": None, "name": "", "i18n": {}, "skills": [], "instagram": "", "telegram": "", "whatsapp": "",
                 "email": "", "has_photo": False, "updated": 0}
    error = None
    if request.method == "POST":
        name = team_mod.clean_text(request.form.get("name"), 100)
        i18n = team_mod.clean_i18n(request.form)
        skills = team_mod.clean_skills(request.form.get("skills", ""))
        contacts = team_mod.clean_contacts(request.form)
        vals = dict(vals, name=name, i18n=i18n, skills=skills, **contacts)
        if not _csrf_ok():
            error = "Сессия ескірді. Бетті жаңартып, қайталаңыз."
        elif len(name) < 2:
            error = "Аты-жөнін толтырыңыз."
        else:
            photo_data = None
            f = request.files.get("photo")
            if f and f.filename:
                photo_data = team_mod.process_photo(f.read(team_mod.MAX_PHOTO + 1))
                if not photo_data:
                    error = "Сурет қабылданбады. JPEG, PNG немесе WEBP, 6 МБ-қа дейін болуы керек."
            if not error:
                try:
                    team_mod.save(mid, name, i18n, skills, contacts, photo_data, remove_photo=bool(request.form.get("rm_photo")))
                except ValueError:
                    error = "Мүше саны шегіне жетті."
                else:
                    return redirect(url_for("admin_team", msg="saved"))
    resp = Response(render_template("admin_team_edit.html", m=vals, error=error, langs=LANGS, mid=mid,
                                    skills_text=", ".join(vals["skills"])), 400 if error else 200)
    resp.headers["Cache-Control"] = "no-store"
    resp.headers["X-Robots-Tag"] = "noindex, nofollow"
    return resp


@app.route("/admin/team/<int:mid>/delete", methods=["POST"])
def admin_team_delete(mid):
    gate = _admin_gate()
    if gate:
        return gate
    if _csrf_ok():
        team_mod.delete(mid)
    return redirect(url_for("admin_team", msg="deleted"))


@app.route("/admin/team/<int:mid>/move", methods=["POST"])
def admin_team_move(mid):
    gate = _admin_gate()
    if gate:
        return gate
    if _csrf_ok() and request.form.get("dir") in ("up", "down"):
        team_mod.move(mid, request.form["dir"])
    return redirect(url_for("admin_team"))


@app.route("/admin/results")
def admin_results():
    gate = _admin_gate()
    if gate:
        return gate
    f = _res_filters()
    resp = Response(render_template(
        "admin_results.html", rows=results.list_results(**f), groups=results.groups(f["test"]),
        summary=results.group_summary(f["test"], f["q"]), f=f, tests=results.TEST_NAMES,
        scales=_test_meta(f["test"])[0], counts=results.test_counts(),
        tz=analytics.TZ.utcoffset(None).seconds // 3600,
        back=request.full_path.rstrip("?")))
    resp.headers["Cache-Control"] = "no-store"
    resp.headers["X-Robots-Tag"] = "noindex, nofollow"
    return resp


@app.route("/admin/results.csv")
def admin_results_csv():
    gate = _admin_gate()
    if gate:
        return gate
    f = _res_filters()
    scales, qs = _test_meta(f["test"])
    rows = results.list_results(limit=100000, **f)
    name = "leaderx-%s.csv" % (f["test"] or "all-tests")
    resp = Response(results.csv_bytes(rows, scales, len(qs)), mimetype="text/csv")
    resp.headers["Content-Disposition"] = "attachment; filename=" + name
    resp.headers["Cache-Control"] = "no-store"
    return resp


@app.route("/admin/results.xlsx")
def admin_results_xlsx():
    """Нағыз Excel файл. Тест таңдалса — сол тест (нәтижелер + сұрақтар парағы), болмаса — әр тест бөлек парақта."""
    gate = _admin_gate()
    if gate:
        return gate
    f = _res_filters()
    sheets = []
    for tid, tname in results.TEST_NAMES.items():
        if f["test"] and tid != f["test"]:
            continue
        rows = results.list_results(limit=100000, **dict(f, test=tid))
        if not rows and not f["test"]:
            continue
        scales, qs = _test_meta(tid)
        head, body = results.table(rows, scales, len(qs))
        sheets.append((tname, head, body))
        if qs and f["test"]:
            sheets.append(("Сұрақтар", ["№", "Сұрақ"], [[i + 1, q] for i, q in enumerate(qs)]))
    if not sheets:
        sheets.append(("Нәтижелер", ["Нәтиже жоқ"], []))
    try:
        data = results.xlsx_bytes(sheets)
    except ImportError:  # openpyxl орнатылмаған -> CSV
        return redirect(url_for("admin_results_csv", **{k: v for k, v in f.items() if v}))
    resp = Response(data, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    resp.headers["Content-Disposition"] = "attachment; filename=leaderx-%s.xlsx" % (f["test"] or "all-tests")
    resp.headers["Cache-Control"] = "no-store"
    return resp


@app.route("/admin/results/delete", methods=["POST"])
def admin_results_delete():
    gate = _admin_gate()
    if gate:
        return gate
    if hmac.compare_digest(request.form.get("csrf", ""), session.get("csrf", "x")):
        rid = request.form.get("id", type=int)
        if rid:
            results.delete(rid)
    back = request.form.get("back", "")
    return redirect(back if back.startswith("/admin/results") else url_for("admin_results"))


@app.route("/")
def root():
    # Басты бетке кіргенде әрқашан қазақша ашылады (тілді жоғарғы KZ/RU/EN батырмасымен ауыстыруға болады)
    return redirect(url_for("index", lang=DEFAULT_LANG))


@app.route("/<lang>/")
def index(lang):
    if lang not in LANGS:
        abort(404)
    return render_template("index.html", lang=lang, langs=LANGS, t=TRANSLATIONS[lang], form_url=FORM_URL,
                           team=team_mod.public_list(lang))


@app.route("/<lang>/kpi")
def kpi(lang):
    if lang not in LANGS:
        abort(404)
    return render_template(
        "kpi.html", lang=lang, langs=LANGS, ui=KPI_UI[lang],
        roles=ROLES, common=COMMON[lang], form_url=FORM_URL,
    )


@app.route("/<lang>/tests")
def tests(lang):
    if lang not in LANGS:
        abort(404)
    return render_template(
        "tests.html", lang=lang, langs=LANGS, ui=TESTS_UI[lang],
        blocks=TEST_BLOCKS, form_url=FORM_URL,
    )


@app.route("/<lang>/tests/leadership")
def leadership(lang):
    if lang not in LANGS:
        abort(404)
    d = LEAD_DATA[lang]
    return render_template("leadership.html", lang=lang, langs=LANGS, ui=d["ui"], data=d, form_url=FORM_URL)


_submits = {}  # ip -> жіберу уақыттары (спамнан қорғау)


def _submit_ok(ip, limit=30, window=3600):
    now = time.time()
    hits = [t for t in _submits.get(ip, []) if now - t < window]
    ok = len(hits) < limit
    if ok:
        hits.append(now)
    _submits[ip] = hits
    return ok


@app.route("/<lang>/tests/leadership/submit", methods=["POST"])
def leadership_submit(lang):
    if lang not in LANGS:
        abort(404)
    if (request.content_length or 0) > 20000:
        return jsonify(ok=False, error="too large"), 413
    if not _submit_ok(_client_ip()):
        return jsonify(ok=False, error="rate"), 429
    d = request.get_json(silent=True)
    if not isinstance(d, dict):
        return jsonify(ok=False, error="bad json"), 400
    name = results.clean(d.get("name"), 100)
    grp = results.clean(d.get("group"), 50)
    contact = results.clean(d.get("contact"), 100)
    ans = d.get("answers")
    if len(name) < 2 or not grp or d.get("consent") is not True:
        return jsonify(ok=False, error="fields"), 400
    if not (isinstance(ans, list) and len(ans) == 20 and
            all(isinstance(a, int) and not isinstance(a, bool) and 1 <= a <= 5 for a in ans)):
        return jsonify(ok=False, error="answers"), 400
    try:
        results.save("leadership", lang, name, grp, contact, ans)
    except Exception:
        return jsonify(ok=False, error="db"), 500
    return jsonify(ok=True)


@app.route("/<lang>/tests/<qid>")
def quiz(lang, qid):
    if lang not in LANGS or qid not in QUIZZES:
        abort(404)
    d = quizzes.view(qid, lang)
    return render_template("quiz.html", lang=lang, langs=LANGS, ui=d["ui"], data=d, qid=qid, form_url=FORM_URL)


@app.route("/<lang>/tests/<qid>/submit", methods=["POST"])
def quiz_submit(lang, qid):
    if lang not in LANGS or qid not in QUIZZES:
        abort(404)
    if (request.content_length or 0) > 20000:
        return jsonify(ok=False, error="too large"), 413
    if not _submit_ok(_client_ip()):
        return jsonify(ok=False, error="rate"), 429
    d = request.get_json(silent=True)
    if not isinstance(d, dict):
        return jsonify(ok=False, error="bad json"), 400
    name = results.clean(d.get("name"), 100)
    grp = results.clean(d.get("group"), 50)
    contact = results.clean(d.get("contact"), 100)
    ans = d.get("answers")
    if len(name) < 2 or not grp or d.get("consent") is not True:
        return jsonify(ok=False, error="fields"), 400
    if not quizzes.valid_answers(qid, ans):
        return jsonify(ok=False, error="answers"), 400
    total, scores = quizzes.score(qid, ans)
    try:
        results.save(qid, lang, name, grp, contact, ans, total, scores)
    except Exception:
        return jsonify(ok=False, error="db"), 500
    return jsonify(ok=True)


@app.route("/healthz")
def healthz():
    return "ok"


if __name__ == "__main__":
    app.config["SESSION_COOKIE_SECURE"] = False  # локалды http://127.0.0.1 үшін
    app.run(debug=True, port=5000)
