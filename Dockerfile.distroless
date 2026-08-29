FROM node:22-slim AS build
WORKDIR /juice-shop
RUN apt-get -o Acquire::ForceIPv4=true update && apt-get -o Acquire::ForceIPv4=true install -y --no-install-recommends \
    python3 \
    make \
    g++ \
    && rm -rf /var/lib/apt/lists/*
COPY juice-shop-src/ .
RUN npm install --fetch-retries=5 --fetch-retry-mintimeout=20000 --fetch-retry-maxtimeout=120000
RUN npm run build:server
RUN npm prune --omit=dev
RUN rm -rf \
    frontend/node_modules \
    frontend/src \
    frontend/.angular \
    test \
    screenshots \
    terraform \
    infrastructure \
    vagrant \
    monitoring \
    .zap \
    .git \
    .github \
    .gitlab \
    .cursor \
    .claude \
    .codeium \
    .continue \
    .junie \
    .ai \
    .dependabot \
    .devcontainer.json \
    .gitlab-ci.yml \
    docker-compose.test.yml \
    cypress.config.ts \
    eslint.config.mjs \
    server.ts \
    app.ts \
    HALL_OF_FAME.md \
    CONTRIBUTING.md \
    SOLUTIONS.md \
    REFERENCES.md \
    CODE_OF_CONDUCT.md \
    README.md \
    .mailmap \
    .gitignore \
    .gitattributes \
    .npmrc \
    .codeclimate.yml \
    crowdin.yaml

RUN mkdir -p logs && chown -R 65532:65532 logs

FROM gcr.io/distroless/nodejs22-debian12
WORKDIR /juice-shop
COPY --from=build --chown=65532:65532 /juice-shop /juice-shop
USER 65532
EXPOSE 3000
CMD ["build/app.js"]
