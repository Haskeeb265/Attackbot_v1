FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
COPY requirements/base.txt /app/requirements/base.txt
RUN pip install --no-cache-dir -r /app/requirements/base.txt

# Install Go-based security tools — pinned versions (no /latest/ redirect)
RUN apt-get update && apt-get install -y wget unzip curl ca-certificates && \
    wget -q https://github.com/projectdiscovery/nuclei/releases/download/v3.3.9/nuclei_3.3.9_linux_amd64.zip && \
    unzip -q nuclei_3.3.9_linux_amd64.zip nuclei && mv nuclei /usr/local/bin/ && rm nuclei_3.3.9_linux_amd64.zip && \
    wget -q https://github.com/projectdiscovery/httpx/releases/download/v1.6.10/httpx_1.6.10_linux_amd64.zip && \
    unzip -q httpx_1.6.10_linux_amd64.zip httpx && mv httpx /usr/local/bin/ && rm httpx_1.6.10_linux_amd64.zip && \
    wget -q https://github.com/projectdiscovery/subfinder/releases/download/v2.6.6/subfinder_2.6.6_linux_amd64.zip && \
    unzip -q subfinder_2.6.6_linux_amd64.zip subfinder && mv subfinder /usr/local/bin/ && rm subfinder_2.6.6_linux_amd64.zip && \
    wget -q https://github.com/projectdiscovery/dnsx/releases/download/v1.2.1/dnsx_1.2.1_linux_amd64.zip && \
    unzip -q dnsx_1.2.1_linux_amd64.zip dnsx && mv dnsx /usr/local/bin/ && rm dnsx_1.2.1_linux_amd64.zip && \
    wget -q https://github.com/projectdiscovery/alterx/releases/download/v0.0.4/alterx_0.0.4_linux_amd64.zip && \
    unzip -q alterx_0.0.4_linux_amd64.zip alterx && mv alterx /usr/local/bin/ && rm alterx_0.0.4_linux_amd64.zip && \
    wget -q https://github.com/ffuf/ffuf/releases/download/v2.1.0/ffuf_2.1.0_linux_amd64.tar.gz && \
    tar xzf ffuf_2.1.0_linux_amd64.tar.gz ffuf && mv ffuf /usr/local/bin/ && rm ffuf_2.1.0_linux_amd64.tar.gz && \
    wget -q https://github.com/tomnomnom/waybackurls/releases/download/v0.1.0/waybackurls-linux-amd64-0.1.0.tgz && \
    tar xzf waybackurls-linux-amd64-0.1.0.tgz waybackurls && mv waybackurls /usr/local/bin/ && rm waybackurls-linux-amd64-0.1.0.tgz && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Nuclei templates
RUN nuclei -update-templates || true

# ffuf wordlist
RUN mkdir -p /wordlists && \
    wget -q https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/Web-Content/common.txt \
    -O /wordlists/common.txt
COPY wordlists/e2e_tiny.txt /wordlists/e2e_tiny.txt

COPY backend/shared /app/backend/shared
COPY backend/__init__.py /app/backend/__init__.py
COPY backend/services/__init__.py /app/backend/services/__init__.py
COPY backend/services/core_engine /app/backend/services/core_engine
ENV PYTHONPATH=/app

# Non-root user for Celery worker (avoids SecurityWarning when running as root)
RUN groupadd --gid 1000 appuser && useradd --uid 1000 --gid 1000 --create-home appuser && chown -R appuser:appuser /app

EXPOSE 8002
USER appuser
CMD ["uvicorn", "backend.services.core_engine.main:app", "--host", "0.0.0.0", "--port", "8002"]
