# syntax=docker/dockerfile:1.7
ARG BUILD_FROM
FROM ${BUILD_FROM}

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV HEALTH_STATUS_PATH=/tmp/smartmeter-faker-health.json
ENV HEALTHCHECK_MAX_AGE_SECONDS=30

RUN apk add --no-cache python3 py3-pip

COPY requirements.txt ./
RUN --mount=type=cache,target=/root/.cache/pip \
    pip3 install --break-system-packages -r requirements.txt

ARG BUILD_VERSION=dev
ENV APP_VERSION=${BUILD_VERSION}

COPY modbus_bridge.py ./
COPY healthcheck.py ./
COPY run.sh /run.sh

RUN chmod a+x /run.sh

EXPOSE 5020

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD ["python3", "healthcheck.py"]

CMD ["/run.sh"]
