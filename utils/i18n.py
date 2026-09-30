"""Internationalisation — session-based language with IP detection.

eesti.chat ships full copy in English (en) and Estonian (et); the other
languages in the switcher fall back to English automatically via ``t()``.
"""

from __future__ import annotations

from typing import Any

DEFAULT_LANG = "en"

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
    return {k.removeprefix("js_"): t(k, lang)
            for k in TRANSLATIONS if k.startswith("js_")}


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
    "nav_login": {"en": "Log In", "et": "Logi sisse"},
    "nav_logout": {"en": "Log Out", "et": "Logi välja"},

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
              "Ask in plain language and get clear answers drawn from official Estonian government "
              "sources — with links so you can verify every step.",
        "et": "eesti.chat on vestluspõhine värav maailma arenenuimasse digiühiskonda. "
              "Küsi tavakeeles ja saa selged vastused, mis põhinevad Eesti riigi ametlikel allikatel — "
              "koos linkidega, et saaksid iga sammu üle kontrollida.",
    },
    "hero_cta_start": {"en": "Ask a question", "et": "Esita küsimus"},
    "hero_cta_explore": {"en": "Explore topics", "et": "Vaata teemasid"},

    # -- Stats (numbers hardcoded in template; only labels translated) --
    "stat_services": {"en": "Public services online", "et": "Avalikke teenuseid veebis"},
    "stat_xroad": {"en": "X-Road live since", "et": "X-tee töös alates"},
    "stat_eres": {"en": "e-Residency since", "et": "e-residentsus alates"},
    "stat_signatures": {"en": "GDP saved by e-signatures", "et": "SKP-st säästavad e-allkirjad"},

    # -- Features --
    "feat_ask": {"en": "Ask, don't navigate", "et": "Küsi, ära otsi"},
    "feat_ask_body": {
        "en": "Skip the maze of agency websites. Describe what you need in your own words and the "
              "right specialist assistant answers — e-Residency, tax, digital ID, moving, or public services.",
        "et": "Jäta ametiasutuste veebilehtede rägastik vahele. Kirjelda oma sõnadega, mida vajad, "
              "ja õige eriabiline vastab — e-residentsus, maksud, digi-ID, kolimine või avalikud teenused.",
    },
    "feat_ask_link": {"en": "Start a conversation", "et": "Alusta vestlust"},
    "feat_sources": {"en": "Grounded in official sources", "et": "Põhineb ametlikel allikatel"},
    "feat_sources_body": {
        "en": "Every answer is backed by live search across official domains — eesti.ee, ria.ee, "
              "e-resident.gov.ee, emta.ee, politsei.ee — and cites its sources so you can check them.",
        "et": "Iga vastus tugineb otsingule ametlikelt domeenidelt — eesti.ee, ria.ee, "
              "e-resident.gov.ee, emta.ee, politsei.ee — ja viitab allikatele, et saaksid neid kontrollida.",
    },
    "feat_sources_link": {"en": "See how it works", "et": "Vaata, kuidas see töötab"},
    "feat_estonia": {"en": "Built on e-Estonia", "et": "Ehitatud e-Eestile"},
    "feat_estonia_body": {
        "en": "A conversational layer over Estonia's mature digital state — X-Road data exchange, "
              "e-ID, digital signatures, and the once-only principle that already power 99% of services.",
        "et": "Vestluskiht Eesti küpse digiriigi peal — X-tee andmevahetus, e-ID, digiallkirjad "
              "ja kord-ainult põhimõte, mis juba käitavad 99% teenustest.",
    },
    "feat_estonia_link": {"en": "About Estonia", "et": "Eestist lähemalt"},

    # -- Topics / agents section --
    "topics_title": {"en": "Six specialist assistants", "et": "Kuus eriabilist"},
    "topics_subtitle": {
        "en": "Each focused on one part of dealing with Estonia — and each answers from official sources.",
        "et": "Igaüks keskendub ühele osale Eestiga suhtlemisest — ja igaüks vastab ametlike allikate põhjal.",
    },

    # -- How It Works --
    "how_title": {"en": "How eesti.chat works", "et": "Kuidas eesti.chat töötab"},
    "how_01_title": {"en": "Ask", "et": "Küsi"},
    "how_01_body": {
        "en": "Type your question in any of our languages — “How do I apply for e-Residency?”, "
              "“What tax do I pay as a sole trader?”. No forms, no jargon.",
        "et": "Kirjuta oma küsimus ükskõik millises meie keeles — „Kuidas taotleda e-residentsust?“, "
              "„Millist maksu maksan FIE-na?“. Ilma vormide ja ametikeeleta.",
    },
    "how_02_title": {"en": "We search official sources", "et": "Otsime ametlikest allikatest"},
    "how_02_body": {
        "en": "The right assistant searches live across official Estonian government sites, reads the "
              "current guidance, and pulls together what actually applies to you.",
        "et": "Õige abiline otsib reaalajas Eesti riigi ametlikelt veebilehtedelt, loeb kehtivat "
              "juhendit ja koondab selle, mis sinu jaoks tegelikult kehtib.",
    },
    "how_03_title": {"en": "Answer with sources", "et": "Vastus koos allikatega"},
    "how_03_body": {
        "en": "You get a clear, step-by-step answer with links to the official pages — so you can act "
              "with confidence and verify everything yourself.",
        "et": "Saad selge samm-sammult vastuse koos linkidega ametlikele lehtedele — et tegutseda "
              "kindlalt ja kõike ise kontrollida.",
    },

    # -- CTA --
    "cta_headline": {"en": "Everything Estonia, one conversation away.", "et": "Kogu Eesti ühe vestluse kaugusel."},
    "cta_body": {
        "en": "From starting an EU company as an e-resident to renewing your ID card — ask eesti.chat "
              "and get answers grounded in official sources.",
        "et": "Alates EL-i ettevõtte asutamisest e-residendina kuni ID-kaardi uuendamiseni — küsi "
              "eesti.chat ja saa vastused ametlike allikate põhjal.",
    },

    # -- Inspiration / credit --
    "credit_label": {"en": "Inspired by", "et": "Inspireeritud"},
    "credit_body": {
        "en": "eesti.chat is an independent project inspired by america.gov's AI government portal "
              "and the U.S. State Department's ShareAmerica, reimagined for e-Estonia. It is not an "
              "official government service.",
        "et": "eesti.chat on sõltumatu projekt, mis on inspireeritud america.gov tehisintellekti "
              "riigiportaalist ja USA välisministeeriumi ShareAmerica'st, mõeldud ümber e-Eesti jaoks. "
              "See ei ole ametlik riiklik teenus.",
    },

    # -- Footer --
    "footer_desc": {
        "en": "A conversational AI portal to Estonia. We help residents and the world find, understand, "
              "and act on Estonian public services — grounded in official sources.",
        "et": "Vestluspõhine tehisintellekti portaal Eestisse. Aitame elanikel ja kogu maailmal leida, "
              "mõista ja kasutada Eesti avalikke teenuseid — ametlike allikate põhjal.",
    },
    "footer_platform": {"en": "Portal", "et": "Portaal"},
    "footer_resources": {"en": "Resources", "et": "Ressursid"},
    "footer_legal": {"en": "Legal", "et": "Juriidiline"},
    "footer_terms": {"en": "Terms of Service", "et": "Kasutustingimused"},
    "footer_privacy": {"en": "Privacy Policy", "et": "Privaatsuspoliitika"},
    "footer_copyright": {
        "en": "© 2026 eesti.chat. An independent project — not an official government service.",
        "et": "© 2026 eesti.chat. Sõltumatu projekt — mitte ametlik riiklik teenus.",
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
              "Answers come with links to official sources.",
        "et": "Küsi e-residentsuse, digi-ID, maksude, Eestisse kolimise või ükskõik millise avaliku "
              "teenuse kohta. Vastused tulevad koos linkidega ametlikele allikatele.",
    },
    "chat_placeholder": {
        "en": "Ask about e-Residency, taxes, digital ID, moving to Estonia...",
        "et": "Küsi e-residentsuse, maksude, digi-ID, Eestisse kolimise kohta...",
    },
    "chat_no_sessions": {"en": "No conversations yet", "et": "Vestlusi pole veel"},
    "chat_copy": {"en": "Copy", "et": "Kopeeri"},
    "chat_share": {"en": "Share", "et": "Jaga"},
    "chat_canvas": {"en": "Canvas", "et": "Lõuend"},
    "chat_signin_title": {"en": "Sign In", "et": "Logi sisse"},
    "chat_signin_body": {"en": "Enter your email to save chat history.", "et": "Sisesta e-post vestlusajaloo salvestamiseks."},
    "chat_sign_in": {"en": "Sign In", "et": "Logi sisse"},
    "chat_sign_out": {"en": "Sign Out", "et": "Logi välja"},
    "chat_cancel": {"en": "Cancel", "et": "Tühista"},
    "chat_artifacts_title": {"en": "Sources & Results", "et": "Allikad ja tulemused"},
    "chat_artifacts_subtitle": {"en": "Official links, tables, and charts", "et": "Ametlikud lingid, tabelid ja graafikud"},

    # -- JS strings --
    "js_thinking": {"en": "Thinking", "et": "Mõtleb"},
    "js_calling": {"en": "Searching", "et": "Otsib"},
    "js_copy_csv": {"en": "Copy CSV", "et": "Kopeeri CSV"},
    "js_copied": {"en": "Copied!", "et": "Kopeeritud!"},
}

# -- Agent translations --
AGENT_TRANSLATIONS: dict[str, dict[str, dict[str, str]]] = {
    "eresidency": {
        "name": {"en": "e-Residency & Company", "et": "e-residentsus ja ettevõte"},
        "one_liner": {
            "en": "Apply for e-Residency and start or run an EU company from anywhere.",
            "et": "Taotle e-residentsust ning asuta või juhi EL-i ettevõtet kõikjalt.",
        },
    },
    "moving": {
        "name": {"en": "Living & Moving", "et": "Elamine ja kolimine"},
        "one_liner": {
            "en": "Residence permits, visas, registering your address, and settling in.",
            "et": "Elamisload, viisad, elukoha registreerimine ja sisseelamine.",
        },
    },
    "tax": {
        "name": {"en": "Taxes & Finance", "et": "Maksud ja rahandus"},
        "one_liner": {
            "en": "Income tax, VAT, and filing through the e-Tax Board.",
            "et": "Tulumaks, käibemaks ja deklareerimine e-maksuametis.",
        },
    },
    "digital": {
        "name": {"en": "Digital ID & e-Services", "et": "Digi-ID ja e-teenused"},
        "one_liner": {
            "en": "e-ID, Smart-ID, Mobiil-ID, digital signatures, and X-Road.",
            "et": "e-ID, Smart-ID, Mobiil-ID, digiallkirjad ja X-tee.",
        },
    },
    "services": {
        "name": {"en": "Public Services", "et": "Avalikud teenused"},
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
    "business": {"name": {"en": "e-Residency & Business", "et": "e-residentsus ja ettevõtlus"}},
    "living": {"name": {"en": "Living in Estonia", "et": "Elamine Eestis"}},
    "digital": {"name": {"en": "Digital Society", "et": "Digiühiskond"}},
    "discover": {"name": {"en": "Discover Estonia", "et": "Avasta Eesti"}},
}
