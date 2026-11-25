# Demo web sistem tanya jawab akademik FILKOM.
# Build dari root repositori: docker build -t pba-filkom-demo .
# Jalankan: docker run --rm -p 7860:7860 pba-filkom-demo
FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-install-project

COPY . .
RUN uv sync --locked

# Unduh model UDPipe saat build agar demo tidak bergantung jaringan saat presentasi.
RUN /app/.venv/bin/python -c "import spacy_udpipe; spacy_udpipe.download('id')"

ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 7860

CMD ["uvicorn", "web.app:app", "--host", "0.0.0.0", "--port", "7860"]
