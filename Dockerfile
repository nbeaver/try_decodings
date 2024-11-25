FROM python:3.8-alpine

LABEL org.opencontainers.image.title="try_decodings" \
      org.opencontainers.image.description="Test-fit various ASCII<->binary encodings." \
      org.opencontainers.image.licenses="MIT"

ENV PYTHONIOENCODING=utf-8

VOLUME /in

COPY . /try_decodings

#ENTRYPOINT [ "/bin/sh", "/try_decodings/docker/docker-entrypoint.sh" ]
ENTRYPOINT [ "/bin/sh" ]
