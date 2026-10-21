# LeaderX — Flask сайты

Көптілді лендинг: қазақша `/kk/`, орысша `/ru/`, ағылшынша `/en/`. Түбір `/` браузер тіліне қарай бағыттайды.

## Іске қосу (локально)
```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py                    # http://127.0.0.1:5000
```

## Структура
- `app.py` — маршруты (`/`, `/<lang>/`, `/healthz`), ссылка на анкету (`FORM_URL`)
- `kpi.py` — **KPI по ролям** (страница `/<lang>/kpi`). Цифры и роли правятся здесь; новая роль = ещё один блок в `ROLES`
- `translations.py` — **все тексты** на трёх языках. Чтобы поменять текст — правьте здесь
- `templates/kpi.html` — страница KPI
- `templates/index.html` — страница (Jinja2), тексты подставляются как `{{ t.ключ }}`
- `static/css/style.css` — стили и цвета (переменные в начале файла)
- `static/img/` — изображения

## Новый язык
1. В `translations.py` скопируйте блок `"en"` под новым кодом (например `"tr"`) и переведите.
2. В `app.py` добавьте код в `LANGS`.
3. В `templates/index.html` добавьте ссылку в блок `.lang`.

## Деплой
- **Render / Railway / Heroku:** подключите репозиторий, команда запуска берётся из `Procfile` (`gunicorn app:app`).
- **VPS:** `gunicorn -w 2 -b 127.0.0.1:8000 app:app` за Nginx, домен leaderx.kz на сервер.
- Ссылку на анкету можно менять без правки кода: переменная окружения `FORM_URL`.
