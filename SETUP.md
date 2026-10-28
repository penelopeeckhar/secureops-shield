# Reconstituer l'environnement SecureOps Shield

Ce dépôt ne contient pas les copies complètes des projets tiers
(OWASP Juice Shop, wazuh-docker) — seulement les fichiers que j'ai
personnellement modifiés. Voici comment reconstituer l'environnement complet.

## 1. Application cible (Bloc 1)
git clone https://github.com/juice-shop/juice-shop.git juice-shop-src
cp docker/juice-shop/Dockerfile.hardened juice-shop-src/Dockerfile


## 2. Stack Wazuh (Bloc 6)

git clone https://github.com/wazuh/wazuh-docker.git -b v4.9.2 wazuh-docker
cp wazuh-config/wazuh_manager.conf.example wazuh-docker/single-node/config/wazuh_cluster/wazuh_manager.conf


Puis éditer `wazuh_manager.conf` pour remplacer `YOUR_THEHIVE_API_KEY_HERE`
par la vraie clé API TheHive générée à l'étape suivante.

## 3. Secrets

Créer `dashboard/.env` :

THEHIVE_API_KEY=<clé générée dans TheHive>


## 3 bis. Variables d'environnement

- `CORTEX_API_KEY` : à définir dans `thehive-cortex/.env` (lue par `docker compose`).
  Copier `thehive-cortex/.env.example` en `thehive-cortex/.env` puis renseigner la valeur.
- `ZAP_AUTH_TOKEN` : jeton JWT Juice Shop utilisé par le plan ZAP authentifié
  (`zap-reports/zap-auth-plan.yaml`), à générer au moment du scan avec :

      export ZAP_AUTH_TOKEN=$(curl -s -X POST http://localhost:3000/rest/user/login -H 'Content-Type: application/json' -d '{"email":"zaptest@juice-sh.op","password":"<mot_de_passe_du_compte_test>"}' | jq -r .authentication.token)

- `THEHIVE_API_KEY` : dans `dashboard/.env`, voir la section 3 ci-dessus.

## 4. Lancer les stacks

Voir les `docker-compose.yml` de chaque dossier (`thehive-cortex/`,
`wazuh-docker/single-node/`, `dashboard/`) et les lancer dans l'ordre :
Bloc 0 → 1 → 6 → 7 → 8.
