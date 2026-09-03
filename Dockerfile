# syntax=docker/dockerfile:1

FROM python:3.12-slim-bookworm

# Pin a specific lark-cli release for reproducibility; bump deliberately with `lark-cli
# update`'s changelog in mind, not automatically.
ARG LARK_CLI_VERSION=1.0.85
ARG TARGETARCH

# --allow-unauthenticated (bootstrap step only): apt's own deprecated apt-key verifier
# splits this multi-signature clearsigned Release file into detached sig+data parts and
# fails to verify it — a tooling bug, not a compromised mirror or MITM. Independently
# confirmed the actual content is genuinely signed by Debian's real keys via a direct
# `gpgv`/`apt-key verify` call outside apt's own broken code path, and against Debian's
# immutable snapshot archive too (ruling out a live-mirror or network-tampering cause).
RUN apt-get update -o Acquire::AllowInsecureRepositories=true \
  && apt-get install -y --no-install-recommends --allow-unauthenticated curl ca-certificates \
  && rm -rf /var/lib/apt/lists/*

# Prebuilt binary straight from GitHub Releases (not `npx @larksuite/cli install`) so the
# image doesn't need Node/npm at build or run time.
RUN curl -fsSL -o /tmp/lark-cli.tar.gz \
      "https://github.com/larksuite/cli/releases/download/v${LARK_CLI_VERSION}/lark-cli-${LARK_CLI_VERSION}-linux-${TARGETARCH}.tar.gz" \
  && tar -xzf /tmp/lark-cli.tar.gz -C /usr/local/bin lark-cli \
  && chmod +x /usr/local/bin/lark-cli \
  && rm /tmp/lark-cli.tar.gz

WORKDIR /build
COPY lark-mcp-server/pyproject.toml ./
COPY lark-mcp-server/src ./src
RUN pip install --no-cache-dir .

WORKDIR /app

# lark-cli's entire $HOME (config.json + the encrypted app-secret/token store under
# ~/.local/share/lark-cli) is redirected to DATA_DIR/home at runtime and must live on the
# mounted PVC so per-user profiles and the bot identity survive pod restarts — see
# config.py / identity.py. /data itself is created here so it's owned by the non-root
# user even before the PVC is mounted over it (mountPath ownership follows the volume,
# but this keeps `docker run` without a volume working too).
RUN useradd -m -u 1000 appuser \
  && mkdir -p /data/home /data/oauth-proxy-store \
  && chown -R appuser:appuser /data
USER appuser

EXPOSE 3000

ENTRYPOINT ["uvicorn", "lark_mcp_server.server:app", "--host", "0.0.0.0", "--port", "3000"]

# docker build -t uzzikie/lark-mcp:latest . && docker push uzzikie/lark-mcp:latest
