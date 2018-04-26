FROM python:3.6-alpine
WORKDIR /tmp

COPY . .
RUN adduser -S slappd && \
    pip install --upgrade . && \
    rm -rf /tmp/*

USER slappd
ENTRYPOINT ["/usr/local/bin/slappd"]