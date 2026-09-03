FROM mcr.microsoft.com/devcontainers/python:3.11-bookworm

COPY cert.crt /usr/local/share/ca-certificates/zscaler-root-ca.crt
RUN update-ca-certificates

ENV SSL_CERT_FILE=/ect/ssl/certs/ca-certificates.crt
ENV PIP_CERT=/etc/ssl/certs/ca-certificates.crt
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt