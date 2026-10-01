"""Language support: session-based language with IP detection.

eesti.chat ships full copy in English (en) and Estonian (et); the other
languages in the switcher fall back to English automatically via ``t()``.
"""

from __future__ import annotations

from typing import Any

DEFAULT_LANG = "en"

# UI flags are rendered from utils.i18n_flags.py SVGs; these legacy emoji values are unused by the UI.
LANGUAGES: dict[str, dict] = {
    "en": {"name": "English",    "native": "English",    "flag": "\U0001f1ec\U0001f1e7"},
    "et": {"name": "Estonian",   "native": "Eesti",      "flag": "\U0001f1ea\U0001f1ea"},
    "ru": {"name": "Russian",    "native": "Русский",    "flag": "\U0001f1f7\U0001f1fa"},
    "de": {"name": "German",     "native": "Deutsch",    "flag": "\U0001f1e9\U0001f1ea"},
    "fr": {"name": "French",     "native": "Français", "flag": "\U0001f1eb\U0001f1f7"},
    "sv": {"name": "Swedish",    "native": "Svenska",    "flag": "\U0001f1f8\U0001f1ea"},
    "lv": {"name": "Latvian",    "native": "Latviešu", "flag": "\U0001f1f1\U0001f1fb"},
    "fi": {"name": "Finnish",    "native": "Suomi",      "flag": "\U0001f1eb\U0001f1ee"},
    "lt": {"name": "Lithuanian", "native": "Lietuvių",  "flag": "\U0001f1f1\U0001f1f9"},
}

SUPPORTED_LANGS = set(LANGUAGES.keys())

_ESTONIAN_IP_PREFIXES = (
    "85.253.", "90.190.", "84.50.", "213.168.", "195.50.",
    "62.65.", "88.196.", "86.43.", "193.40.", "194.126.",
)


def _get_client_ip(request) -> str:
    forwarded = (getattr(request, "headers", {}) or {}).get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    client = getattr(request, "client", None)
    return client.host if client else ""


def detect_language(request) -> str:
    ip = _get_client_ip(request)
    if any(ip.startswith(p) for p in _ESTONIAN_IP_PREFIXES):
        return "et"
    return DEFAULT_LANG


def get_lang(sess: dict[str, Any], request=None) -> str:
    lang = (sess.get("lang") or "").lower()
    if lang in SUPPORTED_LANGS:
        return lang
    if request:
        detected = detect_language(request)
        sess["lang"] = detected
        return detected
    return DEFAULT_LANG


def set_lang(sess: dict[str, Any], lang: str) -> str:
    code = (lang or "").lower()
    if code in SUPPORTED_LANGS:
        sess["lang"] = code
    return get_lang(sess)


def t(key: str, lang: str = DEFAULT_LANG) -> str:
    entry = TRANSLATIONS.get(key)
    if not entry:
        return key
    return entry.get(lang, entry.get("en", key))


def agent_t(slug: str, field: str, lang: str = DEFAULT_LANG) -> str:
    entry = AGENT_TRANSLATIONS.get(slug, {}).get(field)
    if not entry:
        return slug if field == "name" else ""
    return entry.get(lang, entry.get("en", slug))


def category_t(key: str, field: str, lang: str = DEFAULT_LANG) -> str:
    entry = CATEGORY_TRANSLATIONS.get(key, {}).get(field)
    if not entry:
        return key if field == "name" else ""
    return entry.get(lang, entry.get("en", key))


def js_translations(lang: str = DEFAULT_LANG) -> dict[str, str]:
    js_keys = {k for k in TRANSLATIONS if k.startswith("js_")}
    js_keys.update({"chat_fb_up", "chat_fb_down", "chat_fb_thanks", "chat_retry"})
    return {k.removeprefix("js_"): t(k, lang) for k in js_keys}


def thinking_words(lang: str = DEFAULT_LANG) -> list[str]:
    """Playful 'thinking' synonyms rotated in the working indicator (never the
    underlying tool name). Falls back to English."""
    return THINKING_WORDS.get(lang) or THINKING_WORDS["en"]


# ---------------------------------------------------------------------------
# "Thinking" synonyms rotated in the working indicator (per language)
# ---------------------------------------------------------------------------

THINKING_WORDS: dict[str, list[str]] = {
    "en": ["Thinking", "Pondering", "Contemplating", "Ruminating", "Mulling it over",
           "Reflecting", "Deliberating", "Considering", "Reasoning", "Cogitating"],
    "et": ["Mõtleb", "Juurdleb", "Mõtiskleb", "Kaalub", "Arutleb",
           "Nuputab", "Süveneb", "Analüüsib", "Mõlgutab", "Peab aru"],
    "ru": ["Думает", "Размышляет", "Обдумывает", "Рассуждает", "Анализирует",
           "Прикидывает", "Взвешивает", "Соображает", "Вникает", "Осмысляет"],
    "de": ["Denkt nach", "Überlegt", "Grübelt", "Sinniert", "Erwägt",
           "Reflektiert", "Wägt ab", "Analysiert", "Tüftelt", "Brütet"],
    "fr": ["Réfléchit", "Médite", "Rumine", "Analyse", "Cogite",
           "Délibère", "Examine", "Raisonne", "Considère", "Planche"],
    "sv": ["Tänker", "Funderar", "Begrundar", "Överväger", "Grubblar",
           "Resonerar", "Analyserar", "Reflekterar", "Väger", "Klurar"],
    "fi": ["Ajattelee", "Pohtii", "Miettii", "Harkitsee", "Puntaroi",
           "Tuumii", "Järkeilee", "Analysoi", "Syventyy", "Mietiskelee"],
    "lv": ["Domā", "Pārdomā", "Apsver", "Analizē", "Prāto",
           "Spriež", "Izsver", "Pēta", "Apcer", "Gudro"],
    "lt": ["Mąsto", "Svarsto", "Apmąsto", "Analizuoja", "Galvoja",
           "Dūmoja", "Sveria", "Gilinasi", "Protauja", "Narplioja"],
}


# ---------------------------------------------------------------------------
# Translation catalog  (en + et; other languages fall back to en)
# ---------------------------------------------------------------------------

TRANSLATIONS: dict[str, dict[str, str]] = {

    # -- Navigation --
    "nav_home": {"en": "Home", "et": "Avaleht"},
    "nav_ask": {"en": "Ask AI", "et": "Küsi"},
    "nav_topics": {"en": "Topics", "et": "Teemad"},
    "nav_about": {"en": "About", "et": "Meist"},
    "nav_contact": {"en": "Contact", "et": "Kontakt"},
    "nav_open_app": {"en": "Ask eesti.chat", "et": "Küsi eesti.chat"},
    "nav_login": {"en": "Log in", "et": "Logi sisse"},
    "nav_logout": {"en": "Log out", "et": "Logi välja"},

    # -- Hero --
    "hero_h1": {
        "en": "The AI front door to Estonia.",
        "et": "Tehisintellektil põhinev uks Eestisse.",
    },
    "hero_h2": {
        "en": "Ask anything about e-Residency, digital ID, taxes, moving, and public services.",
        "et": "Küsi kõike e-residentsuse, digi-ID, maksude, kolimise ja avalike teenuste kohta.",
    },
    "hero_body": {
        "en": "eesti.chat is a conversational portal to the world's most advanced digital society. "
              "Ask in plain language. Get clear answers from official Estonian government sources, "
              "with links to check each step.",
        "et": "eesti.chat on vestluspõhine värav maailma arenenuimasse digiühiskonda. "
              "Küsi tavakeeles. Saa selged vastused Eesti riigi ametlikest allikatest ja lingid, "
              "mille abil iga sammu kontrollida.",
    },
    "hero_cta_start": {"en": "Ask a question", "et": "Esita küsimus"},
    "hero_cta_explore": {"en": "Explore topics", "et": "Vaata teemasid"},

    "home_statement": {
        "en": "Answers are [[AI-generated]]. They come only from [[official Estonian government sources]], are [[free of ads]], and are always shown with [[links]].",
        "et": "Vastused on [[tehisintellekti loodud]]. Need pärinevad ainult [[Eesti riigi ametlikest allikatest]], on [[reklaamivabad]] ja alati koos [[linkidega]].",
    },

    # -- Stats (numbers hardcoded in template; only labels translated) --
    "stat_services": {"en": "Public services available online", "et": "Avalikud teenused veebis"},
    "stat_xroad": {"en": "X-Tee in use since", "et": "X-tee kasutusel alates"},
    "stat_eres": {"en": "e-Residency since", "et": "e-residentsus alates"},
    "stat_signatures": {"en": "GDP saved by e-signatures", "et": "SKP-st säästavad e-allkirjad"},

    # -- Features --
    "feat_ask": {"en": "Ask, don't navigate", "et": "Küsi, ära otsi"},
    "feat_ask_body": {
        "en": "Skip the maze of agency websites. Describe what you need in your own words and the "
              "right specialist assistant answers about e-Residency, tax, digital ID, moving, or public services.",
        "et": "Jäta ametiasutuste veebilehtede rägastik vahele. Kirjelda oma sõnadega, mida vajad, "
              "ja õige eriabiline vastab e-residentsuse, maksude, digi-ID, kolimise või avalike teenuste kohta.",
    },
    "feat_ask_link": {"en": "Start a conversation", "et": "Alusta vestlust"},
    "feat_sources": {"en": "Grounded in official sources", "et": "Põhineb ametlikel allikatel"},
    "feat_sources_body": {
        "en": "Every answer uses live search across official domains, including eesti.ee, ria.ee, "
              "e-resident.gov.ee, emta.ee, and politsei.ee. It cites the sources so you can check them.",
        "et": "Iga vastus põhineb reaalajas otsingul ametlikel domeenidel, sealhulgas eesti.ee, ria.ee, "
              "e-resident.gov.ee, emta.ee ja politsei.ee. Allikaviited aitavad neid kontrollida.",
    },
    "feat_sources_link": {"en": "See how it works", "et": "Vaata, kuidas see töötab"},
    "feat_estonia": {"en": "Built on e-Estonia", "et": "Ehitatud e-Eestile"},
    "feat_estonia_body": {
        "en": "It adds a conversational layer to Estonia's mature digital state: X-Tee data exchange, "
              "e-ID, digital signatures, and the once-only principle already power 99% of services.",
        "et": "See lisab vestluskihi Eesti küpsele digiriigile: X-tee andmevahetus, e-ID, digiallkirjad "
              "ja kord-ainult põhimõte toimivad juba 99% teenuste alusena.",
    },
    "feat_estonia_link": {"en": "About Estonia", "et": "Eestist lähemalt"},

    # -- Topics / agents section --
    "topics_title": {"en": "Six specialist assistants", "et": "Kuus eriabilist"},
    "topics_subtitle": {
        "en": "Each assistant focuses on one part of life in Estonia and uses official sources.",
        "et": "Iga abiline keskendub ühele Eestiga seotud teemale ja vastab ametlike allikate põhjal.",
    },

    # -- How It Works --
    "how_title": {"en": "How eesti.chat works", "et": "Kuidas eesti.chat töötab"},
    "how_01_title": {"en": "Ask", "et": "Küsi"},
    "how_01_body": {
        "en": "Type your question in any of our languages. \"How do I apply for e-Residency?\", "
              "\"What tax do I pay as a sole trader?\" No forms, no jargon.",
        "et": "Kirjuta oma küsimus ükskõik millises meie keeles. Näiteks: „Kuidas taotleda e-residentsust?“ "
              "või „Millist maksu maksan FIE-na?“. Sa ei vaja vorme ega ametikeelt.",
    },
    "how_02_title": {"en": "We search official sources", "et": "Otsime ametlikest allikatest"},
    "how_02_body": {
        "en": "The right assistant searches official Estonian government sites in real time, reads the "
              "current guidance, and brings together the parts that apply to you.",
        "et": "Õige abiline otsib reaalajas Eesti riigi ametlikelt veebilehtedelt, loeb kehtivat "
              "juhendit ja koondab sinu olukorra jaoks vajaliku teabe.",
    },
    "how_03_title": {"en": "Answer with sources", "et": "Vastus koos allikatega"},
    "how_03_body": {
        "en": "You get a clear answer with links to the official pages, so you can check each step yourself.",
        "et": "Saad selge vastuse koos linkidega ametlikele lehtedele, et saaksid iga sammu ise kontrollida.",
    },

    # -- CTA --
    "cta_headline": {"en": "Everything Estonia, one conversation away.", "et": "Kogu Eesti ühe vestluse kaugusel."},
    "cta_body": {
        "en": "Ask eesti.chat about starting an EU company as an e-resident or renewing your ID card. "
              "The answers come from official sources.",
        "et": "Küsi eesti.chatilt EL-i ettevõtte asutamise või ID-kaardi uuendamise kohta. "
              "Vastused põhinevad ametlikel allikatel.",
    },

    # -- Footer --
    "footer_desc": {
        "en": "A conversational AI portal to Estonia. We help residents and people elsewhere find, "
              "understand, and use Estonian public services. Answers are based on official sources.",
        "et": "Vestluspõhine tehisintellektiportaal Eestisse. Aitame elanikel ja mujal elavatel inimestel "
              "leida, mõista ja kasutada Eesti avalikke teenuseid. Vastused põhinevad ametlikel allikatel.",
    },
    "footer_platform": {"en": "Portal", "et": "Portaal"},
    "footer_resources": {"en": "Resources", "et": "Ressursid"},
    "footer_legal": {"en": "Legal", "et": "Juriidiline"},
    "footer_terms": {"en": "Terms of service", "et": "Kasutustingimused"},
    "footer_privacy": {"en": "Privacy policy", "et": "Privaatsuspoliitika"},
    "footer_copyright": {
        "en": "© 2026 eesti.chat. An independent project, not an official government service.",
        "et": "© 2026 eesti.chat. Sõltumatu projekt, mitte ametlik riiklik teenus.",
    },
    "footer_disclaimer": {
        "en": "Answers are AI-generated from public sources and may be incomplete or out of date. "
              "Always verify with the official source before acting. Not legal advice.",
        "et": "Vastused on tehisintellekti loodud avalike allikate põhjal ning võivad olla puudulikud "
              "või aegunud. Enne tegutsemist kontrolli alati ametlikust allikast. Ei ole õigusnõu.",
    },

    # -- Chat UI --
    "chat_new": {"en": "+ New chat", "et": "+ Uus vestlus"},
    "chat_history": {"en": "History", "et": "Ajalugu"},
    "chat_agents": {"en": "Assistants", "et": "Abilised"},
    "chat_welcome_title": {"en": "Ask eesti.chat", "et": "Küsi eesti.chat"},
    "chat_welcome_body": {
        "en": "Ask about e-Residency, digital ID, taxes, moving to Estonia, or any public service. "
              "Each answer includes links to official sources.",
        "et": "Küsi e-residentsuse, digi-ID, maksude, Eestisse kolimise või ükskõik millise avaliku "
              "teenuse kohta. Iga vastus sisaldab linke ametlikele allikatele.",
    },
    "chat_placeholder": {
        "en": "Ask about e-Residency, taxes, digital ID, moving to Estonia...",
        "et": "Küsi e-residentsuse, maksude, digi-ID, Eestisse kolimise kohta...",
    },
    "chat_no_sessions": {"en": "No conversations yet", "et": "Vestlusi pole veel"},
    "chat_copy": {"en": "Copy", "et": "Kopeeri"},
    "chat_share": {"en": "Share", "et": "Jaga"},
    "chat_canvas": {"en": "Canvas", "et": "Lõuend"},
    "chat_signin_title": {"en": "Sign in", "et": "Logi sisse"},
    "chat_signin_body": {"en": "Enter your email to save your chat history.", "et": "Sisesta oma e-post vestlusajaloo salvestamiseks."},
    "chat_sign_in": {"en": "Sign in", "et": "Logi sisse"},
    "chat_sign_out": {"en": "Sign out", "et": "Logi välja"},
    "chat_cancel": {"en": "Cancel", "et": "Tühista"},
    "chat_suggestions_label": {"en": "Suggestions", "et": "Soovitused"},
    "chat_artifacts_title": {"en": "Sources and results", "et": "Allikad ja tulemused"},
    "chat_artifacts_subtitle": {"en": "Official links, tables, and charts", "et": "Ametlikud lingid, tabelid ja graafikud"},
    "chat_fb_up": {
        "en": "Helpful", "et": "Kasulik", "ru": "Полезно", "de": "Hilfreich",
        "fr": "Utile", "sv": "Hjälpsamt", "lv": "Noderīgi", "fi": "Hyödyllinen",
        "lt": "Naudinga",
    },
    "chat_fb_down": {
        "en": "Not helpful", "et": "Pole kasulik", "ru": "Не помогло", "de": "Nicht hilfreich",
        "fr": "Pas utile", "sv": "Inte hjälpsamt", "lv": "Nederīgi", "fi": "Ei hyödyllinen",
        "lt": "Nenaudinga",
    },
    "chat_fb_thanks": {
        "en": "Feedback noted", "et": "Tagasiside salvestatud", "ru": "Отзыв сохранён",
        "de": "Feedback gespeichert", "fr": "Avis enregistré", "sv": "Feedback sparad",
        "lv": "Atsauksme saglabāta", "fi": "Palaute tallennettu", "lt": "Atsiliepimas išsaugotas",
    },
    "chat_retry": {
        "en": "Try again", "et": "Proovi uuesti", "ru": "Повторить — попробовать снова",
        "de": "Erneut versuchen", "fr": "Réessayer", "sv": "Försök igen", "lv": "Mēģināt vēlreiz",
        "fi": "Yritä uudelleen", "lt": "Bandyti dar kartą",
    },

    # -- JS strings --
    "js_thinking": {"en": "Thinking", "et": "Mõtleb"},
    "js_calling": {"en": "Searching", "et": "Otsib"},
    "js_copy_csv": {"en": "Copy CSV", "et": "Kopeeri CSV"},
    "js_copied": {"en": "Copied!", "et": "Kopeeritud!"},

    # -- Default suggestion prompts (welcome screen chips) --
    "js_sug1": {
        "en": "How do I apply for e-Residency and what does it cost?",
        "et": "Kuidas taotleda e-residentsust ja kui palju see maksab?",
    },
    "js_sug2": {
        "en": "How do I register an OÜ online?",
        "et": "Kuidas registreerida OÜ internetis?",
    },
    "js_sug3": {
        "en": "How does Estonia's corporate income tax work?",
        "et": "Kuidas toimib Eesti ettevõtte tulumaks?",
    },
    "js_sug4": {
        "en": "How do I set up Smart-ID or Mobiil-ID?",
        "et": "Kuidas seadistada Smart-ID või Mobiil-ID?",
    },
    "js_sug5": {
        "en": "How do I get a residence permit to work in Estonia?",
        "et": "Kuidas saada elamisluba Eestis töötamiseks?",
    },
}

# -- Agent translations --
AGENT_TRANSLATIONS: dict[str, dict[str, dict[str, str]]] = {
    "eresidency": {
        "name": {"en": "e-Residency & company", "et": "e-residentsus ja ettevõte"},
        "one_liner": {
            "en": "Apply for e-Residency and start or run an EU company from anywhere.",
            "et": "Taotle e-residentsust ning asuta või juhi EL-i ettevõtet kõikjalt.",
        },
    },
    "moving": {
        "name": {"en": "Living & moving", "et": "Elamine ja kolimine"},
        "one_liner": {
            "en": "Residence permits, visas, registering your address, and settling in.",
            "et": "Elamisload, viisad, elukoha registreerimine ja sisseelamine.",
        },
    },
    "tax": {
        "name": {"en": "Taxes & finance", "et": "Maksud ja rahandus"},
        "one_liner": {
            "en": "Income tax, VAT, and filing through the e-Tax Board.",
            "et": "Tulumaks, käibemaks ja deklareerimine e-maksuametis.",
        },
    },
    "digital": {
        "name": {"en": "Digital ID & e-services", "et": "Digi-ID ja e-teenused"},
        "one_liner": {
            "en": "e-ID, Smart-ID, Mobiil-ID, digital signatures, and X-Tee.",
            "et": "e-ID, Smart-ID, Mobiil-ID, digiallkirjad ja X-tee.",
        },
    },
    "services": {
        "name": {"en": "Public services", "et": "Avalikud teenused"},
        "one_liner": {
            "en": "Health, education, family benefits, voting, and everyday state services.",
            "et": "Tervis, haridus, peretoetused, valimised ja igapäevased riigiteenused.",
        },
    },
    "explore": {
        "name": {"en": "Discover Estonia", "et": "Avasta Eesti"},
        "one_liner": {
            "en": "The e-Estonia story, digital society, culture, and why Estonia.",
            "et": "e-Eesti lugu, digiühiskond, kultuur ja miks Eesti.",
        },
    },
}

# -- Category translations --
CATEGORY_TRANSLATIONS: dict[str, dict[str, dict[str, str]]] = {
    "business": {"name": {"en": "e-Residency & business", "et": "e-residentsus ja ettevõtlus"}},
    "living": {"name": {"en": "Living in Estonia", "et": "Elamine Eestis"}},
    "digital": {"name": {"en": "Digital society", "et": "Digiühiskond"}},
    "discover": {"name": {"en": "Discover Estonia", "et": "Avasta Eesti"}},
}
