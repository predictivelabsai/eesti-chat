"""Bulk open-data loaders (RIK company dump, EMTA tax data, RHR notices) into SQLite.

These sources ship as large daily/quarterly/monthly files, so we mirror them locally
instead of hitting the upstream per query. Run manually with:

    python -m mcp_server.bulk [rik|emta|rhr|all]
"""

from __future__ import annotations

import csv
import io
import json
import logging
import os
import re
import sqlite3
import sys
import tempfile
import threading
import time
import xml.etree.ElementTree as ET
import zipfile
from datetime import date
from pathlib import Path

import httpx

from mcp_server.config import mcp_settings

log = logging.getLogger(__name__)

RIK_CSV_URL = ("https://avaandmed.ariregister.rik.ee/sites/default/files/avaandmed/"
               "ettevotja_rekvisiidid__lihtandmed.csv.zip")
EMTA_PAGE_URL = ("https://www.emta.ee/eraklient/amet-uudised-ja-kontakt/uudised-pressiinfo-statistika/"
                 "statistika-ja-avaandmed")
RHR_MONTH_URL = "https://riigihanked.riik.ee/rhr/api/public/v1/opendata/notice/{y}/month/{m}/xml"

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (source TEXT PRIMARY KEY, loaded_at REAL, source_url TEXT, rows INTEGER);
CREATE TABLE IF NOT EXISTS company (
  reg_code TEXT PRIMARY KEY, name TEXT, legal_form TEXT, legal_form_sub TEXT, vat_no TEXT,
  status TEXT, status_text TEXT, registered TEXT, address TEXT, ehak_code TEXT, ehak_text TEXT,
  zip TEXT, ads_adr_id TEXT, ads_oid TEXT, full_address TEXT, url TEXT);
CREATE INDEX IF NOT EXISTS company_name ON company(name COLLATE NOCASE);
CREATE TABLE IF NOT EXISTS emta_tax (
  reg_code TEXT, year INTEGER, name TEXT, kind TEXT, county TEXT, activity TEXT, as_of TEXT,
  q TEXT, PRIMARY KEY (reg_code, year));
CREATE TABLE IF NOT EXISTS rhr_notice (
  notice_id TEXT PRIMARY KEY, procurement_ref TEXT, notice_type TEXT, title TEXT, description TEXT,
  buyer_name TEXT, buyer_reg_code TEXT, cpv TEXT, value_eur REAL, issue_date TEXT, deadline TEXT,
  url TEXT, month TEXT);
CREATE INDEX IF NOT EXISTS rhr_buyer ON rhr_notice(buyer_reg_code);
CREATE INDEX IF NOT EXISTS rhr_issue ON rhr_notice(issue_date);
"""


def db_path() -> Path:
    p = Path(mcp_settings().data_dir)
    p.mkdir(parents=True, exist_ok=True)
    return p / "eesti_open_data.sqlite"


def connect(path: Path | None = None) -> sqlite3.Connection:
    con = sqlite3.connect(path or db_path(), timeout=30)
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)
    return con


def meta(con: sqlite3.Connection, source: str) -> dict | None:
    row = con.execute("SELECT * FROM meta WHERE source=?", (source,)).fetchone()
    return dict(row) if row else None


def _set_meta(con, source, url, rows):
    con.execute("INSERT OR REPLACE INTO meta VALUES (?,?,?,?)", (source, time.time(), url, rows))


def _download(url: str) -> Path:
    fd, tmp = tempfile.mkstemp(prefix="eesti_bulk_")
    os.close(fd)
    with httpx.stream("GET", url, timeout=httpx.Timeout(600, connect=20), follow_redirects=True,
                      headers={"User-Agent": mcp_settings().user_agent}) as r:
        r.raise_for_status()
        with open(tmp, "wb") as f:
            for chunk in r.iter_bytes(1 << 20):
                f.write(chunk)
    return Path(tmp)


# ---------- RIK ----------

RIK_COLS = ["name", "reg_code", "legal_form", "legal_form_sub", "vat_no", "status", "status_text",
            "registered", "_addr_extra", "address", "ehak_code", "ehak_text", "zip", "ads_adr_id",
            "ads_oid", "full_address", "url"]


def parse_rik_csv(text_stream) -> "iter[dict]":
    reader = csv.reader(text_stream, delimiter=";")
    next(reader, None)  # header
    for row in reader:
        if len(row) < len(RIK_COLS):
            continue
        rec = dict(zip(RIK_COLS, row))
        rec.pop("_addr_extra", None)
        yield rec


def load_rik(con: sqlite3.Connection, zip_path: Path | None = None) -> int:
    path = zip_path or _download(RIK_CSV_URL)
    n = 0
    try:
        with zipfile.ZipFile(path) as z:
            name = next(n for n in z.namelist() if n.endswith(".csv"))
            with z.open(name) as raw:
                stream = io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")
                con.execute("DELETE FROM company")
                cols = [c for c in RIK_COLS if c != "_addr_extra"]
                sql = f"INSERT OR REPLACE INTO company ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})"
                batch = []
                for rec in parse_rik_csv(stream):
                    batch.append([rec[c] for c in cols])
                    if len(batch) >= 5000:
                        con.executemany(sql, batch); n += len(batch); batch = []
                con.executemany(sql, batch); n += len(batch)
        _set_meta(con, "rik", RIK_CSV_URL, n)
        con.commit()
    finally:
        if zip_path is None:
            path.unlink(missing_ok=True)
    return n


# ---------- EMTA ----------

def emta_csv_url(html: str) -> str | None:
    m = re.search(r'href="(https://[^"]+/tasutud_maksud_kaesolev_aasta\.csv)"', html)
    return m.group(1) if m else None


def _num(v: str):
    v = (v or "").strip().replace(" ", "").replace(",", ".")
    if not v:
        return None
    try:
        f = float(v)
        return int(f) if f.is_integer() else f
    except ValueError:
        return None


def parse_emta_csv(text_stream) -> "iter[dict]":
    reader = csv.reader(text_stream)
    header = next(reader, None)
    if not header:
        return
    for row in reader:
        if len(row) < 7:
            continue
        row = row + [""] * (23 - len(row))
        quarters = []
        for i in range(4):
            quarters.append({
                "quarter": i + 1,
                "state_taxes_eur": _num(row[7 + i]),
                "labour_taxes_eur": _num(row[11 + i]),
                "turnover_eur": _num(row[15 + i]),
                "employees": _num(row[19 + i]),
            })
        yield {"as_of": row[0], "reg_code": row[1].strip(), "name": row[2], "kind": row[3],
               "county": row[4], "activity": row[5], "year": int(_num(row[6]) or 0), "quarters": quarters}


def load_emta(con: sqlite3.Connection, csv_path: Path | None = None, url: str | None = None) -> int:
    if csv_path is None:
        page = httpx.get(EMTA_PAGE_URL, timeout=30, follow_redirects=True,
                         headers={"User-Agent": mcp_settings().user_agent}).text
        url = emta_csv_url(page)
        if not url:
            raise RuntimeError("EMTA open-data CSV link not found on the statistics page")
        path = _download(url)
    else:
        path = csv_path
    n = 0
    try:
        with open(path, encoding="utf-8-sig", newline="") as f:
            sql = "INSERT OR REPLACE INTO emta_tax VALUES (?,?,?,?,?,?,?,?)"
            batch = []
            for r in parse_emta_csv(f):
                batch.append((r["reg_code"], r["year"], r["name"], r["kind"], r["county"], r["activity"],
                              r["as_of"], json.dumps(r["quarters"])))
                if len(batch) >= 5000:
                    con.executemany(sql, batch); n += len(batch); batch = []
            con.executemany(sql, batch); n += len(batch)
        _set_meta(con, "emta", url or str(path), n)
        con.commit()
    finally:
        if csv_path is None:
            path.unlink(missing_ok=True)
    return n


# ---------- RHR ----------

def _ln(el) -> str:
    return el.tag.rsplit("}", 1)[-1]


def _child(el, *names):
    cur = el
    for nm in names:
        nxt = None
        for c in cur:
            if _ln(c) == nm:
                nxt = c
                break
        if nxt is None:
            return None
        cur = nxt
    return cur


def _text(el, *names):
    c = _child(el, *names)
    return (c.text or "").strip() if c is not None and c.text else None


def parse_rhr_notice(el, month: str) -> dict:
    orgs = {}
    for org in el.iter():
        if _ln(org) == "Organization":
            comp = _child(org, "Company")
            if comp is None:
                continue
            oid = _text(comp, "PartyIdentification", "ID")
            orgs[oid] = {"name": _text(comp, "PartyName", "Name"),
                         "reg_code": _text(comp, "PartyLegalEntity", "CompanyID")}
    buyer_ref = None
    cp = _child(el, "ContractingParty")
    if cp is not None:
        buyer_ref = _text(cp, "Party", "PartyIdentification", "ID")
    buyer = orgs.get(buyer_ref) or next(iter(orgs.values()), {"name": None, "reg_code": None})
    proj = _child(el, "ProcurementProject")
    title = desc = cpv = ref = None
    value = None
    if proj is not None:
        ref = _text(proj, "ID")
        title = _text(proj, "Name")
        desc = _text(proj, "Description")
        cpv = _text(proj, "MainCommodityClassification", "ItemClassificationCode")
        v = _text(proj, "RequestedTenderTotal", "EstimatedOverallContractAmount")
        value = float(v) if v else None
    deadline = url = None
    for e in el.iter():
        t = _ln(e)
        if t == "TenderSubmissionDeadlinePeriod" and deadline is None:
            deadline = _text(e, "EndDate")
        elif t == "URI" and url is None and e.text and "rhr-web" in e.text:
            url = e.text.strip()
    notice_id = None
    for c in el:
        if _ln(c) == "ID" and c.attrib.get("schemeName") == "notice-id":
            notice_id = (c.text or "").strip()
    return {
        "notice_id": notice_id or _text(el, "ContractFolderID"),
        "procurement_ref": ref, "notice_type": _ln(el), "title": title,
        "description": (desc or "")[:1500] or None,
        "buyer_name": buyer.get("name"), "buyer_reg_code": buyer.get("reg_code"),
        "cpv": cpv, "value_eur": value,
        "issue_date": (_text(el, "IssueDate") or "")[:10] or None,
        "deadline": (deadline or "")[:10] or None,
        "url": url, "month": month,
    }


def iter_rhr_xml(path_or_file, month: str):
    depth = 0
    for ev, el in ET.iterparse(path_or_file, events=("start", "end")):
        if ev == "start":
            depth += 1
            continue
        depth -= 1
        if depth == 1:
            try:
                yield parse_rhr_notice(el, month)
            finally:
                el.clear()


RHR_COLS = ["notice_id", "procurement_ref", "notice_type", "title", "description", "buyer_name",
            "buyer_reg_code", "cpv", "value_eur", "issue_date", "deadline", "url", "month"]


def load_rhr(con: sqlite3.Connection, months: int = 3, files: dict[str, Path] | None = None) -> int:
    n = 0
    targets: dict[str, Path | None] = {}
    if files:
        targets.update(files)
    else:
        d = date.today().replace(day=1)
        for _ in range(months):
            targets[f"{d.year}-{d.month:02d}"] = None
            d = (d.replace(day=1) - __import__("datetime").timedelta(days=1)).replace(day=1)
    sql = f"INSERT OR REPLACE INTO rhr_notice VALUES ({','.join('?' * len(RHR_COLS))})"
    for month, path in targets.items():
        tmp = None
        if path is None:
            y, m = month.split("-")
            try:
                path = tmp = _download(RHR_MONTH_URL.format(y=int(y), m=int(m)))
            except httpx.HTTPError as e:
                log.warning("RHR %s not available: %s", month, e)
                continue
        try:
            con.execute("DELETE FROM rhr_notice WHERE month=?", (month,))
            batch = [[r[c] for c in RHR_COLS] for r in iter_rhr_xml(str(path), month) if r["notice_id"]]
            con.executemany(sql, batch)
            n += len(batch)
        finally:
            if tmp:
                tmp.unlink(missing_ok=True)
    _set_meta(con, "rhr", RHR_MONTH_URL, n)
    con.commit()
    return n


LOADERS = {"rik": load_rik, "emta": load_emta, "rhr": load_rhr}


def refresh_stale(max_age_h: int | None = None) -> dict:
    """Reload every bulk source older than max_age_h. Errors are logged, never raised."""
    max_age = (max_age_h or mcp_settings().bulk_max_age_h) * 3600
    done = {}
    con = connect()
    try:
        for name, fn in LOADERS.items():
            m = meta(con, name)
            if m and time.time() - m["loaded_at"] < max_age:
                continue
            try:
                done[name] = fn(con)
                log.info("bulk %s loaded: %s rows", name, done[name])
            except Exception as e:  # noqa: BLE001
                log.warning("bulk %s failed: %s", name, e)
                done[name] = f"error: {e}"
    finally:
        con.close()
    return done


def start_background_refresh() -> threading.Thread:
    def loop():
        while True:
            refresh_stale()
            time.sleep(3600)
    t = threading.Thread(target=loop, name="bulk-refresh", daemon=True)
    t.start()
    return t


def status() -> dict:
    try:
        con = connect()
        try:
            return {r["source"]: {"loaded_at": r["loaded_at"], "rows": r["rows"]}
                    for r in con.execute("SELECT * FROM meta")}
        finally:
            con.close()
    except Exception as e:  # noqa: BLE001
        return {"error": str(e)}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    con = connect()
    for name in (LOADERS if which == "all" else [which]):
        print(name, LOADERS[name](con))
