# SecureOps Shield

Pipeline DevSecOps complet — de l'analyse du code source à la détection
d'intrusion en temps réel, avec orchestration automatisée de la réponse
à incident.

Projet de fin d'études (PFA) — ENSA Fès, GDNC.

---

## Architecture

Une application volontairement vulnérable (OWASP Juice Shop) sert de cible
à une chaîne de sécurité complète : analyse statique en CI/CD, scan
d'image durcie, tests dynamiques, audit Kubernetes, détection
comportementale (EDR), réponse à incident automatisée (SOAR), le tout
consolidé dans un dashboard de scoring centralisé.
Code source ──▶ CI/CD (SAST/Secrets/SCA) ──▶ Image Docker durcie
│
▼
Kubernetes (CIS) ◀── DAST (ZAP) ◀── Application déployée
│
▼
EDR (Wazuh) ──▶ SOAR (TheHive + Cortex) ──▶ Dashboard consolidé


## Correspondance blocs du projet ↔ contenu du dépôt

| Bloc | Sujet | Dossier / fichiers | Statut |
|---|---|---|---|
| 0 | Environnement (VM, Docker) | `docker-compose.yml` (racine) | ✅ |
| 1 | Application cible vulnérable | `juice-shop-src/` | ✅ |
| 2 | CI/CD — SAST / Secrets / SCA | `.github/workflows/` | ✅ |
| 3 | Conteneurisation & scan d'image | `Dockerfile`, `Dockerfile.distroless`, `Dockerfile.unhardened`, `docker/juice-shop/`, `trivy-*.json` / `trivy-image-report-*.txt` | ✅ |
| 4 | Tests dynamiques (DAST) | `zap-reports/` | ✅ |
| 5 | Sécurité Kubernetes | `k8s/` (kube-bench, Trivy k8s) | ✅ |
| 6 | Détection comportementale (EDR) | `wazuh-config/` | ✅ |
| 7 | Réponse à incident (SOAR) | `thehive-cortex/`, `wazuh-thehive-integration/` | ✅ |
| 8 | Dashboard centralisé & scoring | `dashboard/` | ✅ |
| 9 | Threat Intelligence & IaC *(optionnel)* | — | ⏸️ non réalisé (contrainte RAM de la VM) |

## Stack technique

- **Application cible** : OWASP Juice Shop (Node.js)
- **CI/CD** : GitHub Actions, Semgrep, Bandit, Gitleaks, Trivy
- **Conteneurs** : Docker, image durcie (utilisateur non-root, base slim)
- **DAST** : OWASP ZAP (baseline, fullscan, authentifié)
- **Kubernetes** : k3s, kube-bench (CIS Benchmark), Trivy k8s
- **EDR** : Wazuh (FIM temps réel, rootcheck)
- **SOAR** : TheHive, Cortex, webhook d'automatisation Wazuh → TheHive
- **Dashboard** : Flask (API), nginx, HTML/CSS/JS, WeasyPrint (export PDF)

## Dashboard — aperçu

Le dashboard (`dashboard/`) agrège en temps réel les résultats de tous les
outils (Trivy, ZAP, kube-bench, TheHive) en un score de sécurité pondéré,
avec une chronologie d'incidents en direct et un export PDF pour reporting.

Méthodologie de scoring détaillée dans `dashboard/api/report.py`.

## Démarrage

Voir [`SETUP.md`](./SETUP.md) pour reconstituer l'environnement complet
(la stack Wazuh officielle n'est pas versionnée ici, seuls les fichiers de
configuration modifiés le sont).

## Sécurité

Aucun secret n'est versionné dans ce dépôt — les clés API sont chargées
via variables d'environnement (`.env`, non commité). Voir `SETUP.md` pour
la configuration.

## Auteur

Abir Majdi — ENSA Fès, Génie du Développement Numérique & Cybersécurité
