"""MCP server tests against recorded upstream fixtures (no network)."""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest
import respx

FX = Path(__file__).parent / "mcp_fixtures"
ENVELOPE_KEYS = {"source_name", "source_url", "licence", "retrieved_at", "cached", "data"}


@pytest.fixture(autouse=True)
def _isolated(tmp_path, monkeypatch):
    monkeypatch.setenv("MCP_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("MCP_BULK_AUTOLOAD", "0")
    from mcp_server import config, core
    config.mcp_settings.cache_clear()
    core.cache_clear()
    core._limiters.clear()
    core._client = None
    yield
    config.mcp_settings.cache_clear()


def _env_ok(r: dict):
    assert ENVELOPE_KEYS <= set(r), r.keys()
    assert r["source_url"].startswith("http")
    assert r["retrieved_at"]


def fx(name):
    return (FX / name).read_bytes()


@respx.mock
async def test_company_search_and_cache():
    from mcp_server import sources
    route = respx.get(url__startswith="https://ariregister.rik.ee/est/api/autocomplete").mock(
        return_value=httpx.Response(200, content=fx("rik.json")))
    r = await sources.company_search("bolt", 3)
    _env_ok(r)
    assert r["data"][0]["reg_code"] == "17449106" and r["data"][0]["status"] == "registered"
    assert len(r["data"]) == 3 and r["cached"] is False
    r2 = await sources.company_search("Bolt", 3)
    assert r2["cached"] is True and route.call_count == 1


async def test_bulk_rik_and_company_details():
    from mcp_server import bulk, sources
    con = bulk.connect()
    assert bulk.load_rik(con, FX / "rik_lihtandmed.csv.zip") == 2
    con.close()
    r = await sources.company_details("11694365")
    _env_ok(r)
    d = r["data"]
    assert d["name"] == "007 Autohaus osaühing" and d["vat_no"] == "EE101335276"
    assert d["legal_form"] == "Osaühing" and "Tartu" in d["address"]
    with pytest.raises(ValueError):
        await sources.company_details("123")


@respx.mock
async def test_company_details_fallback_to_autocomplete():
    from mcp_server import sources
    respx.get(url__startswith="https://ariregister.rik.ee/est/api/autocomplete").mock(
        return_value=httpx.Response(200, content=fx("rik.json")))
    r = await sources.company_details("16469147")
    assert r["data"]["name"].startswith("Bolt Fleet") and "fallback" in r["method"]


async def test_bulk_emta_tax_data():
    from mcp_server import bulk, sources
    con = bulk.connect()
    assert bulk.load_emta(con, FX / "emta.csv", url="https://example/emta.csv") == 3
    con.close()
    r = await sources.company_tax_data("10000018")
    _env_ok(r)
    y = [x for x in r["data"] if x["year"] == 2025][0]
    assert y["year"] == 2025 and y["quarters"][0]["employees"] == 254
    assert y["quarters"][0]["turnover_eur"] == 34309154


def test_emta_link_scrape():
    from mcp_server.bulk import emta_csv_url
    html = '<a href="https://ncfailid.emta.ee/s/X/download/tasutud_maksud_kaesolev_aasta.csv">csv</a>'
    assert emta_csv_url(html).endswith("tasutud_maksud_kaesolev_aasta.csv")


async def test_bulk_rhr_and_search():
    from mcp_server import bulk, sources
    con = bulk.connect()
    assert bulk.load_rhr(con, files={"2026-09": FX / "rhr.xml"}) == 2
    con.close()
    r = await sources.procurement_search(limit=5)
    _env_ok(r)
    first = [n for n in r["data"] if n["title"] == "Kontrapulsaator"][0]
    assert first["buyer_reg_code"] == "90006399" and first["value_eur"] == 350000.0
    assert first["deadline"] == "2026-09-30" and first["cpv"] == "33182000"
    assert first["url"].startswith("https://riigihanked.riik.ee/rhr-web/")
    r = await sources.procurement_search(buyer_reg_code="90006399")
    assert all(n["buyer_reg_code"] == "90006399" for n in r["data"])


@respx.mock
async def test_law_search():
    from mcp_server import sources
    respx.get(url__startswith="https://www.riigiteataja.ee/api/oigusakt_otsing").mock(
        return_value=httpx.Response(200, content=fx("rt.json")))
    r = await sources.law_search("tulumaks", limit=2)
    _env_ok(r)
    assert r["data"]["total"] == 555
    assert r["data"]["acts"][0]["url"] == "https://www.riigiteataja.ee/akt/105072017023"
    with pytest.raises(ValueError):
        await sources.law_search("x", in_force_on="today")


@respx.mock
async def test_address_lookup():
    from mcp_server import sources
    respx.get(url__startswith="https://inaadress.maaamet.ee/").mock(
        return_value=httpx.Response(200, content=fx("ads.json")))
    r = await sources.address_lookup("Vabaduse väljak 7 Tallinn", 1)
    _env_ok(r)
    a = r["data"][0]
    assert a["ads_oid"] == "ME00638994" and a["municipality"] == "Tallinn"
    assert 59 < a["lat"] < 60 and 24 < a["lon"] < 25


@respx.mock
async def test_stat_meta_and_query():
    from mcp_server import sources
    respx.get("https://andmed.stat.ee/api/v1/en/stat/RV021").mock(
        return_value=httpx.Response(200, content=fx("rv021_meta.json")))
    respx.post("https://andmed.stat.ee/api/v1/en/stat/RV021").mock(
        return_value=httpx.Response(200, content=fx("rv021_query.json")))
    m = await sources.stat_table_meta("rv021")
    assert m["data"]["variables"][0]["code"] == "Sugu"
    q = await sources.stat_query("RV021", {"Sugu": ["1", "2"], "Aasta": ["top:2"]})
    _env_ok(q)
    rows = q["data"]["rows"]
    assert len(rows) == 4 and {"Sex", "Year", "value"} <= set(rows[0])
    assert q["query"][1]["selection"] == {"filter": "top", "values": ["2"]}


def test_jsonstat_dict_values():
    from mcp_server.sources import parse_jsonstat2
    js = {"id": ["a"], "size": [2], "dimension": {"a": {"label": "A", "category": {"index": ["x", "y"]}}},
          "value": {"1": 5}}
    assert parse_jsonstat2(js)["rows"] == [{"A": "x", "value": None}, {"A": "y", "value": 5}]


@respx.mock
async def test_weather():
    from mcp_server import sources
    respx.get(url__startswith="https://www.ilmateenistus.ee/ilma_andmed/xml/observations").mock(
        return_value=httpx.Response(200, content=fx("obs.xml")))
    respx.get(url__startswith="https://www.ilmateenistus.ee/ilma_andmed/xml/forecast").mock(
        return_value=httpx.Response(200, content=fx("fc.xml")))
    now = await sources.weather_now("tallinn")
    _env_ok(now)
    assert now["data"]["stations"] and all("Tallinn" in s["station"] for s in now["data"]["stations"])
    fc = await sources.weather_forecast()
    assert len(fc["data"]) == 4 and fc["data"][0]["night"]["temp_min_c"] is not None


@respx.mock
async def test_exchange_rate():
    from mcp_server import sources
    respx.get("https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml").mock(
        return_value=httpx.Response(200, content=fx("ecb.xml")))
    r = await sources.exchange_rate("usd")
    _env_ok(r)
    assert r["data"]["currency"] == "USD" and r["data"]["rate"] > 0
    with pytest.raises(LookupError):
        await sources.exchange_rate("XXX")


@respx.mock
async def test_word_lookup_and_open_data():
    from mcp_server import sources
    respx.get("https://api.sonapi.ee/v2/tere").mock(return_value=httpx.Response(200, content=fx("sona.json")))
    respx.get(url__startswith="https://andmed.eesti.ee/api/datasets").mock(
        return_value=httpx.Response(200, content=fx("ava.json")))
    w = await sources.word_lookup("tere")
    _env_ok(w)
    assert "hello" in w["data"]["entries"][0]["meanings"][0]["translations"]["eng"]
    o = await sources.open_data_search("x-tee")
    _env_ok(o)
    assert o["data"]["total"] == 5724 and o["data"]["datasets"][0]["url"].startswith("https://andmed.eesti.ee/")


@respx.mock
async def test_retry_on_5xx_then_error():
    from mcp_server import core, sources
    route = respx.get("https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml").mock(
        return_value=httpx.Response(503))
    with pytest.raises(core.UpstreamError):
        await sources.exchange_rate()
    assert route.call_count == 3


async def test_mcp_protocol_lists_and_calls_tools():
    from mcp.shared.memory import create_connected_server_and_client_session
    from mcp_server.server import mcp
    async with create_connected_server_and_client_session(mcp._mcp_server) as client:
        tools = {t.name for t in (await client.list_tools()).tools}
        assert {"company_search", "company_details", "company_tax_data", "law_search", "address_lookup",
                "stat_search", "stat_query", "procurement_search", "weather_now", "exchange_rate",
                "word_lookup", "open_data_search", "gov_web_search"} <= tools
        with respx.mock:
            respx.get("https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml").mock(
                return_value=httpx.Response(200, content=fx("ecb.xml")))
            res = await client.call_tool("exchange_rate", {"currency": "GBP"})
        assert not res.isError
        assert res.structuredContent["data"]["currency"] == "GBP"
        assert res.structuredContent["licence"]


def _http_client(monkeypatch, **env):
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    from mcp_server import config
    config.mcp_settings.cache_clear()
    from starlette.testclient import TestClient
    from mcp_server.server import http_app
    return TestClient(http_app())


INIT = {"jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                   "clientInfo": {"name": "t", "version": "0"}}}
HDRS = {"accept": "application/json, text/event-stream", "content-type": "application/json"}


def test_http_health_auth_and_rate_limit(monkeypatch):
    from mcp_server.auth import hash_key
    with _http_client(monkeypatch, MCP_ANON_RPM="2", MCP_API_KEY_HASHES=hash_key("ek_good")) as c:
        h = c.get("/health")
        assert h.status_code == 200 and h.json()["status"] == "ok"
        assert c.post("/mcp", json=INIT, headers=HDRS).status_code == 200
        assert c.post("/mcp", json=INIT, headers=HDRS).status_code == 200
        r = c.post("/mcp", json=INIT, headers=HDRS)
        assert r.status_code == 429 and "retry-after" in r.headers
        assert c.post("/mcp", json=INIT, headers={**HDRS, "authorization": "Bearer ek_bad"}).status_code == 401
        ok = c.post("/mcp", json=INIT, headers={**HDRS, "x-api-key": "ek_good"})
        assert ok.status_code == 200 and ok.json()["result"]["serverInfo"]["name"] == "eesti-gov"
        # health is never rate limited
        assert c.get("/health").status_code == 200


# ---------- live smoke test (network) ----------

@pytest.mark.parametrize("tool,args", [
    ("company_search", {"query": "bolt", "limit": 2}),
    ("law_search", {"query": "tulumaksuseadus", "limit": 2}),
    ("address_lookup", {"address": "Vabaduse väljak 7 Tallinn", "limit": 1}),
    ("stat_search", {"query": "population", "limit": 2}),
    ("stat_query", {"table_id": "RV021", "filters": {"Sugu": ["1"], "Aasta": ["top:1"]}}),
    ("weather_now", {"station": "Tallinn"}),
    ("weather_forecast", {}),
    ("exchange_rate", {"currency": "USD"}),
    ("word_lookup", {"word": "tere"}),
    ("open_data_search", {"query": "ilm", "limit": 2}),
])
async def test_live_smoke(request, tool, args):
    if not request.config.getoption("--run-integration", default=False):
        pytest.skip("pass --run-integration to run live upstream checks")
    from mcp_server import sources
    r = await getattr(sources, tool)(**args)
    _env_ok(r)
    assert r["data"], f"{tool} returned no data"
