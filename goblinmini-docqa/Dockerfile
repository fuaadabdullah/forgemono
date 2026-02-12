FROM python:3.11-slim

RUN useradd -m -u 1001 goblin
WORKDIR /home/goblin/app

COPY pyproject.toml /home/goblin/app/
RUN pip install --no-cache-dir -U pip setuptools wheel && \
  pip install --no-cache-dir fastapi uvicorn pydantic requests redis python-dotenv jinja2

COPY app /home/goblin/app/app
RUN chown -R goblin:goblin /home/goblin/app

USER goblin
ENV DOCQA_TOKEN=""
ENV REDIS_URL=redis://localhost:6379/0
CMD ["uvicorn", "app.server:app", "--host", "0.0.0.0", "--port", "9000", "--workers", "1"]
