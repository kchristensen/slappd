FROM python:3.10-alpine
WORKDIR /tmp

COPY . .
RUN adduser -S slappd && \
    pip install --no-cache-dir --upgrade . && \
    rm -rf /tmp/*

USER slappd
ENTRYPOINT ["/usr/local/bin/slappd"]
