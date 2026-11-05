"""Тесттер / Тесты / Tests. Жаңа тест = блоктың "items" тізіміне бір жол.
url=None -> сілтеме әлі жоқ; file -> static/docs/ ішіндегі docx жүктеу."""

P = "https://psytests.org/work/"

BLOCKS = [
    {"id": "general", "items": [
        {"name": "Определение лидерства", "url": P + "northA.html"},
        {"name": "Лидер. Менеджер. Эксперт, ЛМЭ", "url": P + "lme.html"},
        {"names": {"kk": "Көшбасшылықты тестілеу", "ru": "Тест на лидерство LeaderX", "en": "LeaderX leadership test"}, "route": "leadership"},
        {"name": "Опросник на определение типа последователя", "url": P + "northL.html"},
    ]},
    {"id": "qualities", "items": [
        {"name": "Опросник для определения лидерских качеств", "url": P + "northB.html"},
        {"name": "Тест на определение лидерских качеств", "url": P + "tmklid.html"},
        {"name": "Оценка коммуникативно-лидерских способностей", "url": P + "amanB.html"},
    ]},
    {"id": "styles", "items": [
        {"name": "Опросник стиля лидерства по теории «путь – цель»", "url": P + "northE.html"},
        {"name": "Опросник аутентичного лидерства, ALQ", "url": "https://psytests.org/result?v=nrlH1JDL&pp=1"},
        {"name": "Опросник по адаптивному лидерству", "url": P + "northJ.html"},
        {"name": "Инструмент анализа инклюзивного лидерства", "url": P + "northK.html"},
        {"name": "Многофакторный опросник лидерства, MLQ-6S", "url": P + "mleadq.html"},
    ]},
    {"id": "resources", "items": [
        {"name": "Тест эмоционального интеллекта Шутте (SREIT)", "file": "schutte-eq.docx"},
        {"name": "Опросник социального интеллекта Карртика (KSII)", "file": "karrtika-social-iq.docx"},
        {"name": "Определение стиля познания Д. Колба (LSI)", "file": "kolb-lsi.docx"},
        {"name": "Методика «Жизненная успешность» (Деева Н. А.)", "file": "deeva-life-success.docx"},
        {"name": "Методика оценки интеллекта успеха (Сабырбай Б. Е.)", "file": "sabyrbay-success-iq.docx"},
    ]},
]

UI = {
    "kk": {
        "title": "Көшбасшылық тесттері — LeaderX",
        "h1": "Көшбасшылық тесттері",
        "lead": "Өзіңнің көшбасшылық деңгейің, қасиеттерің және стиліңді анықтайтын сауалнамалар.",
        "start": "Тестті бастау", "back": "Басты бет", "apply": "Анкета", "open": "Тестті ашу",
        "download": "Бланкіні жүктеу (.docx)", "soon": "Сілтеме жақында қосылады",
        "blocks": {
            "general": ("Жалпы көшбасшылық", "Көшбасшылықтың жалпы деңгейі мен рөлі."),
            "qualities": ("Көшбасшы қасиеттері", "Жеке қасиеттер мен коммуникативті қабілеттер."),
            "styles": ("Көшбасшылық стильдері", "Көшбасшы қалай басқарады және команданы қалай жетелейді."),
            "resources": ("Интеллект және жеке ресурстар", "Көшбасшылықты қолдайтын эмоциялық, әлеуметтік интеллект және табыс."),
        },
    },
    "ru": {
        "title": "Тесты на лидерство — LeaderX",
        "h1": "Тесты на лидерство",
        "lead": "Опросники, которые помогут определить уровень лидерства, качества и стиль.",
        "start": "Начать тест", "back": "На главную", "apply": "Анкета", "open": "Открыть тест",
        "download": "Скачать бланк (.docx)", "soon": "Ссылка скоро появится",
        "blocks": {
            "general": ("Общее лидерство", "Общий уровень лидерства и роль в группе."),
            "qualities": ("Лидерские качества", "Личные качества и коммуникативные способности."),
            "styles": ("Стили лидерства", "Как лидер управляет и ведёт команду."),
            "resources": ("Интеллект и личные ресурсы", "Эмоциональный и социальный интеллект, успешность — опора лидера."),
        },
    },
    "en": {
        "title": "Leadership tests — LeaderX",
        "h1": "Leadership tests",
        "lead": "Questionnaires to find out your leadership level, qualities and style.",
        "start": "Start test", "back": "Home", "apply": "Apply", "open": "Open test",
        "download": "Download form (.docx)", "soon": "Link coming soon",
        "blocks": {
            "general": ("General leadership", "Overall leadership level and role in a group."),
            "qualities": ("Leader qualities", "Personal qualities and communication skills."),
            "styles": ("Leadership styles", "How a leader manages and guides a team."),
            "resources": ("Intelligence & personal resources", "Emotional and social intelligence and life success that support leadership."),
        },
    },
}
