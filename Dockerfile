FROM node:20-alpine AS frontend
WORKDIR /frontend
COPY app/frontend/package.json app/frontend/package-lock.json* ./
RUN npm install
COPY app/frontend/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /srv/backend
COPY app/backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY app/backend/ ./
COPY --from=frontend /frontend/dist /srv/frontend/dist
ENV MES_DEV=0
ENV MES_DATABASE_PATH=/data/database.db
ENV MES_BACKUP_DIR=/data/backups
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
