import hashlib, hmac, os, secrets, time
from datetime import timedelta
from flask import Flask, Response, render_template, redirect, url_for, request, abort, session, jsonify
import analytics
import results
from translations import TRANSLATIONS
from kpi import ROLES, COMMON, UI as KPI_UI
from tests import BLOCKS as TEST_BLOCKS, UI as TESTS_UI
from leadtest import DATA as LEAD_DATA

app = Flask(__name__)
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 60 * 60 * 24 * 7
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


TRACKED = {"index", "kpi", "tests", "leadership"}


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


def _res_filters():
    test = request.args.get("test", "")
    if test not in results.TEST_NAMES:
        test = ""
    return {"test": test, "grp": request.args.get("grp", "")[:50], "q": request.args.get("q", "")[:60]}


@app.route("/admin/results")
def admin_results():
    gate = _admin_gate()
    if gate:
        return gate
    f = _res_filters()
    resp = Response(render_template(
        "admin_results.html", rows=results.list_results(**f), groups=results.groups(f["test"]),
        summary=results.group_summary(f["test"], f["q"]), f=f, tests=results.TEST_NAMES,
        scales=LEAD_DATA["kk"]["scales"], tz=analytics.TZ.utcoffset(None).seconds // 3600,
        back=request.full_path.rstrip("?")))
    resp.headers["Cache-Control"] = "no-store"
    resp.headers["X-Robots-Tag"] = "noindex, nofollow"
    return resp


@app.route("/admin/results.csv")
def admin_results_csv():
    gate = _admin_gate()
    if gate:
        return gate
    rows = results.list_results(limit=100000, **_res_filters())
    resp = Response(results.csv_bytes(rows, LEAD_DATA["kk"]["scales"]), mimetype="text/csv")
    resp.headers["Content-Disposition"] = "attachment; filename=leaderx-results.csv"
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
    lang = request.accept_languages.best_match(LANGS, default=DEFAULT_LANG)
    return redirect(url_for("index", lang=lang))


@app.route("/<lang>/")
def index(lang):
    if lang not in LANGS:
        abort(404)
    return render_template("index.html", lang=lang, langs=LANGS, t=TRANSLATIONS[lang], form_url=FORM_URL)


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


@app.route("/healthz")
def healthz():
    return "ok"


if __name__ == "__main__":
    app.config["SESSION_COOKIE_SECURE"] = False  # локалды http://127.0.0.1 үшін
    app.run(debug=True, port=5000)
