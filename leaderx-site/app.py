import os
from flask import Flask, render_template, redirect, url_for, request, abort
from translations import TRANSLATIONS
from kpi import ROLES, COMMON, UI as KPI_UI

app = Flask(__name__)
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 60 * 60 * 24 * 7  

LANGS = ["kk", "ru", "en"]
DEFAULT_LANG = "kk"

FORM_URL = os.environ.get(
    "FORM_URL",
    "https://docs.google.com/forms/d/e/1FAIpQLSezQqGbAKt7CebGqzqrBaav8Dw3n_ljQ15wL3k4fq66abu9zQ/viewform?usp=header",
)


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


@app.route("/healthz")
def healthz():
    return "ok"


if __name__ == "__main__":
    app.run(debug=True, port=5000)
