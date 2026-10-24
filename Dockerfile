FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl \
    && curl -kfsSL https://gu-st.ru/content/lending/russian_trusted_root_ca_pem.crt \
       -o /usr/local/share/ca-certificates/russian_trusted_root_ca.crt \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/*
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
