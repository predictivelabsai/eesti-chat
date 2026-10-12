"""Official API directory for the homepage; links checked 2026-10-02."""
from fasthtml.common import A, Article, Button, Code, Div, H2, H3, Li, NotStr, P, Pre, Script, Section, Span, Ul
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


T_OFFICIAL = ("Official government APIs", "Riiklikud API-d")

MCP_ENDPOINT = "https://mcp.eesti.chat/mcp"

MCP_SNIPPETS = (
    ("claude", "Claude Desktop", "claude_desktop_config.json",
     '{\n  "mcpServers": {\n    "eesti-gov": {\n      "command": "npx",\n'
     '      "args": ["-y", "mcp-remote", "https://mcp.eesti.chat/mcp"]\n    }\n  }\n}'),
    ("cursor", "Cursor", "~/.cursor/mcp.json",
     '{\n  "mcpServers": {\n    "eesti-gov": {\n      "url": "https://mcp.eesti.chat/mcp"\n    }\n  }\n}'),
    ("curl", "curl", "List the tools",
     "curl https://mcp.eesti.chat/mcp \\\n"
     "  -H 'Content-Type: application/json' \\\n"
     "  -H 'Accept: application/json, text/event-stream' \\\n"
     "  -d '{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"tools/list\"}'"),
)

# (group en, group et, [(tool, description en, description et)])
MCP_TOOLS = (
    ("Companies & tax", "Ettevõtted ja maksud", (
        ("company_search", "Find companies in the e-Business Register", "Otsi ettevõtteid äriregistrist"),
        ("company_details", "Legal form, status, VAT number, address", "Õiguslik vorm, staatus, KMKR, aadress"),
        ("company_tax_data", "EMTA quarterly taxes, turnover, employees", "EMTA kvartali maksud, käive, töötajad"),
        ("procurement_search", "Public procurement notices (RHR)", "Riigihangete teated (RHR)"),
    )),
    ("Law & places", "Õigus ja asukohad", (
        ("law_search", "Search legislation in Riigi Teataja", "Otsi õigusakte Riigi Teatajast"),
        ("address_lookup", "Official In-ADS addresses and coordinates", "Ametlikud In-ADS aadressid ja koordinaadid"),
        ("weather_now", "Live weather station observations", "Ilmajaamade värsked vaatlused"),
        ("weather_forecast", "4-day national forecast", "4 päeva ilmaprognoos"),
    )),
    ("Statistics & more", "Statistika ja muu", (
        ("stat_search", "Find Statistics Estonia tables", "Otsi Statistikaameti tabeleid"),
        ("stat_table_meta / stat_query", "Read table variables and query data", "Tabeli muutujad ja andmepäringud"),
        ("exchange_rate", "ECB / Eesti Pank euro reference rates", "EKP / Eesti Panga euro kursid"),
        ("word_lookup", "Estonian dictionary (EKI Sõnaveeb)", "Eesti sõnaraamat (EKI Sõnaveeb)"),
        ("open_data_search", "Datasets on andmed.eesti.ee", "Andmestikud portaalis andmed.eesti.ee"),
        ("gov_web_search", "Search official .ee websites", "Otsing ametlikelt .ee veebilehtedelt"),
    )),
)

COPY_JS = """
document.addEventListener('click', function (e) {
  var btn = e.target.closest('[data-copy-target]');
  if (!btn) return;
  var el = document.getElementById(btn.getAttribute('data-copy-target'));
  if (!el || !navigator.clipboard) return;
  navigator.clipboard.writeText(el.innerText).then(function () {
    var label = btn.querySelector('.mcp-copy-label');
    var prev = label.textContent;
    label.textContent = btn.getAttribute('data-copied');
    setTimeout(function () { label.textContent = prev; }, 1600);
  });
});
"""


def _copy_button(target, lang):
    et = lang == "et"
    return Button(Icon("copy", 14), Span("Kopeeri" if et else "Copy", cls="mcp-copy-label"),
                  type="button", cls="mcp-copy", data_copy_target=target,
                  data_copied="Kopeeritud" if et else "Copied",
                  aria_label=("Kopeeri" if et else "Copy") + " " + target.replace("-", " "))


def mcp_block(lang="en"):
    et = lang == "et"
    T = (lambda en, est: est if et else en)
    snippets = [
        Div(
            Div(Span(title, cls="mcp-snippet-title"), Span(sub, cls="mcp-snippet-sub"),
                _copy_button(f"mcp-snippet-{key}", lang), cls="mcp-snippet-head"),
            Pre(Code(code, id=f"mcp-snippet-{key}"), cls="mcp-code"),
            cls="mcp-snippet",
        ) for key, title, sub, code in MCP_SNIPPETS
    ]
    tools = [
        Div(H3(g_et if et else g_en, cls="mcp-tool-group"),
            Ul(*[Li(Code(name, cls="mcp-tool-name"), Span(d_et if et else d_en, cls="mcp-tool-desc"),
                    cls="mcp-tool") for name, d_en, d_et in items], cls="mcp-tool-list"))
        for g_en, g_et, items in MCP_TOOLS
    ]
    return Div(
        Div(
            Span("MCP", cls="developer-api-type"),
            H3(T("Estonia’s public data, inside your AI agent",
                 "Eesti avalikud andmed otse sinu tehisintellekti agendis"), cls="mcp-hero-title"),
            P(T("eesti.chat runs a free Model Context Protocol server. Connect Claude, Cursor or any MCP client "
                "and your agent can look up companies, laws, addresses, statistics, procurements and more from "
                "official Estonian sources. Every answer comes with its source URL, licence and timestamp.",
                "eesti.chat pakub tasuta Model Context Protocoli serverit. Ühenda Claude, Cursor või muu MCP klient "
                "ning agent saab otsida ettevõtteid, õigusakte, aadresse, statistikat, riigihankeid ja muud "
                "ametlikest Eesti allikatest. Iga vastusega tuleb allika URL, litsents ja ajatempel."),
              cls="mcp-hero-copy"),
            Div(Span(T("Endpoint", "Otspunkt"), cls="mcp-endpoint-label"),
                Code(MCP_ENDPOINT, id="mcp-endpoint", cls="mcp-endpoint-url"),
                _copy_button("mcp-endpoint", lang), cls="mcp-endpoint"),
            P(T("Streamable HTTP · read-only tools · no sign-up needed",
                "Streamable HTTP · ainult lugemiseks · registreerumist pole vaja"), cls="mcp-endpoint-meta"),
            cls="mcp-hero",
        ),
        Div(*snippets, cls="mcp-snippets"),
        Div(
            Div(H3(T("15 tools, all from official sources", "15 tööriista, kõik ametlikest allikatest"),
                   cls="mcp-subtitle"),
                Div(*tools, cls="mcp-tool-grid"), cls="mcp-tools"),
            Div(
                H3(T("Rate limits & API keys", "Päringupiirangud ja API võtmed"), cls="mcp-subtitle"),
                Ul(
                    Li(Span(T("Anonymous", "Anonüümne"), cls="mcp-limit-tier"),
                       Span(T("30 requests / minute · 500 / day per IP", "30 päringut minutis · 500 päevas IP kohta"),
                            cls="mcp-limit-value")),
                    Li(Span(T("With API key", "API võtmega"), cls="mcp-limit-tier"),
                       Span(T("300 requests / minute · 20,000 / day", "300 päringut minutis · 20 000 päevas"),
                            cls="mcp-limit-value")),
                    cls="mcp-limits"),
                P(T("Send your key as ", "Saada võti päises "), Code("Authorization: Bearer <key>"),
                  T(". Need higher limits? ", ". Vajad suuremaid piiranguid? "),
                  A(T("Ask for a key", "Küsi võtit"), href="/contact", cls="mcp-inline-link"), ".",
                  cls="mcp-limits-note"),
                cls="mcp-limits-card"),
            cls="mcp-bottom",
        ),
        Script(NotStr(COPY_JS)),
        cls="mcp-block",
    )


def developers_section(lang="en"):
    et = lang == "et"
    return Section(
        Div(
            Span(t("nav_developers", lang), cls="section-label-blue"),
            H2(t("developers_title", lang), id="developers-title", cls="section-title"),
            mcp_block(lang),
            H3(T_OFFICIAL[1] if et else T_OFFICIAL[0], cls="mcp-subtitle developers-official-title"),
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
