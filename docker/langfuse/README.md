# Local Langfuse

This folder is intended for the official Langfuse v3 Docker Compose file.

Use the upstream file when you are ready to run the full local stack:

```bash
curl -L https://raw.githubusercontent.com/langfuse/langfuse/main/docker-compose.yml -o docker-compose.yml
cp .env.example .env
docker compose up -d
```

Langfuse v3 uses web and worker containers plus Postgres, ClickHouse, Redis, and MinIO. Keep all generated secrets local and replace the placeholder values before sharing this setup.
