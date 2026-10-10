"""Official API directory for the homepage; links checked 2026-10-02."""
from fasthtml.common import A, Article, Div, H2, H3, P, Section, Span
from utils.brand import Icon
from utils.i18n import t

# English and Estonian copy; other languages use the standard English fallback.
APIS = (
    ("Statistics Estonia", "Statistikaamet", "PxWeb API",
     "Population, economy and other statistical tables in machine-readable form.",
     "Rahvastiku, majanduse ja muude valdkondade statistikatabelid masinloetaval kujul.",
     "Public data queries", "Avalikud andmepäringud",
     "https://stat.ee/en/statistikaamet/developers"),
    ("e-Business Register", "E-äriregister", "XML API",
     "Company and registry queries from the Centre of Registers and Information Systems (RIK).",
     "Ettevõtete ja registriandmete päringud Registrite ja Infosüsteemide Keskuselt (RIK).",
     "Access varies by service; some queries require a contract",
     "Juurdepääs sõltub teenusest; osa päringuid nõuab lepingut",
     "https://abiinfo.rik.ee/en/e-business-register-queries/xml-service-api"),
    ("Maps & spatial data", "Kaardid ja ruumiandmed", "WMS / WFS / WCS",
     "Map layers and geographic data from the Land and Spatial Development Board.",
     "Maa- ja Ruumiameti kaardikihid ning ruumiandmed.",
     "Public map services", "Avalikud kaarditeenused",
     "https://geoportaal.maaamet.ee/est/teenused/wms-wfs-wcs-teenused-p65.html"),
    ("Address search & geocoding", "Aadressiotsing ja geokodeerimine", "In-ADS",
     "Find Estonian addresses and explore address normalisation and geocoding services.",
     "Otsi Eesti aadresse ning tutvu aadresside normaliseerimise ja geokodeerimise teenustega.",
     "See service-specific integration guidance", "Vaata teenuse liidestamise juhiseid",
     "https://geoportaal.maaamet.ee/eng/services-p40.html"),
    ("Land cadastre", "Maakataster", "REST API",
     "Cadastral parcel information and change logs through the land operations platform.",
     "Katastriüksuste andmed ja muudatuste logid maatoimingute platvormi kaudu.",
     "Public API endpoints; additional X-tee services have access conditions",
     "Avalikud API otspunktid; täiendavatel X-tee teenustel on juurdepääsutingimused",
     "https://kataster.ee/avaandmed/x-teeapi-teenused"),
    ("X-tee data exchange", "X-tee andmevahetus", "REST / SOAP",
     "Connect to Estonia’s data exchange ecosystem and participating agencies’ services.",
     "Liitu Eesti andmevahetuskeskkonnaga ja kasuta liitunud asutuste teenuseid.",
     "Membership, security server and service agreements required",
     "Vajalikud on liikmelisus, turvaserver ja teenusekokkulepped",
     "https://www.ria.ee/en/state-information-system/data-exchange-platforms/data-exchange-layer-x-tee"),
)


def developers_section(lang="en"):
    et = lang == "et"
    return Section(
        Div(
            Span(t("nav_developers", lang), cls="section-label-blue"),
            H2(t("developers_title", lang), id="developers-title", cls="section-title"),
            P(t("developers_intro", lang), cls="developers-intro"),
            Div(*[
                Article(
                    Span(protocol, cls="developer-api-type"),
                    H3(name_et if et else name, cls="agent-card-title"),
                    P(desc_et if et else desc, cls="agent-card-copy"),
                    P(access_et if et else access, cls="developer-api-access"),
                    A(Span(t("developers_docs", lang)), Icon("arrow-right", 16),
                      href=url, target="_blank", rel="noopener noreferrer",
                      aria_label=f'{t("developers_docs", lang)}: {name_et if et else name}',
                      cls="editorial-link"),
                    cls="developer-api-card",
                ) for name, name_et, protocol, desc, desc_et, access, access_et, url in APIS
            ], cls="agent-grid"),
            cls="portal-container",
        ), id="developers", aria_labelledby="developers-title",
        cls="public-section public-section-alt scroll-mt-16",
    )
