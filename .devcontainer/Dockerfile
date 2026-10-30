FROM mcr.microsoft.com/devcontainers/python:3.11-bookworm


COPY cert.crt /usr/local/share/ca-certificates/zscaler-root-ca.crt
RUN update-ca-certificates

ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
ENV PIP_CERT=/etc/ssl/certs/ca-certificates.crt
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt


RUN apt-get update\
    && apt-get install -y --no-install-recommends libgl1 curl unzip \
    && curl -fsSL https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip -o /tmp/awscliv2.zip \
    && unzip -q /tmp/awscliv2.zip -d /tmp/awscli-install \
    && /tmp/awscli-install/aws/install \
    && rm -rf /tmp/awscli-install /tmp/awscliv2.zip /var/lib/apt/lists/*