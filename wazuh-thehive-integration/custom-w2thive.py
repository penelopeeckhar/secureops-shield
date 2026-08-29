#!/var/ossec/framework/python/bin/python3
import sys
import json
import requests
from datetime import datetime, timezone
import os

# Configuration
THEHIVE_URL = os.environ.get("THEHIVE_URL", "http://192.168.111.10:9000")
THEHIVE_API_KEY = os.environ.get("THEHIVE_API_KEY", "")

def main():
    alert_file = sys.argv[1]

    with open(alert_file) as f:
        alert_json = json.load(f)

    rule = alert_json.get('rule', {})
    agent = alert_json.get('agent', {})

    title = f"Wazuh Alert: {rule.get('description', 'Unknown')}"
    description = json.dumps(alert_json, indent=2)
    severity = 2  # default: medium
    level = rule.get('level', 0)
    if level >= 12:
        severity = 3  # high
    elif level >= 7:
        severity = 2  # medium
    else:
        severity = 1  # low

    payload = {
        "type": "wazuh",
        "source": "wazuh-manager",
        "sourceRef": alert_json.get('id', str(datetime.now(timezone.utc).timestamp())),
        "title": title,
        "description": description,
        "severity": severity,
        "tlp": 2,
        "tags": [f"agent:{agent.get('name', 'unknown')}", f"rule:{rule.get('id', 'unknown')}"]
    }

    headers = {
        "Authorization": f"Bearer {THEHIVE_API_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.post(f"{THEHIVE_URL}/api/v1/alert", json=payload, headers=headers, timeout=10)
    with open("/tmp/w2thive-debug.log", "a") as log:
        log.write(f"{datetime.now()}: status={response.status_code} body={response.text}\n")

if __name__ == "__main__":
    main()
