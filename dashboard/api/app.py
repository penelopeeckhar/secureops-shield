import json
import os
import re
from datetime import datetime, timezone

import requests
from flask import Flask, jsonify, Response
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

TRIVY_IMAGE_PATH = os.environ.get("TRIVY_IMAGE_PATH", "/data/trivy-hardened-v3.json")
TRIVY_K8S_PATH = os.environ.get("TRIVY_K8S_PATH", "/data/trivy-k8s-full.json")
KUBE_BENCH_PATH = os.environ.get("KUBE_BENCH_PATH", "/data/kube-bench-report.txt")
ZAP_PATH = os.environ.get("ZAP_PATH", "/data/zap-fullscan-report.json")

THEHIVE_URL = os.environ.get("THEHIVE_URL", "http://192.168.111.10:9000")
THEHIVE_API_KEY = os.environ.get("THEHIVE_API_KEY", "")


def safe_json(path):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception as e:
        return {"_error": str(e)}


def parse_trivy_image():
    data = safe_json(TRIVY_IMAGE_PATH)
    if "_error" in data:
        return {"available": False, "error": data["_error"]}

    sev_count = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "UNKNOWN": 0}
    for result in data.get("Results", []) or []:
        for vuln in result.get("Vulnerabilities", []) or []:
            sev = vuln.get("Severity", "UNKNOWN")
            sev_count[sev] = sev_count.get(sev, 0) + 1

    total = sum(sev_count.values())
    return {
        "available": True,
        "total": total,
        "severities": sev_count,
        "artifact": data.get("ArtifactName", "unknown"),
    }


def parse_trivy_k8s():
    data = safe_json(TRIVY_K8S_PATH)
    if "_error" in data:
        return {"available": False, "error": data["_error"]}

    sev_count = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "UNKNOWN": 0}
    results = data.get("Results", data if isinstance(data, list) else [])
    for result in results or []:
        for vuln in result.get("Vulnerabilities", []) or []:
            sev = vuln.get("Severity", "UNKNOWN")
            sev_count[sev] = sev_count.get(sev, 0) + 1
        for mc in result.get("Misconfigurations", []) or []:
            sev = mc.get("Severity", "UNKNOWN")
            sev_count[sev] = sev_count.get(sev, 0) + 1

    return {"available": True, "total": sum(sev_count.values()), "severities": sev_count}


def parse_kube_bench():
    try:
        with open(KUBE_BENCH_PATH, "r") as f:
            lines = f.readlines()
    except Exception as e:
        return {"available": False, "error": str(e)}

    counts = {"PASS": 0, "FAIL": 0, "WARN": 0, "INFO": 0}
    for line in lines:
        m = re.match(r"^\[(PASS|FAIL|WARN|INFO)\]", line.strip())
        if m:
            counts[m.group(1)] += 1

    checked = counts["PASS"] + counts["FAIL"]
    pct = round((counts["PASS"] / checked) * 100) if checked else None
    return {"available": True, "counts": counts, "compliance_pct": pct}


def parse_zap():
    data = safe_json(ZAP_PATH)
    if "_error" in data:
        return {"available": False, "error": data["_error"]}

    risk_labels = {"3": "High", "2": "Medium", "1": "Low", "0": "Informational"}
    counts = {"High": 0, "Medium": 0, "Low": 0, "Informational": 0}
    top_finding = None
    top_risk = -1

    for site in data.get("site", []) or []:
        for alert in site.get("alerts", []) or []:
            risk = risk_labels.get(str(alert.get("riskcode", "0")), "Informational")
            try:
                n = int(alert.get("count", 1))
            except (TypeError, ValueError):
                n = 1
            counts[risk] += n
            rc = int(alert.get("riskcode", 0))
            if rc > top_risk:
                top_risk = rc
                top_finding = alert.get("name") or alert.get("alert")

    total = sum(counts.values())
    return {"available": True, "total": total, "risk": counts, "top_finding": top_finding}


def query_thehive():
    if not THEHIVE_API_KEY:
        return {"available": False, "error": "THEHIVE_API_KEY not set"}

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {THEHIVE_API_KEY}",
    }

    def count_query(name):
        body = {"query": [{"_name": name}, {"_name": "count"}]}
        r = requests.post(f"{THEHIVE_URL}/api/v1/query", json=body, headers=headers, timeout=5)
        r.raise_for_status()
        return r.json()

    try:
        alert_total = count_query("listAlert")
        case_total = count_query("listCase")
        return {"available": True, "alerts_total": alert_total, "cases_total": case_total}
    except Exception as e:
        return {"available": False, "error": str(e)}


def compute_score(image, dast, k8s):
    # Each category gets its own 0-100 sub-score (capped independently),
    # then a weighted average — one severe category no longer zeroes
    # out the whole score. Coefficients are a documented heuristic,
    # not a security-industry standard.
    scores = {}

    if image.get("available"):
        s = image["severities"]
        deduction = s.get("CRITICAL", 0) * 4 + s.get("HIGH", 0) * 0.3 + s.get("MEDIUM", 0) * 0.1
        scores["image"] = max(0, 100 - deduction)

    if dast.get("available"):
        r = dast["risk"]
        deduction = r.get("High", 0) * 8 + r.get("Medium", 0) * 1 + r.get("Low", 0) * 0.2
        scores["dast"] = max(0, 100 - deduction)

    if k8s.get("available") and k8s.get("compliance_pct") is not None:
        scores["k8s"] = k8s["compliance_pct"]

    weights = {"image": 0.4, "dast": 0.3, "k8s": 0.3}
    available_weight = sum(weights[k] for k in scores)
    if available_weight == 0:
        return 0

    weighted = sum(scores[k] * weights[k] for k in scores) / available_weight
    global_score = round(weighted)
    sub_scores = {k: round(v) for k, v in scores.items()}
    sub_scores["global"] = global_score
    return global_score, sub_scores


@app.route("/api/summary")
def summary():
    image = parse_trivy_image()
    k8s_vulns = parse_trivy_k8s()
    k8s_bench = parse_kube_bench()
    dast = parse_zap()
    hive = query_thehive()
    timeline = query_timeline()

    score, sub_scores = compute_score(image, dast, k8s_bench)

    return jsonify({
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "global_score": score,
        "sub_scores": sub_scores,
        "image_scan": image,
        "kubernetes": {"cis_benchmark": k8s_bench, "vulnerabilities": k8s_vulns},
        "dast": dast,
        "soar": hive,
        "timeline": timeline,
    })


@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)


SEVERITY_PILL = {"LOW": "ok", "MEDIUM": "warn", "HIGH": "crit", "CRITICAL": "crit"}


def query_timeline(limit=8):
    if not THEHIVE_API_KEY:
        return {"available": False, "error": "THEHIVE_API_KEY not set", "items": []}

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {THEHIVE_API_KEY}",
    }
    body = {
        "query": [
            {"_name": "listAlert"},
            {"_name": "sort", "_fields": [{"_createdAt": "desc"}]},
            {"_name": "page", "from": 0, "to": limit},
        ]
    }

    try:
        r = requests.post(f"{THEHIVE_URL}/api/v1/query", json=body, headers=headers, timeout=5)
        r.raise_for_status()
        alerts = r.json()
    except Exception as e:
        return {"available": False, "error": str(e), "items": []}

    items = []
    for a in alerts:
        ts = a.get("date") or a.get("_createdAt")
        time_str = ""
        if ts:
            try:
                time_str = datetime.fromtimestamp(ts / 1000, tz=timezone.utc).strftime("%H:%M:%S")
            except Exception:
                time_str = ""
        sev_label = a.get("severityLabel", "MEDIUM")
        tags = a.get("tags", [])
        items.append({
            "time": time_str,
            "source": a.get("source", "unknown"),
            "desc": a.get("title", ""),
            "tag": tags[-1] if tags else a.get("type", ""),
            "severity": sev_label,
            "pill": SEVERITY_PILL.get(sev_label, "warn"),
        })

    return {"available": True, "items": items}


from report import generate_pdf_bytes


@app.route("/api/report")
def report():
    image = parse_trivy_image()
    k8s_vulns = parse_trivy_k8s()
    k8s_bench = parse_kube_bench()
    dast = parse_zap()
    hive = query_thehive()
    timeline = query_timeline()
    score, sub_scores = compute_score(image, dast, k8s_bench)

    data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "global_score": score,
        "sub_scores": sub_scores,
        "image_scan": image,
        "kubernetes": {"cis_benchmark": k8s_bench, "vulnerabilities": k8s_vulns},
        "dast": dast,
        "soar": hive,
        "timeline": timeline,
    }

    pdf_bytes = generate_pdf_bytes(data)
    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={"Content-Disposition": "attachment; filename=secureops-shield-report.pdf"},
    )
