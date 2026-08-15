ARG MODE=release

FROM python:3.13-slim AS base

COPY . /app
WORKDIR /app

RUN pip install --no-cache-dir -e .

FROM base AS dev
ENTRYPOINT ["fastapi", "dev", "src/nr5103e_manager/main.py", "--port", "16080", "--reload"]

FROM base AS release
ENTRYPOINT ["uvicorn", "nr5103e_manager.main:app", "--host", "0.0.0.0", "--port", "16080"]

FROM ${MODE} AS final