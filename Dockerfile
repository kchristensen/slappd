FROM python:3.11-alpine
WORKDIR /tmp

LABEL org.opencontainers.image.source https://github.com/kchristensen/slappd

COPY . .
RUN adduser -S slappd && \
    pip install --no-cache-dir --upgrade . && \
    rm -rf /tmp/*

USER slappd
ENTRYPOINT ["/usr/local/bin/slappd"]
