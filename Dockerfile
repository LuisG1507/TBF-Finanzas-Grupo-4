FROM node:22-bookworm-slim AS frontend
WORKDIR /proyecto/frontend-ts
COPY frontend-ts/package.json frontend-ts/package-lock.json ./
RUN npm ci
COPY frontend-ts/ ./
RUN npm run build

FROM python:3.13-slim
WORKDIR /proyecto
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini ./
COPY --from=frontend /proyecto/frontend-ts/dist ./frontend-ts/dist
EXPOSE 8000
CMD ["sh", "-c", "exec python -m uvicorn app.web:app --host 0.0.0.0 --port \"${PORT:-8000}\""]
