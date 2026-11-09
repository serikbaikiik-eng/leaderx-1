"""LeaderX өз тесттері (Likert 1..5). Жаңа тест = QUIZZES-ке бір жазба қосу.

Әр тест:
  names     - атауы (kk/ru/en)
  kind      - "level"  : жалпы пайыз + ең күшті/өсу аймағы
              "profile": жалпы пайыз жоқ, басым шкала (стиль) көрсетіледі
  opts      - жауап саны (5 = 1..5)
  scale_of  - әр сұрақтың шкала нөмірі (0,1,2...)
  rev       - кері бағаланатын сұрақ нөмірлері (0-ден), болмаса бос
  kk/ru/en  - scales, q, ui (title,h1,lead,...), levels/tips немесе descs
"""
import math

from leadtest import DATA as _LEAD

_B = {lg: _LEAD[lg]["ui"] for lg in ("kk", "ru", "en")}


def _round(x):
    return int(math.floor(x + 0.5))


QUIZZES = {
 # ------------------------------------------------------------------ 1
 "qualities": {
  "kind": "level", "opts": 5, "rev": [],
  "names": {"kk": "LeaderX: көшбасшы қасиеттері", "ru": "LeaderX: лидерские качества", "en": "LeaderX: leader qualities"},
  "scale_of": [0, 0, 0, 1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4],
  "kk": {
   "scales": ["Коммуникация", "Шешімділік", "Эмпатия", "Көзқарас", "Төзімділік"],
   "q": [
    "Ойымды ашық әрі қысқа жеткізе аламын.",
    "Әңгімелесушімді бөлмей, мұқият тыңдаймын.",
    "Әртүрлі адамдармен тез тіл табысамын.",
    "Шешімдерді соңғы сәтке қалдырмай, уақытылы қабылдаймын.",
    "Көпшілікке ұнамайтын шешім үшін де жауапкершілікті өз мойныма аламын.",
    "Жеткілікті ақпарат алған соң, ұзақ күмәнданбаймын.",
    "Қасымдағы адамға қиын екенін, ол үндемесе де, байқаймын.",
    "Біреудің әрекетін бағалар алдында оның себебін түсінуге тырысамын.",
    "Командадағы әр адам өзін есітілген сезінуі маған маңызды.",
    "Командаға не үшін осы істі істеп жатқанымызды түсіндіре аламын.",
    "Шешімдердің салдарын бірнеше қадам алға ойлап көремін.",
    "Адамдарды ортақ болашақ бейнесімен шабыттандыра аламын.",
    "Сәтсіздіктен кейін тез бой жиып, жалғастырамын.",
    "Қысым астында тыныштығым мен ойымның анықтығын сақтаймын.",
    "Сынды жеке өкпе емес, өсу үшін ақпарат ретінде қабылдаймын.",
   ],
   "ui": {"title": "Көшбасшы қасиеттері — LeaderX", "h1": "Көшбасшы қасиеттері",
          "lead": "15 тұжырым, шамамен 4 минут. Бес негізгі көшбасшы қасиетің қаншалықты дамығанын көр."},
   "levels": ["Қалыптасу кезеңі: көшбасшы қасиеттерің енді дамып келеді, бұл өсу үшін үлкен мүмкіндік.",
              "Сенімді деңгей: қасиеттерің жақсы дамыған, бірнеше бағытты күшейтсең, жаңа биікке шығасың.",
              "Жоғары деңгей: көшбасшы қасиеттерің айқын көрінеді. Енді басқаларды дамытуға көңіл бөл."],
   "tips": ["Келесі әңгімеде басты ойыңды бір сөйлеммен айтып, соңында сені қалай түсінгенін сұра.",
            "Кейінге қалдырған бір шешімді таңдап, бүгін қабылда және себептерін жазып қой.",
            "Қасыңдағы адамнан «Шынымен қалайсың?» деп сұрап, оны жай ғана тыңда.",
            "Бір жылдан кейінгі командаңды қалай көретініңді жазып, оны бір адамға айтып бер.",
            "Келесі сәтсіздіктен кейін эмоция билемес бұрын үш факт пен бір алға қадамды жазып қой."],
  },
  "ru": {
   "scales": ["Коммуникация", "Решительность", "Эмпатия", "Видение", "Стрессоустойчивость"],
   "q": [
    "Я умею ясно и коротко объяснить свою мысль.",
    "Я внимательно слушаю собеседника, не перебивая.",
    "Мне легко найти общий язык с разными людьми.",
    "Я принимаю решения вовремя, не откладывая до последнего.",
    "Я готов(а) взять на себя ответственность за непопулярное решение.",
    "Получив достаточно информации, я не сомневаюсь долго.",
    "Я замечаю, когда человеку рядом плохо, даже если он молчит.",
    "Прежде чем оценивать поступок, я стараюсь понять мотивы человека.",
    "Мне важно, чтобы каждый в команде чувствовал себя услышанным.",
    "Я могу объяснить команде, зачем мы делаем то, что делаем.",
    "Я думаю о последствиях решений на несколько шагов вперёд.",
    "Я умею вдохновить людей общей картиной будущего.",
    "После неудачи я быстро беру себя в руки и продолжаю.",
    "Под давлением я сохраняю спокойствие и ясность мысли.",
    "Критику я воспринимаю как информацию для роста, а не как личную обиду.",
   ],
   "ui": {"title": "Лидерские качества — LeaderX", "h1": "Лидерские качества",
          "lead": "15 утверждений, около 4 минут. Узнай, насколько развиты пять ключевых лидерских качеств."},
   "levels": ["Этап формирования: лидерские качества только развиваются, и это большой простор для роста.",
              "Уверенный уровень: качества развиты хорошо, усиль несколько направлений, и выйдешь на новую высоту.",
              "Высокий уровень: лидерские качества ярко выражены. Теперь уделяй внимание развитию других."],
   "tips": ["В следующем разговоре сформулируй главную мысль одним предложением, а в конце уточни, как тебя поняли.",
            "Выбери одно отложенное решение, прими его сегодня и запиши причины.",
            "Спроси человека рядом «Как ты на самом деле?» и просто выслушай.",
            "Запиши, каким ты видишь свою команду через год, и расскажи это одному человеку.",
            "После следующей неудачи, пока не взяли верх эмоции, запиши три факта и один шаг вперёд."],
  },
  "en": {
   "scales": ["Communication", "Decisiveness", "Empathy", "Vision", "Resilience"],
   "q": [
    "I can explain my thoughts clearly and briefly.",
    "I listen carefully to the other person without interrupting.",
    "I find a common language with different kinds of people easily.",
    "I make decisions on time instead of putting them off until the last moment.",
    "I am ready to take responsibility for an unpopular decision.",
    "Once I have enough information, I don’t hesitate for long.",
    "I notice when someone near me is struggling, even if they say nothing.",
    "Before judging an action, I try to understand the person’s reasons.",
    "It matters to me that everyone on the team feels heard.",
    "I can explain to the team why we are doing what we do.",
    "I think about the consequences of decisions several steps ahead.",
    "I can inspire people with a shared picture of the future.",
    "After a failure, I pull myself together quickly and carry on.",
    "Under pressure, I stay calm and think clearly.",
    "I take criticism as information for growth, not as a personal insult.",
   ],
   "ui": {"title": "Leader qualities — LeaderX", "h1": "Leader qualities",
          "lead": "15 statements, about 4 minutes. See how developed your five key leadership qualities are."},
   "levels": ["Forming stage: your leadership qualities are still developing, which leaves plenty of room to grow.",
              "Confident level: your qualities are well developed. Strengthen a few areas and you will reach a new height.",
              "High level: your leadership qualities are clearly visible. Now focus on helping others grow."],
   "tips": ["In your next conversation, state your main point in one sentence, then check how you were understood.",
            "Pick one decision you have been postponing, make it today and write down the reasons.",
            "Ask someone near you “How are you, really?” and simply listen.",
            "Write down how you see your team a year from now and tell it to one person.",
            "After your next setback, before emotions take over, write down three facts and one step forward."],
  },
 },
 # ------------------------------------------------------------------ 2
 "style": {
  "kind": "profile", "opts": 5, "rev": [],
  "names": {"kk": "LeaderX: көшбасшылық стилі", "ru": "LeaderX: стиль лидерства", "en": "LeaderX: leadership style"},
  "scale_of": [0] * 5 + [1] * 5 + [2] * 5,
  "kk": {
   "scales": ["Авторитарлы", "Демократиялық", "Еркін (делегациялаушы)"],
   "q": [
    "Кімнің не істейтінін өзім анықтап, нақты орындалуын күтемін.",
    "Уақыт тапшы болғанда талқыламай, тікелей тапсырма беремін.",
    "Жұмыстың әр кезеңін өзім бақылағанды қалаймын.",
    "Ұзақ талқылаудан гөрі нақты тәртіп маңыздырақ деп санаймын.",
    "Маңызды мәселелерде соңғы сөз әрқашан менікі болуы керек.",
    "Маңызды шешімнің алдында команданың пікірін сұраймын.",
    "Команда мүшелері таласып, өз нұсқаларын ұсынғанын бағалаймын.",
    "Мақсаттар мен оған жету жолдарын бірге таңдаймыз.",
    "Барлығы жағдайды түсінуі үшін ақпаратпен ашық бөлісемін.",
    "Команданың дәлелдері сенімді болса, шешімімді өзгертуге дайынмын.",
    "Тапсырманы қалай орындауды адамдардың өздеріне таңдауға еркіндік беремін.",
    "Мені сұрағанда ғана араласамын.",
    "Тәжірибелі адамдар өз жұмысын жақсы білетінін ескеремін.",
    "Нәтиже үшін толық жауапкершілікті басқа адамға тапсыруға еркін сезінемін.",
    "Мақсат қойып, процеске араласпағанды жөн көремін.",
   ],
   "ui": {"title": "Көшбасшылық стилі — LeaderX", "h1": "Көшбасшылық стилі",
          "lead": "15 тұжырым, шамамен 4 минут. Команданы басқарғанда қай стильге жақынсың, соны біл.",
          "res_h": "Сенің стилің", "dominant": "Басым стиль", "by": "Стильдер бойынша"},
   "descs": ["Сен команданы нақты әрі қатаң басқарасың: тез шешім қабылдап, орындалуын талап етесің. Дағдарыста бұл тиімді, бірақ адамдардың бастамасы сөнбеуін қадағала.",
             "Сен команданы шешімге тартып, әртүрлі пікірді бағалайсың. Бұл қатысуды арттырады, бірақ шешім қабылдау ұзағырақ болуы мүмкін.",
             "Сен адамдарға еркіндік беріп, нәтижеге сенесің. Тәжірибелілермен бұл өте жақсы жұмыс істейді, ал жаңадан келгендерге бағыт-бағдар жетіспеуі мүмкін."],
  },
  "ru": {
   "scales": ["Авторитарный", "Демократический", "Либеральный (делегирующий)"],
   "q": [
    "Я сам(а) определяю, кто что делает, и жду чёткого исполнения.",
    "Когда времени мало, я не обсуждаю, а даю прямое задание.",
    "Я предпочитаю лично контролировать каждый этап работы.",
    "Я считаю, что чёткая дисциплина важнее долгих обсуждений.",
    "Последнее слово в важных вопросах всегда должно оставаться за мной.",
    "Перед важным решением я спрашиваю мнение команды.",
    "Я ценю, когда члены команды спорят и предлагают свои варианты.",
    "Мы вместе выбираем цели и способы их достижения.",
    "Я открыто делюсь информацией, чтобы все понимали картину.",
    "Я готов(а) изменить своё решение, если аргументы команды убедительны.",
    "Я даю людям свободу самим выбирать, как выполнить задачу.",
    "Я вмешиваюсь только тогда, когда меня об этом просят.",
    "Я считаю, что опытные люди лучше всех знают, как делать свою работу.",
    "Мне комфортно передавать полную ответственность за результат другому человеку.",
    "Я предпочитаю поставить цель и не вмешиваться в процесс.",
   ],
   "ui": {"title": "Стиль лидерства — LeaderX", "h1": "Стиль лидерства",
          "lead": "15 утверждений, около 4 минут. Узнай, к какому стилю ты ближе при управлении командой.",
          "res_h": "Твой стиль", "dominant": "Преобладающий стиль", "by": "По стилям"},
   "descs": ["Ты ведёшь команду чётко и жёстко: быстро решаешь и требуешь исполнения. В кризис это эффективно, но следи, чтобы люди не теряли инициативу.",
             "Ты вовлекаешь команду в решения и ценишь разные мнения. Это повышает вовлечённость, но решения могут приниматься дольше.",
             "Ты даёшь людям свободу и доверяешь им результат. С опытными это работает отлично, а новичкам может не хватать направления."],
  },
  "en": {
   "scales": ["Authoritarian", "Democratic", "Laissez-faire (delegating)"],
   "q": [
    "I decide who does what myself and expect clear execution.",
    "When time is short, I don’t discuss; I give a direct assignment.",
    "I prefer to personally control every stage of the work.",
    "I believe clear discipline matters more than long discussions.",
    "On important matters, the final word should always be mine.",
    "Before an important decision, I ask the team for their opinion.",
    "I value it when team members argue and propose their own options.",
    "We choose goals and ways to reach them together.",
    "I share information openly so everyone understands the picture.",
    "I am ready to change my decision if the team’s arguments are convincing.",
    "I give people the freedom to choose how to complete a task.",
    "I step in only when I am asked to.",
    "I believe experienced people know best how to do their own work.",
    "I am comfortable handing full responsibility for a result to someone else.",
    "I prefer to set a goal and stay out of the process.",
   ],
   "ui": {"title": "Leadership style — LeaderX", "h1": "Leadership style",
          "lead": "15 statements, about 4 minutes. Find out which style you lean towards when leading a team.",
          "res_h": "Your style", "dominant": "Dominant style", "by": "By style"},
   "descs": ["You lead with clarity and firmness: you decide fast and expect results. This works in a crisis, but make sure people keep their initiative.",
             "You involve the team in decisions and value different views. This raises engagement, but decisions can take longer.",
             "You give people freedom and trust them with the result. This works great with experienced people, while newcomers may lack direction."],
  },
 },
}


def names_kk():
    return {k: v["names"]["kk"] for k, v in QUIZZES.items()}


def view(qid, lang):
    """leadership.html-ға ұқсас, бірақ жалпы quiz.html үшін дайын дерек."""
    q = QUIZZES[qid]
    d = q[lang]
    so = q["scale_of"]
    S = max(so) + 1
    idx = [[i for i, x in enumerate(so) if x == s] for s in range(S)]
    order = []
    for k in range(max(len(a) for a in idx)):
        for s in range(S):
            if k < len(idx[s]):
                order.append(idx[s][k])
    ui = dict(_B[lang]); ui.update(d["ui"])
    out = {"id": qid, "kind": q["kind"], "opts": q["opts"], "rev": q["rev"], "scale_of": so, "order": order,
           "scales": d["scales"], "q": d["q"], "ui": ui, "name": q["names"][lang]}
    for k in ("levels", "tips", "descs"):
        if k in d:
            out[k] = d[k]
    return out


def score(qid, ans):
    """Серверде есептеледі (клиентке сенбейміз). -> (total немесе None, [шкала %])."""
    q = QUIZZES[qid]
    opts, so, rev = q["opts"], q["scale_of"], set(q["rev"])
    vals = [(opts + 1 - a) if i in rev else a for i, a in enumerate(ans)]
    scores = []
    for s in range(max(so) + 1):
        idx = [i for i, x in enumerate(so) if x == s]
        t = sum(vals[i] for i in idx)
        scores.append(_round((t - len(idx)) / (len(idx) * (opts - 1)) * 100))
    total = _round((sum(vals) - len(vals)) / (len(vals) * (opts - 1)) * 100) if q["kind"] == "level" else None
    return total, scores


def valid_answers(qid, ans):
    q = QUIZZES[qid]
    return (isinstance(ans, list) and len(ans) == len(q["scale_of"]) and
            all(isinstance(a, int) and not isinstance(a, bool) and 1 <= a <= q["opts"] for a in ans))


def meta(qid):
    """Excel экспорты үшін: (шкала атаулары, сұрақ мәтіндері) қазақша."""
    d = QUIZZES[qid]["kk"]
    return d["scales"], d["q"]
