from datetime import datetime, timezone

from weasyprint import HTML

SEV_COLOR = {"CRITICAL": "#EF4444", "HIGH": "#F5A623", "MEDIUM": "#8B96A8", "LOW": "#5EEAD4", "UNKNOWN": "#8B96A8"}
RISK_COLOR = {"High": "#EF4444", "Medium": "#F5A623", "Low": "#8B96A8", "Informational": "#8B96A8"}


def _score_color(pct):
    if pct is None:
        return "#8B96A8"
    if pct >= 70:
        return "#0F8F7E"
    if pct >= 40:
        return "#B8710A"
    return "#C0392B"


def _sev_rows(severities, color_map):
    rows = ""
    for label, count in severities.items():
        if count == 0:
            continue
        color = color_map.get(label, "#8B96A8")
        rows += f'''
        <tr>
          <td><span class="dot" style="background:{color}"></span>{label.title()}</td>
          <td class="num">{count}</td>
        </tr>'''
    return rows or '<tr><td colspan="2" class="muted">Aucune entrée</td></tr>'


def _timeline_rows(items):
    rows = ""
    for it in items[:12]:
        color = {"ok": "#0F8F7E", "warn": "#B8710A", "crit": "#C0392B"}.get(it.get("pill"), "#8B96A8")
        rows += f'''
        <tr>
          <td class="mono">{it.get("time", "—")}</td>
          <td>{it.get("source", "")}</td>
          <td>{it.get("desc", "")}</td>
          <td class="mono">{it.get("tag", "")}</td>
          <td><span class="pill" style="background:{color}22; color:{color}">{it.get("severity", "")}</span></td>
        </tr>'''
    return rows or '<tr><td colspan="5" class="muted">Aucun incident récent</td></tr>'


def build_html(data):
    now = datetime.now(timezone.utc).strftime("%d/%m/%Y à %H:%M UTC")
    score = data.get("global_score", 0)
    sub = data.get("sub_scores", {})
    image = data.get("image_scan", {})
    dast = data.get("dast", {})
    k8s = data.get("kubernetes", {}).get("cis_benchmark", {})
    soar = data.get("soar", {})
    timeline = data.get("timeline", {}).get("items", [])

    score_color = _score_color(score)

    return f'''<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<style>
@page {{ size: A4; margin: 0; }}
@page :not(:first) {{ margin: 22mm 18mm; @bottom-center {{ content: "SecureOps Shield — Rapport de sécurité"; font-family: Helvetica, Arial, sans-serif; font-size: 8px; color: #8B96A8; }} }}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: Helvetica, Arial, sans-serif; color: #1B2434; font-size: 10.5px; line-height: 1.5; }}
.mono {{ font-family: "Courier New", monospace; }}
h1, h2, h3 {{ font-family: Helvetica, Arial, sans-serif; font-weight: 700; }}

/* ---- Cover page ---- */
.cover {{
  background: #0B0F17; color: #E8ECF1;
  width: 210mm; height: 297mm;
  page-break-after: always;
  padding: 30mm 22mm;
  position: relative;
}}
.cover .brand {{ font-family: Helvetica, Arial, sans-serif; font-weight: 700; font-weight: 700; font-size: 15px; margin-bottom: 60mm; letter-spacing: 0.3px; }}
.cover .eyebrow {{ color: #6C8CFF; font-size: 11px; letter-spacing: 2px; text-transform: uppercase; font-weight: 600; margin-bottom: 10px; }}
.cover h1 {{ font-size: 30px; font-weight: 700; line-height: 1.25; max-width: 130mm; margin-bottom: 14mm; }}
.cover .meta {{ color: #8B96A8; font-size: 10px; }}
.cover .score-block {{ position: absolute; bottom: 30mm; left: 22mm; }}
.cover .score-num {{ font-family: "Courier New", monospace; font-weight: 600; font-size: 46px; color: {score_color if score>=70 else ('#F5A623' if score>=40 else '#EF4444')}; }}
.cover .score-label {{ font-size: 9px; color: #8B96A8; letter-spacing: 1.5px; text-transform: uppercase; margin-top: 2px; }}

/* ---- Body pages ---- */
section {{ margin-bottom: 9mm; page-break-inside: avoid; }}
h2 {{ font-size: 14px; font-weight: 600; margin-bottom: 4mm; color: #0B0F17; border-bottom: 1px solid #E3E7EE; padding-bottom: 2mm; }}
.grid {{ display: flex; gap: 5mm; margin-bottom: 6mm; }}
.card {{ flex: 1; border: 1px solid #E3E7EE; border-radius: 3mm; padding: 4mm; }}
.card .label {{ font-size: 8.5px; color: #8B96A8; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 2mm; }}
.card .value {{ font-family: "Courier New", monospace; font-weight: 600; font-size: 20px; }}
.card .sub {{ font-size: 8.5px; color: #8B96A8; margin-top: 1mm; }}

table {{ width: 100%; border-collapse: collapse; font-size: 9.5px; }}
th {{ text-align: left; font-size: 8px; text-transform: uppercase; letter-spacing: 0.5px; color: #8B96A8; padding: 2mm 3mm; border-bottom: 1px solid #E3E7EE; }}
td {{ padding: 2mm 3mm; border-bottom: 1px solid #F0F2F6; }}
td.num {{ font-family: "Courier New", monospace; text-align: right; }}
.muted {{ color: #8B96A8; font-style: italic; }}
.dot {{ display: inline-block; width: 2.2mm; height: 2.2mm; border-radius: 50%; margin-right: 2mm; }}
.pill {{ font-family: "Courier New", monospace; font-size: 8px; padding: 0.8mm 2mm; border-radius: 2mm; font-weight: 600; }}
.methodology {{ background: #F7F9FC; border-radius: 3mm; padding: 5mm; font-size: 9px; color: #4A5568; line-height: 1.6; }}
</style>
</head>
<body>

<div class="cover">
  <div class="brand">SecureOps Shield</div>
  <div class="eyebrow">Rapport de sécurité consolidé</div>
  <h1>Défense en profondeur — synthèse du pipeline DevSecOps</h1>
  <div class="meta">Généré le {now}<br>SAST · Secrets · SCA · Image · DAST · Kubernetes · EDR · SOAR</div>
  <div class="score-block">
    <div class="score-num">{score}</div>
    <div class="score-label">Score global / 100</div>
  </div>
</div>

<section>
  <h2>Résumé par catégorie</h2>
  <div class="grid">
    <div class="card">
      <div class="label">Scan d'image (Trivy)</div>
      <div class="value">{image.get("total", "—")}</div>
      <div class="sub">Score {sub.get("image", "—")}/100</div>
    </div>
    <div class="card">
      <div class="label">DAST (OWASP ZAP)</div>
      <div class="value">{dast.get("total", "—")}</div>
      <div class="sub">Score {sub.get("dast", "—")}/100</div>
    </div>
    <div class="card">
      <div class="label">Kubernetes (CIS)</div>
      <div class="value">{k8s.get("compliance_pct", "—")}%</div>
      <div class="sub">kube-bench + Trivy k8s</div>
    </div>
    <div class="card">
      <div class="label">SOAR (TheHive)</div>
      <div class="value">{soar.get("cases_total", "—")}</div>
      <div class="sub">{soar.get("alerts_total", "—")} alertes au total</div>
    </div>
  </div>
</section>

<section>
  <h2>Scan d'image Docker — détail par sévérité</h2>
  <table>
    <tr><th>Sévérité</th><th style="text-align:right">Nombre</th></tr>
    {_sev_rows(image.get("severities", {}), SEV_COLOR)}
  </table>
</section>

<section>
  <h2>DAST — détail par niveau de risque</h2>
  <table>
    <tr><th>Risque</th><th style="text-align:right">Nombre</th></tr>
    {_sev_rows(dast.get("risk", {}), RISK_COLOR)}
  </table>
  <div style="margin-top:4mm; font-size:9.5px;"><b>Principale faille identifiée :</b> {dast.get("top_finding", "—")}</div>
</section>

<section>
  <h2>Conformité Kubernetes (CIS Benchmark)</h2>
  <table>
    <tr><th>Statut</th><th style="text-align:right">Nombre</th></tr>
    <tr><td><span class="dot" style="background:#0F8F7E"></span>Pass</td><td class="num">{k8s.get("counts", {}).get("PASS", "—")}</td></tr>
    <tr><td><span class="dot" style="background:#C0392B"></span>Fail</td><td class="num">{k8s.get("counts", {}).get("FAIL", "—")}</td></tr>
    <tr><td><span class="dot" style="background:#B8710A"></span>Warn</td><td class="num">{k8s.get("counts", {}).get("WARN", "—")}</td></tr>
    <tr><td><span class="dot" style="background:#8B96A8"></span>Info</td><td class="num">{k8s.get("counts", {}).get("INFO", "—")}</td></tr>
  </table>
</section>

<section>
  <h2>Chronologie des incidents récents (TheHive)</h2>
  <table>
    <tr><th>Heure</th><th>Source</th><th>Description</th><th>Règle</th><th>Sévérité</th></tr>
    {_timeline_rows(timeline)}
  </table>
</section>

<section>
  <h2>Méthodologie de scoring</h2>
  <div class="methodology">
    Le score global est une moyenne pondérée de trois sous-scores indépendants
    (Image 40%, DAST 30%, Kubernetes 30%), chacun plafonné entre 0 et 100 avant
    pondération — une catégorie sévère ne peut donc pas annuler artificiellement
    les autres. Coefficients de déduction : Image (Critique ×4, Haute ×0.3,
    Moyenne ×0.1), DAST (Haut ×8, Moyen ×1, Bas ×0.2), Kubernetes (score = %
    de conformité CIS Benchmark). Cette pondération est un choix méthodologique
    documenté pour ce projet, pas une norme du secteur.
  </div>
</section>

</body>
</html>'''


def generate_pdf_bytes(data):
    html = build_html(data)
    return HTML(string=html).write_pdf(optimize_size=())
