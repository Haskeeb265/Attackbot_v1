FROM python:3.12-slim

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
COPY requirements/base.txt /app/requirements/base.txt
RUN pip install --no-cache-dir -r /app/requirements/base.txt
# Install Go-based security tools
RUN apt-get update && apt-get install -y wget unzip curl && \
    wget -q https://github.com/projectdiscovery/nuclei/releases/latest/download/nuclei_linux_amd64.zip && \
    unzip -q nuclei_linux_amd64.zip && mv nuclei /usr/local/bin/ && rm nuclei_*.zip && \
    wget -q https://github.com/projectdiscovery/httpx/releases/latest/download/httpx_linux_amd64.zip && \
    unzip -q httpx_linux_amd64.zip && mv httpx /usr/local/bin/ && rm httpx_*.zip && \
    wget -q https://github.com/projectdiscovery/subfinder/releases/latest/download/subfinder_linux_amd64.zip && \
    unzip -q subfinder_linux_amd64.zip && mv subfinder /usr/local/bin/ && rm subfinder_*.zip && \
    wget -q https://github.com/projectdiscovery/dnsx/releases/latest/download/dnsx_linux_amd64.zip && \
    unzip -q dnsx_linux_amd64.zip && mv dnsx /usr/local/bin/ && rm dnsx_*.zip && \
    wget -q https://github.com/projectdiscovery/alterx/releases/latest/download/alterx_linux_amd64.zip && \
    unzip -q alterx_linux_amd64.zip && mv alterx /usr/local/bin/ && rm alterx_*.zip && \
    wget -q https://github.com/ffuf/ffuf/releases/latest/download/ffuf_linux_amd64.tar.gz && \
    tar xzf ffuf_linux_amd64.tar.gz && mv ffuf /usr/local/bin/ && rm ffuf_*.tar.gz && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Nuclei templates
RUN nuclei -update-templates || true

# ffuf wordlist
RUN mkdir -p /wordlists && \
    wget -q https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/Web-Content/common.txt \
    -O /wordlists/common.txt

COPY backend/shared /app/backend/shared
COPY backend/__init__.py /app/backend/__init__.py
COPY backend/services/__init__.py /app/backend/services/__init__.py
COPY backend/services/core_engine /app/backend/services/core_engine

ENV PYTHONPATH=/app

EXPOSE 8002

CMD ["uvicorn", "backend.services.core_engine.main:app", "--host", "0.0.0.0", "--port", "8002"]