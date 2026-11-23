# ---------------------------------------------------------------------------
# VYRALIS — one image: studio build + processing API.
#
# Stage 1 builds the Vite studio, stage 2 runs FastAPI and serves that build from
# the same origin. Same-origin matters: it keeps the studio's API calls free of
# CORS, lets the optional HTTP Basic gate protect the whole app, and means OAuth
# callbacks and downloads all live on one host.
# ---------------------------------------------------------------------------
FROM node:20-slim AS studio
WORKDIR /web
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY index.html vite.config.ts tsconfig.json tsconfig.app.json tsconfig.node.json ./
COPY postcss.config.js tailwind.config.js ./
COPY public ./public
COPY src ./src
RUN npm run build

FROM python:3.11-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    VYRALIS_DATA_DIR=/var/lib/vyralis \
    VYRALIS_WEB_DIR=/app/dist

# Debian's ffmpeg is built with libass, which the caption burn-in needs.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && ffmpeg -hide_banner -filters 2>/dev/null | grep -q " subtitles " \
    && echo "libass present" 

WORKDIR /app
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install -r /app/backend/requirements.txt
COPY backend /app/backend
COPY --from=studio /web/dist /app/dist

RUN mkdir -p /var/lib/vyralis
EXPOSE 8000

# Render terminates TLS; --proxy-headers makes redirect URLs and scheme detection correct.
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
