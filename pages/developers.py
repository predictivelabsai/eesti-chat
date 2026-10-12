"""Official API directory for the homepage; links checked 2026-10-02."""
from pathlib import Path

from fasthtml.common import A, Article, Button, Code, Div, H2, H3, H4, Li, NotStr, Ol, P, Script, Section, Span, Ul
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
_CLIENT_DIR = Path(__file__).resolve().parent.parent / "static" / "brand" / "clients"


def _logo(name: str):
    try:
        return NotStr((_CLIENT_DIR / f"{name}.svg").read_text())
    except OSError:  # pragma: no cover
        return ""


def _tr(lang):
    return (lambda en, et: et if lang == "et" else en)


def _copy_btn(text: str, lang: str, label: str = ""):
    T = _tr(lang)
    return Button(Icon("copy", 14), Span(T("Copy", "Kopeeri"), cls="dev-copy-label"),
                  type="button", cls="dev-copy", data_copy=text,
                  data_copied=T("Copied", "Kopeeritud"),
                  aria_label=T("Copy", "Kopeeri") + (f" {label}" if label else ""))


def _terminal(lang, cmd: str, out: list[str] = (), title: str = "", prompt: bool = True, label: str = ""):
    """Dark terminal block. The copy button copies only `cmd` (no prompt, no output)."""
    lines = cmd.split("\n")
    rows = [Div(Span("$ " if (prompt and i == 0) else ("  " if prompt else ""), cls="dev-term-prompt"),
                Span(line, cls="dev-term-cmd"), cls="dev-term-row") for i, line in enumerate(lines)]
    rows += [Div(Span("→ ", cls="dev-term-arrow"), Span(o, cls="dev-term-out"), cls="dev-term-row")
             for o in out]
    return Div(
        Div(Div(Span(cls="dev-dot"), Span(cls="dev-dot"), Span(cls="dev-dot"), cls="dev-dots"),
            Span(title, cls="dev-term-title"), _copy_btn(cmd, lang, label or title), cls="dev-term-bar"),
        Div(*rows, cls="dev-term-body"),
        cls="dev-term",
    )


CLAUDE_CMD = "claude mcp add --transport http eesti https://mcp.eesti.chat/mcp"
CURL_CMD = ("curl -s https://mcp.eesti.chat/mcp \\\n"
            "  -H 'Content-Type: application/json' \\\n"
            "  -H 'Accept: application/json, text/event-stream' \\\n"
            "  -d '{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"tools/list\"}'")
CURSOR_JSON = '{\n  "mcpServers": {\n    "eesti": { "url": "https://mcp.eesti.chat/mcp" }\n  }\n}'
GROK_JSON = ('"tools": [{\n  "type": "mcp",\n  "server_label": "eesti",\n'
             '  "server_url": "https://mcp.eesti.chat/mcp"\n}]')

# (key, name, logo, steps en, steps et, snippet title, snippet, prompt?)
CLIENTS = (
    ("chatgpt", "ChatGPT", "chatgpt",
     ("Settings → Apps & Connectors → Advanced → turn on Developer mode.",
      "Create a connector, name it eesti.chat and paste the server URL.",
      "Choose No authentication, then Create."),
     ("Seaded → Apps & Connectors → Advanced → lülita sisse Developer mode.",
      "Loo konnektor, anna nimeks eesti.chat ja kleebi serveri URL.",
      "Vali No authentication ja seejärel Create."),
     "Server URL", MCP_ENDPOINT, False),
    ("claude", "Claude", "claude",
     ("Claude.ai or Desktop: Settings → Connectors → Add custom connector, paste the URL.",
      "Claude Code: run the command below once."),
     ("Claude.ai või Desktop: Settings → Connectors → Add custom connector, kleebi URL.",
      "Claude Code: käivita allolev käsk üks kord."),
     "Claude Code", CLAUDE_CMD, True),
    ("grok", "Grok", "grok",
     ("xAI API: add eesti.chat as a remote MCP tool in your request.",
      "Grok calls the tools server-side and returns cited answers."),
     ("xAI API: lisa eesti.chat päringusse kaug-MCP tööriistana.",
      "Grok kutsub tööriistu serveri poolel ja tagastab viidetega vastused."),
     "xAI Responses API", GROK_JSON, False),
    ("cursor", "Cursor", "cursor",
     ("Open Cursor Settings → MCP → Add new MCP server,",
      "or add this to ~/.cursor/mcp.json and reload."),
     ("Ava Cursor Settings → MCP → Add new MCP server",
      "või lisa see faili ~/.cursor/mcp.json ja laadi uuesti."),
     "~/.cursor/mcp.json", CURSOR_JSON, False),
)

MCP_TOOLS = (
    ("Companies & tax", "Ettevõtted ja maksud", (
        ("company_search", "Find companies in the e-Business Register", "Otsi ettevõtteid äriregistrist"),
        ("company_details", "Legal form, status, VAT number, address", "Õiguslik vorm, staatus, KMKR, aadress"),
        ("company_tax_data", "EMTA quarterly taxes, turnover, employees", "EMTA kvartali maksud, käive, töötajad"),
        ("procurement_search", "Public procurement notices (RHR)", "Riigihangete teated (RHR)"),
        ("law_search", "Legislation in Riigi Teataja", "Õigusaktid Riigi Teatajas"),
    )),
    ("Places & everyday", "Asukohad ja igapäev", (
        ("address_lookup", "Official In-ADS addresses and coordinates", "Ametlikud In-ADS aadressid ja koordinaadid"),
        ("weather_now", "Live weather station observations", "Ilmajaamade värsked vaatlused"),
        ("weather_forecast", "4-day national forecast", "4 päeva ilmaprognoos"),
        ("exchange_rate", "ECB / Eesti Pank euro reference rates", "EKP / Eesti Panga euro kursid"),
        ("word_lookup", "Estonian dictionary (EKI Sõnaveeb)", "Eesti sõnaraamat (EKI Sõnaveeb)"),
    )),
    ("Data & search", "Andmed ja otsing", (
        ("stat_search", "Find Statistics Estonia tables", "Otsi Statistikaameti tabeleid"),
        ("stat_table_meta", "Variables and value codes of a table", "Tabeli muutujad ja koodid"),
        ("stat_query", "Query a statistics table", "Statistikatabeli päring"),
        ("open_data_search", "Datasets on andmed.eesti.ee", "Andmestikud portaalis andmed.eesti.ee"),
        ("gov_web_search", "Search official .ee websites", "Otsing ametlikelt .ee veebilehtedelt"),
    )),
)

DEV_JS = """
(function () {
  document.addEventListener('click', function (e) {
    var btn = e.target.closest('.dev-copy');
    if (btn) {
      var text = btn.getAttribute('data-copy');
      var done = function () {
        var l = btn.querySelector('.dev-copy-label'), prev = l.textContent;
        l.textContent = btn.getAttribute('data-copied'); btn.classList.add('is-copied');
        setTimeout(function () { l.textContent = prev; btn.classList.remove('is-copied'); }, 1600);
      };
      if (navigator.clipboard && window.isSecureContext) { navigator.clipboard.writeText(text).then(done); }
      else { var t = document.createElement('textarea'); t.value = text; document.body.appendChild(t);
             t.select(); try { document.execCommand('copy'); done(); } catch (x) {} t.remove(); }
      return;
    }
    var tab = e.target.closest('.dev-client-tab');
    if (tab) {
      var root = tab.closest('.dev-clients');
      root.querySelectorAll('.dev-client-tab').forEach(function (b) {
        var on = b === tab; b.classList.toggle('is-active', on); b.setAttribute('aria-selected', on ? 'true' : 'false');
        b.tabIndex = on ? 0 : -1;
      });
      root.querySelectorAll('.dev-client-panel').forEach(function (p) {
        p.hidden = p.id !== tab.getAttribute('aria-controls');
      });
    }
  });
  document.addEventListener('keydown', function (e) {
    var tab = e.target.closest && e.target.closest('.dev-client-tab');
    if (!tab || (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft')) return;
    var tabs = Array.prototype.slice.call(tab.parentNode.querySelectorAll('.dev-client-tab'));
    var i = tabs.indexOf(tab) + (e.key === 'ArrowRight' ? 1 : -1);
    var next = tabs[(i + tabs.length) % tabs.length]; next.focus(); next.click(); e.preventDefault();
  });
})();
"""


def mcp_block(lang="en"):
    T = _tr(lang)
    et = lang == "et"
    stats = [("15", T("read-only tools", "lugemistööriista")), ("11", T("official sources", "ametlikku allikat")),
             ("0", T("sign-ups needed", "registreerumist")), ("2", T("access tiers", "juurdepääsutaset"))]

    clients = Div(
        Div(*[Button(Span(_logo(logo), cls="dev-client-logo"), Span(name),
                     type="button", role="tab", id=f"dev-tab-{key}", aria_controls=f"dev-panel-{key}",
                     aria_selected="true" if i == 0 else "false", tabindex="0" if i == 0 else "-1",
                     cls="dev-client-tab" + (" is-active" if i == 0 else ""))
              for i, (key, name, logo, *_r) in enumerate(CLIENTS)],
            role="tablist", aria_label=T("MCP clients", "MCP kliendid"), cls="dev-client-tabs"),
        *[Div(
            Ol(*[Li(x) for x in (st_et if et else st_en)], cls="dev-client-steps"),
            _terminal(lang, snippet, title=stitle, prompt=prompt, label=f"{name} {stitle}"),
            role="tabpanel", id=f"dev-panel-{key}", aria_labelledby=f"dev-tab-{key}",
            hidden=(i != 0), cls="dev-client-panel")
          for i, (key, name, logo, st_en, st_et, stitle, snippet, prompt) in enumerate(CLIENTS)],
        cls="dev-clients",
    )

    return Div(
        # Hero
        Div(
            Span(T("MCP server", "MCP server"), cls="section-label-blue"),
            H3(T("Plug Estonia’s public data into your AI agent.",
                 "Ühenda Eesti avalikud andmed oma tehisintellekti agendiga."), cls="dev-hero-title"),
            P(T("A free Model Context Protocol server for companies, laws, addresses, statistics, procurements, "
                "weather and more, straight from official Estonian sources. Every result is cited.",
                "Tasuta Model Context Protocoli server ettevõtete, õigusaktide, aadresside, statistika, riigihangete, "
                "ilma ja muu jaoks otse ametlikest Eesti allikatest. Iga tulemus on viidatud."), cls="dev-lede"),
            Div(Code(MCP_ENDPOINT, cls="dev-endpoint-url"), _copy_btn(MCP_ENDPOINT, lang, "endpoint"),
                cls="dev-endpoint"),
            Div(*[Div(Span(n, cls="dev-stat-n"), Span(l, cls="dev-stat-l"), cls="dev-stat") for n, l in stats],
                cls="dev-stats"),
            cls="dev-hero",
        ),
        # Works with
        Div(Span(T("Works with", "Töötab koos"), cls="dev-works-label"),
            Div(*[Span(Span(_logo(logo), cls="dev-client-logo"), Span(name), cls="dev-works-item")
                  for key, name, logo, *_r in CLIENTS], cls="dev-works-row"),
            cls="dev-works"),
        # Terminal 1: install
        Div(
            H3(T("Connect from your terminal.", "Ühenda terminalist."), cls="dev-h"),
            P(T("One command adds eesti.chat to Claude Code. Any client that speaks MCP over HTTP works the same way.",
                "Üks käsk lisab eesti.chati Claude Code'i. Iga MCP-d HTTP kaudu toetav klient töötab samamoodi."),
              cls="dev-p"),
            _terminal(lang, CLAUDE_CMD, [
                "Added HTTP MCP server eesti with URL: https://mcp.eesti.chat/mcp",
                T("15 tools · company_search, law_search, address_lookup, stat_query …",
                  "15 tööriista · company_search, law_search, address_lookup, stat_query …")],
                title="claude", label="Claude Code"),
            P(T("Example output, illustrative.", "Näidisväljund, illustratiivne."), cls="dev-note"),
            Div(
                Div(H4(T("How the endpoint and tool names read", "Kuidas otspunkti ja tööriistade nimesid lugeda"),
                       cls="dev-h4"),
                    P(Code("https://mcp.eesti.chat/mcp"),
                      T(" is a single streamable-HTTP endpoint; there is nothing else to configure. "
                        "Tools are named ", " on üks streamable HTTP otspunkt, muud seadistada pole vaja. "
                        "Tööriistade nimed on kujul "),
                      Code("{domain}_{action}"), T(": ", ": "), Code("company_search"), ", ",
                      Code("company_details"), ", ", Code("stat_query"),
                      T(". eesti is just the local name you give the server.",
                        ". eesti on lihtsalt kohalik nimi, mille serverile annad."), cls="dev-p"),
                    cls="dev-sub"),
                Div(H4(T("What a result contains", "Mida tulemus sisaldab"), cls="dev-h4"),
                    Ul(Li(Code("source_url"), T(" the official page or file the data came from",
                                                 " ametlik leht või fail, kust andmed pärinevad")),
                       Li(Code("licence"), T(" reuse terms, e.g. CC BY 4.0", " taaskasutuse tingimused, nt CC BY 4.0")),
                       Li(Code("retrieved_at"), T(" when it was fetched (UTC)", " millal andmed toodi (UTC)")),
                       Li(Code("cached"), T(" whether it was served from cache", " kas vastus tuli vahemälust")),
                       Li(Code("data"), T(" the result itself", " tulemus ise")), cls="dev-fields"),
                    cls="dev-sub"),
                cls="dev-subs"),
            cls="dev-step",
        ),
        # Terminal 2: curl
        Div(
            H3(T("Or call it directly.", "Või kutsu otse."), cls="dev-h"),
            P(T("It is plain JSON-RPC over HTTPS, so curl works too.",
                "See on tavaline JSON-RPC üle HTTPS-i, nii et ka curl töötab."), cls="dev-p"),
            _terminal(lang, CURL_CMD, [
                '{"jsonrpc":"2.0","id":1,"result":{"tools":[',
                '  {"name":"company_search","description":"Search the Estonian e-Business Register…"},',
                '  {"name":"law_search","description":"Search Estonian legislation in Riigi Teataja…"},',
                "  … 13 more ]}}"], title="curl", label="curl tools/list"),
            P(T("Example output, illustrative and shortened.", "Näidisväljund, illustratiivne ja lühendatud."),
              cls="dev-note"),
            cls="dev-step",
        ),
        # Clients
        Div(
            H3(T("Connect your client.", "Ühenda oma klient."), cls="dev-h"),
            clients,
            cls="dev-step",
        ),
        # Tools + limits
        Div(
            Div(H3(T("15 tools, all from official sources", "15 tööriista, kõik ametlikest allikatest"), cls="dev-h"),
                Div(*[Div(H4(g_et if et else g_en, cls="dev-tool-group"),
                          Ul(*[Li(Code(n, cls="dev-tool-name"), Span(d_et if et else d_en, cls="dev-tool-desc"),
                                  cls="dev-tool") for n, d_en, d_et in items], cls="dev-tool-list"))
                      for g_en, g_et, items in MCP_TOOLS], cls="dev-tool-grid"),
                cls="dev-card"),
            Div(H3(T("Rate limits & API keys", "Päringupiirangud ja API võtmed"), cls="dev-h"),
                Ul(Li(Span(T("Anonymous", "Anonüümne"), cls="dev-tier"),
                      Span(T("30 / minute · 500 / day per IP", "30 minutis · 500 päevas IP kohta"), cls="dev-tier-v")),
                   Li(Span(T("API key", "API võti"), cls="dev-tier"),
                      Span(T("300 / minute · 20,000 / day", "300 minutis · 20 000 päevas"), cls="dev-tier-v")),
                   cls="dev-tiers"),
                P(T("Send the key as ", "Saada võti päises "), Code("Authorization: Bearer <key>"),
                  T(". Over the limit you get 429 with Retry-After. ", ". Piirangu ületamisel tuleb 429 koos Retry-Afteriga. "),
                  A(T("Ask for a key", "Küsi võtit"), href="/contact", cls="dev-link"), ".", cls="dev-p"),
                cls="dev-card"),
            cls="dev-bottom",
        ),
        Script(NotStr(DEV_JS)),
        cls="dev-block",
    )


def developers_section(lang="en"):
    et = lang == "et"
    return Section(
        Div(
            Span(t("nav_developers", lang), cls="section-label-blue"),
            H2(t("developers_title", lang), id="developers-title", cls="section-title"),
            mcp_block(lang),
            H3(T_OFFICIAL[1] if et else T_OFFICIAL[0], cls="dev-h developers-official-title"),
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
