# Simple Dockerfile for Streamlit app
ARG INSTALL_WEASYPRINT=false
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Install system dependencies optionally needed by weasyprint
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    libpango-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libcairo2 \
    libffi-dev \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

# Optionally install WeasyPrint if requested at build time
RUN if [ "${INSTALL_WEASYPRINT}" = "true" ]; then pip install weasyprint; fi

# Copy app code
COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "streamlit_app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
