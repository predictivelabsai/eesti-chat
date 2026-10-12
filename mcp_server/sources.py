"""Tool implementations, one async function per MCP tool.

Every function returns an envelope: {source_name, source_url, licence, retrieved_at, cached, data}.
Parsers are separate pure functions so tests can run them on recorded fixtures.
"""

from __future__ import annotations

import asyncio
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from urllib.parse import quote, urlencode

from mcp_server import bulk
from mcp_server.config import mcp_settings
from mcp_server.core import UpstreamError, cached, envelope, fetch

RIK_STATUS = {"R": "registered", "L": "in liquidation", "N": "bankrupt", "K": "deleted"}
RIK_LEGAL_FORM = {"1": "Füüsilisest isikust ettevõtja", "2": "Täisühing", "3": "Usaldusühing",
                  "4": "Osaühing", "5": "Aktsiaselts", "6": "Tulundusühistu", "7": "Mittetulundusühing",
                  "8": "Sihtasutus", "9": "Euroopa äriühing"}


def _clamp(n: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, int(n)))


# ---------------- Business register ----------------

def parse_rik_autocomplete(payload: dict) -> list[dict]:
    out = []
    for c in payload.get("data") or []:
        out.append({
            "reg_code": str(c.get("reg_code")),
            "name": c.get("name"),
            "status": RIK_STATUS.get(c.get("status"), c.get("status")),
            "legal_form_code": c.get("legal_form"),
            "address": c.get("legal_address"),
            "zip": c.get("zip_code"),
            "historical_names": c.get("historical_names") or [],
            "url": c.get("url"),
        })
    return out


async def company_search(query: str, limit: int = 10) -> dict:
    query = query.strip()
    if len(query) < 2:
        raise ValueError("query must be at least 2 characters")
    limit = _clamp(limit, 1, 25)
    url = f"https://ariregister.rik.ee/est/api/autocomplete?q={quote(query)}"

    async def run():
        r = await fetch("rik", "GET", url)
        return envelope("rik", url, parse_rik_autocomplete(r.json())[:limit])
    return await cached(("company_search", query.lower(), limit), 24 * 3600, run)


def _company_from_row(row) -> dict:
    d = dict(row)
    return {
        "reg_code": d["reg_code"], "name": d["name"], "legal_form": d["legal_form"],
        "legal_form_subtype": d["legal_form_sub"] or None, "vat_no": d["vat_no"] or None,
        "status": d["status_text"], "status_code": d["status"], "registered": d["registered"],
        "address": d["full_address"] or d["address"], "zip": d["zip"] or None,
        "ehak_code": d["ehak_code"] or None, "ads_oid": d["ads_oid"] or None,
        "url": d["url"] or f"https://ariregister.rik.ee/est/company/{d['reg_code']}",
    }


async def company_details(reg_code: str) -> dict:
    reg_code = re.sub(r"\D", "", reg_code)
    if len(reg_code) != 8:
        raise ValueError("reg_code must be an 8-digit Estonian registry code")
    con = bulk.connect()
    try:
        m = bulk.meta(con, "rik")
        row = con.execute("SELECT * FROM company WHERE reg_code=?", (reg_code,)).fetchone() if m else None
    finally:
        con.close()
    if row is not None:
        loaded = datetime.fromtimestamp(m["loaded_at"], timezone.utc).replace(microsecond=0).isoformat()
        return envelope("rik", bulk.RIK_CSV_URL, _company_from_row(row), retrieved_at=loaded,
                        method="open-data dump (daily)")
    # Fallback: autocomplete by registry code (less detail, always available).
    res = await company_search(reg_code, 5)
    match = [c for c in res["data"] if c["reg_code"] == reg_code]
    if not match:
        raise LookupError(f"no company with registry code {reg_code}")
    return {**res, "data": match[0], "method": "autocomplete fallback (bulk dump not loaded)"}


async def company_tax_data(reg_code: str) -> dict:
    reg_code = re.sub(r"\D", "", reg_code)
    con = bulk.connect()
    try:
        m = bulk.meta(con, "emta")
        rows = con.execute("SELECT * FROM emta_tax WHERE reg_code=? ORDER BY year DESC",
                           (reg_code,)).fetchall() if m else []
    finally:
        con.close()
    if not m:
        raise UpstreamError("EMTA open data not loaded yet on this server; try again later")
    loaded = datetime.fromtimestamp(m["loaded_at"], timezone.utc).replace(microsecond=0).isoformat()
    data = [{"year": r["year"], "name": r["name"], "kind": r["kind"], "county": r["county"],
             "activity": r["activity"], "data_as_of": r["as_of"], "quarters": json.loads(r["q"])}
            for r in rows]
    return envelope("emta", m["source_url"], data, retrieved_at=loaded,
                    note="Quarterly state taxes, labour taxes, taxable turnover and employee count "
                         "published by EMTA. Empty list = no data published for this code.")


# ---------------- Riigi Teataja ----------------

def parse_rt_search(payload: dict) -> dict:
    acts = []
    for a in payload.get("aktid") or []:
        gid = a.get("globaalID")
        acts.append({
            "act_id": str(gid), "title": a.get("pealkiri"), "abbreviation": a.get("lyhend"),
            "type": a.get("liik"), "issuer": a.get("valjaandja"),
            "in_force_from": (a.get("kehtivus") or {}).get("algus"),
            "in_force_until": (a.get("kehtivus") or {}).get("lopp"),
            "text_type": a.get("tekst"),
            "url": f"https://www.riigiteataja.ee/akt/{gid}",
        })
    return {"total": (payload.get("metaandmed") or {}).get("kokku"), "acts": acts}


async def law_search(query: str, in_force_on: str | None = None, limit: int = 10) -> dict:
    limit = _clamp(limit, 1, 50)
    params = {"leht": 1, "limiit": limit, "pealkiri": query.strip()}
    if in_force_on:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", in_force_on):
            raise ValueError("in_force_on must be YYYY-MM-DD")
        params["kehtiv"] = in_force_on
    url = "https://www.riigiteataja.ee/api/oigusakt_otsing/1/otsi?" + urlencode(params)

    async def run():
        r = await fetch("riigiteataja", "GET", url, headers={"Accept": "application/json"})
        payload = r.json()
        if payload.get("staatus") != "OK":
            raise UpstreamError(f"Riigi Teataja error: {payload.get('vead')}")
        return envelope("riigiteataja", url, parse_rt_search(payload))
    return await cached(("law_search", params), 24 * 3600, run)


# ---------------- In-ADS address ----------------

def parse_inads(payload: dict) -> list[dict]:
    out = []
    for a in payload.get("addresses") or []:
        def f(k):
            v = a.get(k)
            return float(v) if v not in (None, "") else None
        out.append({
            "full_address": a.get("taisaadress") or a.get("pikkaadress"),
            "short_address": a.get("aadresstekst"),
            "county": a.get("maakond"), "municipality": a.get("omavalitsus"),
            "settlement": a.get("asustusyksus"), "postcode": a.get("sihtnumber") or None,
            "object_type": a.get("liikVal"), "ads_oid": a.get("ads_oid"), "adr_id": a.get("adr_id"),
            "ehak_code": a.get("ehak"), "cadastral_or_building_id": a.get("tunnus") or None,
            "lat": f("viitepunkt_b"), "lon": f("viitepunkt_l"),
            "l_est97_x": f("viitepunkt_x"), "l_est97_y": f("viitepunkt_y"),
        })
    return out


async def address_lookup(address: str, limit: int = 5) -> dict:
    limit = _clamp(limit, 1, 20)
    url = ("https://inaadress.maaamet.ee/inaadress/gazetteer?"
           + urlencode({"address": address.strip(), "results": limit}))

    async def run():
        r = await fetch("inads", "GET", url)
        return envelope("inads", url, parse_inads(r.json()))
    return await cached(("address", address.strip().lower(), limit), 30 * 24 * 3600, run)


# ---------------- Statistics Estonia ----------------

STAT_BASE = "https://andmed.stat.ee/api/v1"
STAT_DBS = ["keskkond", "majandus", "rahvastik", "sotsiaalelu", "eri-valdkondade-statistika", "rahvaloendus"]


async def stat_search(query: str, lang: str = "en", limit: int = 10) -> dict:
    lang = "et" if lang == "et" else "en"
    limit = _clamp(limit, 1, 30)

    async def run():
        async def one(db):
            u = f"{STAT_BASE}/{lang}/stat/{db}?" + urlencode({"query": query})
            try:
                r = await fetch("stat", "GET", u, retries=1)
                data = r.json()
                return [{**x, "database": db} for x in data if isinstance(x, dict) and x.get("id")] if isinstance(data, list) else []
            except (UpstreamError, ValueError):
                return []
        res = [x for chunk in await asyncio.gather(*(one(d) for d in STAT_DBS)) for x in chunk]
        res.sort(key=lambda x: -(x.get("score") or 0))
        seen, out = set(), []
        for x in res:
            tid = x["id"].removesuffix(".PX")
            if tid in seen:
                continue
            seen.add(tid)
            out.append({"table_id": tid, "title": x.get("title"), "published": x.get("published"),
                        "score": x.get("score"), "path": f"{x['database']}{x.get('path','')}"})
        return envelope("stat", f"{STAT_BASE}/{lang}/stat?query={quote(query)}", out[:limit])
    return await cached(("stat_search", query.lower(), lang, limit), 24 * 3600, run)


async def stat_table_meta(table_id: str, lang: str = "en") -> dict:
    lang = "et" if lang == "et" else "en"
    tid = re.sub(r"[^A-Za-z0-9_]", "", table_id).upper()
    url = f"{STAT_BASE}/{lang}/stat/{tid}"

    async def run():
        r = await fetch("stat", "GET", url)
        p = r.json()
        vars_ = [{"code": v["code"], "label": v.get("text"),
                  "values": [{"code": c, "label": t} for c, t in zip(v.get("values", []), v.get("valueTexts", []))][:400],
                  "value_count": len(v.get("values", [])), "time": v.get("time", False),
                  "can_omit": v.get("elimination", False)} for v in p.get("variables", [])]
        return envelope("stat", url, {"table_id": tid, "title": p.get("title"), "variables": vars_})
    return await cached(("stat_meta", tid, lang), 7 * 24 * 3600, run)


def parse_jsonstat2(js: dict, max_rows: int = 500) -> dict:
    ids = js["id"]
    sizes = js["size"]
    dims = js["dimension"]
    cats = []
    for d in ids:
        idx = dims[d]["category"]["index"]
        order = sorted(idx, key=idx.get) if isinstance(idx, dict) else list(idx)
        labels = dims[d]["category"].get("label", {})
        cats.append([(c, labels.get(c, c)) for c in order])
    values = js.get("value") or []
    if isinstance(values, dict):
        total = 1
        for s in sizes:
            total *= s
        values = [values.get(str(i)) for i in range(total)]
    rows = []
    for i, v in enumerate(values[:max_rows]):
        rem, row = i, {}
        for d, s, cs in reversed(list(zip(ids, sizes, cats))):
            row[dims[d].get("label", d)] = cs[rem % s][1]
            rem //= s
        rows.append({**dict(reversed(list(row.items()))), "value": v})
    return {"title": js.get("label"), "updated": js.get("updated"),
            "rows": rows, "total_cells": len(values), "truncated": len(values) > max_rows}


async def stat_query(table_id: str, filters: dict[str, list[str]], lang: str = "en") -> dict:
    """filters: {variable_code: [value codes]}; use ["*"] for all values, "top:N" for the last N."""
    lang = "et" if lang == "et" else "en"
    tid = re.sub(r"[^A-Za-z0-9_]", "", table_id).upper()
    url = f"{STAT_BASE}/{lang}/stat/{tid}"
    query = []
    for code, vals in (filters or {}).items():
        vals = [vals] if isinstance(vals, str) else list(vals)
        if vals == ["*"]:
            query.append({"code": code, "selection": {"filter": "all", "values": ["*"]}})
        elif len(vals) == 1 and str(vals[0]).startswith("top:"):
            query.append({"code": code, "selection": {"filter": "top", "values": [vals[0][4:]]}})
        else:
            query.append({"code": code, "selection": {"filter": "item", "values": [str(v) for v in vals]}})
    body = {"query": query, "response": {"format": "json-stat2"}}

    async def run():
        r = await fetch("stat", "POST", url, json=body)
        return envelope("stat", url, {"table_id": tid, **parse_jsonstat2(r.json())}, query=body["query"])
    return await cached(("stat_query", tid, lang, body), 24 * 3600, run)


# ---------------- Procurement ----------------

async def procurement_search(query: str | None = None, buyer_reg_code: str | None = None,
                             cpv_prefix: str | None = None, from_date: str | None = None,
                             limit: int = 20) -> dict:
    limit = _clamp(limit, 1, 100)
    con = bulk.connect()
    try:
        m = bulk.meta(con, "rhr")
        if not m:
            raise UpstreamError("RHR open data not loaded yet on this server; try again later")
        where, args = [], []
        if query:
            where.append("(title LIKE ? OR description LIKE ? OR buyer_name LIKE ?)")
            args += [f"%{query}%"] * 3
        if buyer_reg_code:
            where.append("buyer_reg_code=?"); args.append(re.sub(r"\D", "", buyer_reg_code))
        if cpv_prefix:
            where.append("cpv LIKE ?"); args.append(re.sub(r"\D", "", cpv_prefix) + "%")
        if from_date:
            where.append("issue_date>=?"); args.append(from_date)
        sql = "SELECT * FROM rhr_notice" + (" WHERE " + " AND ".join(where) if where else "") + \
              " ORDER BY issue_date DESC LIMIT ?"
        rows = [dict(r) for r in con.execute(sql, args + [limit])]
        months = [r[0] for r in con.execute("SELECT DISTINCT month FROM rhr_notice ORDER BY month")]
    finally:
        con.close()
    loaded = datetime.fromtimestamp(m["loaded_at"], timezone.utc).replace(microsecond=0).isoformat()
    return envelope("rhr", "https://riigihanked.riik.ee/rhr/api/public/v1/opendata", rows,
                    retrieved_at=loaded, months_covered=months)


# ---------------- Weather ----------------

def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def parse_observations(xml_text: str | bytes) -> dict:
    root = ET.fromstring(xml_text)
    ts = root.attrib.get("timestamp")
    obs_time = datetime.fromtimestamp(int(ts), timezone.utc).isoformat() if ts else None
    stations = []
    for s in root.findall("station"):
        g = lambda k: (s.findtext(k) or "").strip() or None  # noqa: E731
        stations.append({"station": g("name"), "lat": _f(g("latitude")), "lon": _f(g("longitude")),
                         "phenomenon": g("phenomenon"), "air_temperature_c": _f(g("airtemperature")),
                         "relative_humidity_pct": _f(g("relativehumidity")),
                         "wind_speed_ms": _f(g("windspeed")), "wind_gust_ms": _f(g("windspeedmax")),
                         "wind_direction_deg": _f(g("winddirection")),
                         "precipitation_mm": _f(g("precipitations")), "pressure_hpa": _f(g("airpressure")),
                         "visibility_km": _f(g("visibility"))})
    return {"observed_at": obs_time, "stations": stations}


async def weather_now(station: str | None = None) -> dict:
    url = "https://www.ilmateenistus.ee/ilma_andmed/xml/observations.php"

    async def run():
        r = await fetch("ilm", "GET", url)
        return envelope("ilm", url, parse_observations(r.content))
    res = await cached(("weather_now",), 600, run)
    data = res["data"]
    st = data["stations"]
    if station:
        s = station.lower()
        st = [x for x in st if x["station"] and s in x["station"].lower()]
    else:
        st = [x for x in st if x["air_temperature_c"] is not None]
    return {**res, "data": {"observed_at": data["observed_at"], "stations": st}}


def parse_forecast(xml_text: str | bytes) -> list[dict]:
    root = ET.fromstring(xml_text)
    days = []
    for fc in root.findall("forecast"):
        item = {"date": fc.attrib.get("date")}
        for part in ("night", "day"):
            p = fc.find(part)
            if p is None:
                continue
            item[part] = {"phenomenon": p.findtext("phenomenon"), "temp_min_c": _f(p.findtext("tempmin")),
                          "temp_max_c": _f(p.findtext("tempmax")), "text": (p.findtext("text") or "").strip(),
                          "places": [{"name": pl.findtext("name"), "phenomenon": pl.findtext("phenomenon"),
                                      "temp_min_c": _f(pl.findtext("tempmin")), "temp_max_c": _f(pl.findtext("tempmax"))}
                                     for pl in p.findall("place")]}
        days.append(item)
    return days


async def weather_forecast(lang: str = "eng") -> dict:
    lang = lang if lang in ("eng", "est", "rus") else "eng"
    url = f"https://www.ilmateenistus.ee/ilma_andmed/xml/forecast.php?lang={lang}"

    async def run():
        r = await fetch("ilm", "GET", url)
        return envelope("ilm", url, parse_forecast(r.content))
    return await cached(("weather_forecast", lang), 1800, run)


# ---------------- ECB rates ----------------

def parse_ecb(xml_text: str | bytes) -> dict:
    root = ET.fromstring(xml_text)
    out_date, rates = None, {}
    for el in root.iter():
        if el.tag.endswith("Cube") and "time" in el.attrib:
            out_date = el.attrib["time"]
        if el.tag.endswith("Cube") and "currency" in el.attrib:
            rates[el.attrib["currency"]] = float(el.attrib["rate"])
    return {"date": out_date, "base": "EUR", "rates": rates}


async def exchange_rate(currency: str | None = None) -> dict:
    url = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml"

    async def run():
        r = await fetch("ecb", "GET", url)
        return envelope("ecb", url, parse_ecb(r.content),
                        note="Eesti Pank publishes the ECB euro reference rates (euro area member).")
    res = await cached(("ecb",), 6 * 3600, run)
    if currency:
        c = currency.upper().strip()
        rate = res["data"]["rates"].get(c)
        if rate is None:
            raise LookupError(f"no ECB reference rate for {c}")
        return {**res, "data": {"date": res["data"]["date"], "base": "EUR", "currency": c, "rate": rate}}
    return res


# ---------------- Sõnaveeb ----------------

def parse_sonaveeb(payload: dict) -> dict:
    entries = []
    for r in payload.get("searchResult") or []:
        entries.append({
            "word_classes": r.get("wordClasses") or [],
            "forms": [{"form": f.get("value"), "code": f.get("code"), "morph": f.get("morphValue")}
                      for f in (r.get("wordForms") or [])][:40],
            "meanings": [{"definition": m.get("definition"),
                          "part_of_speech": [p.get("value") for p in m.get("partOfSpeech") or []],
                          "examples": (m.get("examples") or [])[:5], "synonyms": (m.get("synonyms") or [])[:10],
                          "translations": {lng: [t.get("words") for t in ts][:5]
                                           for lng, ts in (m.get("translations") or {}).items()}}
                         for m in (r.get("meanings") or [])][:10],
        })
    return {"word": payload.get("requestedWord"), "estonian_word": payload.get("estonianWord"), "entries": entries}


async def word_lookup(word: str) -> dict:
    w = word.strip()
    if not w or len(w) > 80:
        raise ValueError("word must be 1-80 characters")
    url = f"https://api.sonapi.ee/v2/{quote(w)}"

    async def run():
        r = await fetch("sonaveeb", "GET", url)
        return envelope("sonaveeb", f"https://sonaveeb.ee/search/unif/dlall/dsall/{quote(w)}/1", parse_sonaveeb(r.json()),
                        api_url=url)
    return await cached(("word", w.lower()), 7 * 24 * 3600, run)


# ---------------- Open data portal ----------------

def parse_avaandmed(payload: dict) -> dict:
    items = [{"dataset_id": d.get("id"), "slug": d.get("slug"), "title": d.get("title"),
              "title_en": d.get("titleEn"), "updated": d.get("updatedAt"), "access": d.get("access"),
              "url": f"https://andmed.eesti.ee/datasets/{d.get('slug')}"} for d in payload.get("data") or []]
    return {"total": (payload.get("metadata") or {}).get("total"), "datasets": items}


async def open_data_search(query: str, limit: int = 10) -> dict:
    limit = _clamp(limit, 1, 50)
    url = "https://andmed.eesti.ee/api/datasets?" + urlencode({"search": query.strip(), "limit": limit, "page": 1})

    async def run():
        r = await fetch("avaandmed", "GET", url)
        return envelope("avaandmed", url, parse_avaandmed(r.json()))
    return await cached(("avaandmed", query.lower(), limit), 24 * 3600, run)


# ---------------- Exa ----------------

async def gov_web_search(query: str, max_results: int = 6, official_only: bool = True) -> dict:
    from tools.search import OFFICIAL_DOMAINS  # reuse the chat app's domain list
    key = mcp_settings().exa_api_key
    if not key:
        raise UpstreamError("web search is not configured on this server")
    payload = {"query": query, "numResults": _clamp(max_results, 1, 15), "type": "auto",
               "contents": {"text": {"maxCharacters": 1000}, "highlights": {"numSentences": 3}}}
    if official_only:
        payload["includeDomains"] = OFFICIAL_DOMAINS

    async def run():
        r = await fetch("exa", "POST", "https://api.exa.ai/search", json=payload,
                        headers={"x-api-key": key, "content-type": "application/json"}, retries=1)
        res = [{"title": x.get("title"), "url": x.get("url"), "published": x.get("publishedDate"),
                "highlights": x.get("highlights") or [], "text": (x.get("text") or "")[:1000]}
               for x in r.json().get("results", [])]
        return envelope("exa", "https://api.exa.ai/search", res)
    return await cached(("exa", query.lower(), max_results, official_only), 6 * 3600, run)


