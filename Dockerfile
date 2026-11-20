# Project Studio web server (serve.py + studio package). The voice stack runs in stack/domotica-voz.
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim
WORKDIR /app
COPY serve*.py ./
COPY studio ./studio
COPY catalog ./catalog
COPY examples ./examples
COPY modules ./modules
COPY connectors ./connectors
COPY stack ./stack
COPY web ./web
ENV STUDIO_HOST=0.0.0.0 STUDIO_DATA=/data STUDIO_SECRETS=/secrets PYTHONUNBUFFERED=1
EXPOSE 8765
CMD ["python", "serve.py", "--port", "8765"]
