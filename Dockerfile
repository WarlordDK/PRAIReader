FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    poppler-utils \
    libjpeg-dev \
    libopenjp2-7-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libtiff5-dev \
    libpng-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]