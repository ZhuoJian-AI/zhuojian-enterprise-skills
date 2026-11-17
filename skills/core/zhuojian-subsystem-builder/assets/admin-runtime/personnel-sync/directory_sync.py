#!/usr/bin/env python3
"""Small, dependency-free Runtime sender. Collector owns source semantics.

Input: {departments: [{external_id,name,parent_external_id}],
        employees: [{external_id,display_name,department_external_id,is_active}]}.
Missing entries never generate departure events. No passwords or roles travel.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler
from uuid import uuid4


class SyncError(RuntimeError):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def json_text(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def normalize(value):
    if not isinstance(value, dict) or set(value) != {"departments", "employees"}:
        raise SyncError("Collector must return departments and employees")
    result = {"departments": [], "employees": []}
    for kind, allowed, required in (
        ("departments", {"external_id", "name", "parent_external_id"}, {"external_id", "name"}),
        ("employees", {"external_id", "display_name", "department_external_id", "is_active"},
         {"external_id", "display_name", "is_active"}),
    ):
        if not isinstance(value[kind], list):
            raise SyncError("Collector rows must be lists")
        seen = set()
        for row in value[kind]:
            if not isinstance(row, dict) or set(row) - allowed or not required <= set(row):
                raise SyncError("Collector row has unsupported or missing fields")
            for key in required - {"is_active"}:
                if not isinstance(row[key], str) or not row[key].strip():
                    raise SyncError("Source IDs and names must be nonempty strings")
            if "is_active" in row and row["is_active"] is not None and type(row["is_active"]) is not bool:
                raise SyncError("Employment state must be an explicit boolean or null for profiles-only sources")
            for key in allowed - required:
                if row.get(key) is not None and (not isinstance(row[key], str) or not row[key]):
                    raise SyncError("Department references must be strings or null")
            if row["external_id"] in seen:
                raise SyncError("Duplicate source ID")
            seen.add(row["external_id"])
            # Explicit nulls make omitted/null references one stable snapshot.
            result[kind].append({key: row.get(key) for key in sorted(allowed)})
    pending = {r["external_id"]: r for r in result["departments"]}
    ordered = []
    while pending:
        ready = sorted((r for r in pending.values() if r["parent_external_id"] not in pending), key=lambda r:r["external_id"])
        if not ready:
            raise SyncError("Collector department tree contains a cycle")
        for row in ready:
            ordered.append(row); pending.pop(row["external_id"])
    result["departments"] = ordered
    result["employees"].sort(key=lambda r:r["external_id"])
    return result


def connect(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    db = sqlite3.connect(path, timeout=30)
    if os.name != "nt":
        path.chmod(0o600)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("CREATE TABLE IF NOT EXISTS observed(kind TEXT,external_id TEXT,revision INTEGER,content TEXT,PRIMARY KEY(kind,external_id))")
    db.execute("CREATE TABLE IF NOT EXISTS outbox(sequence INTEGER PRIMARY KEY AUTOINCREMENT,request_id TEXT UNIQUE,payload TEXT)")
    db.execute("CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT)")
    return db


def enqueue(db, snapshot, *, identity):
    """Advance source revisions only in the transaction that saves delivery."""
    normalized = normalize(snapshot)
    db.execute("BEGIN IMMEDIATE")
    try:
        check_identity(db,identity)
        changes = {"departments": [], "employees": []}
        for kind, rows in normalized.items():
            for row in rows:
                content = json_text(row)
                previous = db.execute("SELECT revision,content FROM observed WHERE kind=? AND external_id=?", (kind,row["external_id"])).fetchone()
                if previous and previous[1] == content:
                    continue
                version = previous[0] + 1 if previous else 1
                changes[kind].append({**row, "source_version": version})
                db.execute("INSERT INTO observed VALUES (?,?,?,?) ON CONFLICT(kind,external_id) DO UPDATE SET revision=excluded.revision,content=excluded.content",
                    (kind,row["external_id"],version,content))
        # Departments precede employees, including after a lost acknowledgement.
        batches = []
        if len(changes["departments"]) <= 500 and len(changes["employees"]) <= 500:
            if any(changes.values()):
                batches.append(changes)
        else:
            for kind in ("departments", "employees"):
                for offset in range(0,len(changes[kind]),500):
                    batches.append({"departments": changes[kind][offset:offset+500] if kind=="departments" else [],
                        "employees": changes[kind][offset:offset+500] if kind=="employees" else []})
        for batch in batches:
            request_id = str(uuid4())
            db.execute("INSERT INTO outbox(request_id,payload) VALUES (?,?)", (request_id,json_text({**batch,"request_id":request_id})))
        db.commit()
        return len(batches)
    except BaseException:
        db.rollback()
        raise


def check_identity(db, identity):
    old = db.execute("SELECT value FROM settings WHERE key='identity'").fetchone()
    if old and old[0] != identity:
        raise SyncError("State belongs to another enterprise source; use a separate state file")
    db.execute("INSERT OR IGNORE INTO settings VALUES ('identity',?)", (identity,))


def deliver(origin, source_key, credential, batch, *, opener=None):
    parsed = urlsplit(origin)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in {"", "/"}:
        raise SyncError("Platform origin must be a plain HTTPS origin")
    if not credential.startswith("zjrt_"):
        raise SyncError("Existing Runtime registration credential required")
    url = origin.rstrip("/") + "/api/v1/ecs-publisher/directory/"+quote(source_key,safe="")+"/batches"
    request = Request(url, data=json_text(batch).encode(), method="POST",
        headers={"Content-Type":"application/json","Authorization":"Bearer "+credential})
    try:
        with (opener or build_opener(NoRedirect())).open(request, timeout=60) as response:
            content = response.read(1048577)
            if len(content) > 1048576:
                raise SyncError("Oversized batch receipt")
            result = json.loads(content)
    except HTTPError as exc:
        raise SyncError("Batch delivery rejected: HTTP "+str(exc.code)) from None
    except (URLError, TimeoutError, ValueError):
        raise SyncError("Batch delivery unavailable; durable outbox retained") from None
    if (not isinstance(result, dict) or result.get("request_id") != batch["request_id"]
            or result.get("source_key") != source_key or result.get("dry_run") is not False):
        raise SyncError("Receipt does not acknowledge this source batch")
    return result


def drain(db, send):
    # Hold SQLite's ordinary write lock through send + ACK, so two timer/manual
    # invocations cannot deliver newer batches ahead of an older pending one.
    sent = 0
    while True:
        db.execute("BEGIN IMMEDIATE")
        try:
            row = db.execute("SELECT sequence,payload FROM outbox ORDER BY sequence LIMIT 1").fetchone()
            if row is None:
                db.commit(); return sent
            send(json.loads(row[1]))
            db.execute("DELETE FROM outbox WHERE sequence=?", (row[0],))
            db.commit(); sent += 1
        except BaseException:
            db.rollback(); raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--preview", action="store_true", help="Read source and show counts only; no SaaS or state writes")
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    command = config.get("collector_argv")
    if not isinstance(command, list) or not command or any(not isinstance(v,str) for v in command):
        raise SyncError("collector_argv must be the registered read-only collector command")
    def collect():
        completed = subprocess.run(command, capture_output=True, check=False, timeout=120)
        if completed.returncode:
            raise SyncError("Source collector failed; no new batch created")
        return normalize(json.loads(completed.stdout))
    if args.preview:
        snapshot = collect()
        print(json_text({"departments":len(snapshot["departments"]),"employees":len(snapshot["employees"]),
            "explicit_inactive":sum(r["is_active"] is False for r in snapshot["employees"]),"saas_writes":False}))
        return
    profile = json.loads(Path(config.get("runtime_profile","/etc/zhuojian/runtime.json")).read_text(encoding="utf-8"))
    origin = profile["platform"]["baseUrl"]
    identity = json_text([origin,profile["organizationId"],profile["runtimeId"],config["source_key"]])
    credential = Path(config.get("credential_file","/etc/zhuojian/runtime-registration.key")).read_text().strip()
    with connect(config["state_file"]) as db:
        check_identity(db,identity)
        db.commit()
        # An unavailable original system must not prevent retrying old batches.
        sent = drain(db,lambda batch:deliver(origin,config["source_key"],credential,batch))
        snapshot = collect()
        enqueue(db,snapshot,identity=identity)
        sent += drain(db,lambda batch:deliver(origin,config["source_key"],credential,batch))
        print(json_text({"delivered_batches":sent,"pending_batches":db.execute("SELECT count(*) FROM outbox").fetchone()[0]}))


if __name__ == "__main__":
    try:
        main()
    except (SyncError, OSError, subprocess.SubprocessError, ValueError, KeyError, sqlite3.Error) as exc:
        # Never print collector stderr, source records, command arguments or tokens.
        print(str(exc) if isinstance(exc,SyncError) else "Personnel sync failed; check protected local configuration",file=sys.stderr)
        sys.exit(1)
