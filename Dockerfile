FROM python:3.11-slim-bullseye

ENV DEBIAN_FRONTEND=noninteractive

# --- System deps + Build deps (bleiben bis nach pip install) ---
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg2 \
    apt-transport-https \
    ca-certificates \
    gcc \
    g++ \
    unixodbc \
    unixodbc-dev \
    && curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/11/prod bullseye main" \
        > /etc/apt/sources.list.d/microsoft-prod.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql17

# --- OpenSSL TLS workaround (SECLEVEL=2 -> 1) ---
RUN set -eux; \
    sed -i 's/^CipherString = DEFAULT@SECLEVEL=2/# CipherString = DEFAULT@SECLEVEL=2/' /etc/ssl/openssl.cnf || true; \
    grep -q '^openssl_conf *= *default_conf' /etc/ssl/openssl.cnf \
      || sed -i 's/^\(# *System default\)$/\1\nopenssl_conf = default_conf/' /etc/ssl/openssl.cnf; \
    grep -q '^\[system_default_sect\]' /etc/ssl/openssl.cnf || cat >> /etc/ssl/openssl.cnf <<'EOF'

[default_conf]
ssl_conf = ssl_sect

[ssl_sect]
system_default = system_default_sect

[system_default_sect]
MinProtocol = TLSv1
CipherString = DEFAULT@SECLEVEL=1
EOF

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- nach pip: Build deps entfernen + cleanup ---
RUN apt-get purge -y --auto-remove gcc g++ curl gnupg2 apt-transport-https \
    && rm -rf /var/lib/apt/lists/*

COPY app.py run.py config.py diagnose_db.py VERSION ./
COPY services/ ./services/
COPY utils/ ./utils/
COPY Excel/ ./Excel_base/

RUN mkdir -p logs data Excel

VOLUME ["/app/Excel"]
EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')" || exit 1

ENTRYPOINT ["streamlit", "run", "app.py", \
  "--server.headless=true", \
  "--server.address=0.0.0.0", \
  "--server.port=8501"]
