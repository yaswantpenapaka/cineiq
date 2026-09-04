FROM python:3.11-slim-bookworm

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# scikit-surprise is compiled during the image build; curl is used by Compose
# health checks.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install "Cython<3" "numpy==1.24.3" \
    && pip install -r requirements.txt

# Only inference code and its required artifacts belong in the serving image.
COPY src ./src
COPY api ./api
COPY app ./app
COPY data/merged_movies.csv ./data/merged_movies.csv
COPY data/movielens/ratings.csv ./data/movielens/ratings.csv
COPY models/svd_model.pkl ./models/svd_model.pkl

RUN mkdir -p feedback

EXPOSE 8000 8501

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
