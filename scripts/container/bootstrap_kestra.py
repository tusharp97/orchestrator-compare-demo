#!/usr/bin/env python3
"""Create the demo Kestra flow, trigger it, and wait for it to succeed.

Kestra moved its REST paths under a tenant prefix (``/api/v1/main/...``) in
newer releases while older ones use ``/api/v1/...``. The API base is detected at
runtime so the demo works on either layout.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

KESTRA = os.environ.get("KESTRA_URL", "http://kestra:8080").rstrip("/")
MGMT = os.environ.get("KESTRA_MGMT_URL", "http://kestra:8081").rstrip("/")
TENANT = os.environ.get("KESTRA_TENANT", "main")
NAMESPACE = "demo"
FLOW_ID = "shop_revenue_pipeline"
FLOW_PATH = Path(
    os.environ.get(
        "KESTRA_FLOW_PATH", "/opt/demo/kestra/flows/shop_revenue_pipeline.yml"
    )
)

SUCCESS_STATES = {"SUCCESS", "WARNING"}
FAILURE_STATES = {"FAILED", "KILLED", "CANCELLED"}


def call(method, url, data=None, content_type=None):
    """Return (status, parsed_body). HTTP errors are returned, not raised."""
    headers = {"Accept": "application/json"}
    if content_type:
        headers["Content-Type"] = content_type
    request = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            raw = response.read()
            status = response.status
    except urllib.error.HTTPError as error:
        raw = error.read()
        status = error.code
    if not raw:
        return status, None
    text = raw.decode("utf-8", errors="replace")
    try:
        return status, json.loads(text)
    except json.JSONDecodeError:
        return status, text


def wait_ready() -> None:
    print(f"Waiting for Kestra at {MGMT}/health")
    for _ in range(120):
        try:
            with urllib.request.urlopen(f"{MGMT}/health", timeout=5):
                print("Kestra is ready")
                return
        except urllib.error.HTTPError:
            # The server answered, which is all this check needs.
            print("Kestra is ready")
            return
        except Exception:
            time.sleep(4)
    raise SystemExit("Kestra did not become ready")


def detect_base() -> str:
    candidates = [f"{KESTRA}/api/v1/{TENANT}", f"{KESTRA}/api/v1"]
    for base in candidates:
        status, _ = call("GET", f"{base}/flows/search?size=1")
        if status == 200:
            print(f"Using Kestra API base {base}")
            return base
    raise SystemExit(
        f"Could not find a working Kestra API base. Tried: {', '.join(candidates)}"
    )


def upsert_flow(base: str, yaml_text: str) -> None:
    payload = yaml_text.encode("utf-8")
    status, body = call(
        "POST", f"{base}/flows", data=payload, content_type="application/x-yaml"
    )
    if status in (200, 201):
        print("Created Kestra flow")
        return
    status, body = call(
        "PUT",
        f"{base}/flows/{NAMESPACE}/{FLOW_ID}",
        data=payload,
        content_type="application/x-yaml",
    )
    if status in (200, 201):
        print("Updated Kestra flow")
        return
    raise SystemExit(f"Failed to upsert Kestra flow ({status}): {body}")


def trigger(base: str) -> str:
    status, body = call("POST", f"{base}/executions/{NAMESPACE}/{FLOW_ID}")
    if status not in (200, 201) or not isinstance(body, dict) or "id" not in body:
        raise SystemExit(f"Failed to trigger Kestra flow ({status}): {body}")
    print(f"Triggered Kestra execution {body['id']}")
    return body["id"]


def wait_success(base: str, execution_id: str) -> None:
    url = f"{base}/executions/{execution_id}"
    last_state = None
    for _ in range(120):
        status, body = call("GET", url)
        if status != 200 or not isinstance(body, dict):
            time.sleep(4)
            continue
        state = body.get("state")
        if isinstance(state, dict):
            state = state.get("current")
        if state != last_state:
            print(f"Kestra execution {execution_id} state={state}", flush=True)
            last_state = state
        if state in SUCCESS_STATES:
            return
        if state in FAILURE_STATES:
            raise SystemExit(f"Kestra pipeline ended with state {state}")
        time.sleep(5)
    raise SystemExit("Kestra pipeline did not finish in time")


def main() -> None:
    if not FLOW_PATH.exists():
        raise SystemExit(f"Missing flow file {FLOW_PATH}")
    wait_ready()
    base = detect_base()
    upsert_flow(base, FLOW_PATH.read_text(encoding="utf-8"))
    wait_success(base, trigger(base))


if __name__ == "__main__":
    main()
