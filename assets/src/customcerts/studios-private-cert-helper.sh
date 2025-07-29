#!/usr/bin/env bash 
# studios-private-cert-helper.sh  <base‑image>  <cert‑file>  [new‑tag]  [alias]  [ecr‑uri]
#
# If you pass an ecr‑uri (e.g. 123456789012.dkr.ecr.eu-west-1.amazonaws.com/xpra:with-ca)
# the script will:
#   * docker‑login to the registry (AWS CLI required, creds pre‑configured)
#   * tag NEW_TAG → ECR_URI  (if NEW_TAG already *is* the ECR uri, tagging is skipped)
#   * push it
#
# ──────────────────────────────────────────────────────────────
#  Examples
# ──────────────────────────────────────────────────────────────
#  Keep local only:
#     ./studios-private-cert-helper.sh public.cr.seqera.io/platform/data-studio-xpra:6.2.0-r2-1-0.8 \
#                    ./PRIVATE_CERT.pem
#
#  Push to ECR:
#     ./studios-private-cert-helper.sh public.cr.seqera.io/platform/data-studio-xpra:6.2.0-r2-1-0.8 \
#                    ./PRIVATE_CERT.pem \
#                    seqera/xpra:with-ca \
#                    corp_ca \
#                    123456789012.dkr.ecr.eu-west-1.amazonaws.com/xpra:with-ca
#

set -euo pipefail
# ── positional args ──────────────────────────────────────────
BASE_IMAGE="${1:?Give the base image}"
CERT_PATH="${2:?Give the path to a PEM or CRT file}"
NEW_TAG="${3:-${BASE_IMAGE%%:*}-with-ca}"
ALIAS="${4:-custom_root_ca}"
ECR_URI="${5:-}"               # optional; full URI incl. tag

# ── staging dir ──────────────────────────────────────────────
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

CERT_NAME="custom-cert.crt"
cp "$CERT_PATH" "$TMP/$CERT_NAME"

cat >"$TMP/Dockerfile" <<'EOF'
ARG BASE
FROM ${BASE}
USER root
ARG CERT_NAME
ARG ALIAS
COPY "${CERT_NAME}" /usr/local/share/ca-certificates/
RUN set -e; \
    update-ca-certificates && \
    if command -v keytool >/dev/null 2>&1; then \
        keytool -import -trustcacerts -cacerts -storepass changeit -noprompt \
               -alias "${ALIAS}" \
               -file /usr/local/share/ca-certificates/"${CERT_NAME}" || true; \
    fi
EOF

echo "▶ Building $NEW_TAG ..."
docker build -q \
  --build-arg BASE="$BASE_IMAGE" \
  --build-arg CERT_NAME="$CERT_NAME" \
  --build-arg ALIAS="$ALIAS" \
  -t "$NEW_TAG" "$TMP"

echo "✔ Image built: $NEW_TAG"

# ── ECR push (optional) ──────────────────────────────────────
if [[ -n "$ECR_URI" ]]; then
  REGISTRY="${ECR_URI%%/*}"                # 123456789012.dkr.ecr.<region>.amazonaws.com
  IFS='.' read -ra _parts <<<"$REGISTRY"
  REGION="${_parts[3]}"
  echo "▶ Logging in to $REGISTRY ..."
  aws ecr get-login-password --region "${REGION}" | \
      docker login --username AWS --password-stdin "$REGISTRY"

  # tag only if NEW_TAG != ECR_URI
  if [[ "$NEW_TAG" != "$ECR_URI" ]]; then
    docker tag "$NEW_TAG" "$ECR_URI"
  fi

  echo "▶ Pushing $ECR_URI ..."
  docker push "$ECR_URI"
  echo "✔ Pushed to ECR."
fi

echo "🎉 Done."
