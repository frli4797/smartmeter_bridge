ARG BUILD_ARCH=amd64
ARG BUILD_FROM=ghcr.io/home-assistant/${BUILD_ARCH}-base-python:3.12
FROM ${BUILD_FROM}

WORKDIR /app

ARG BUILD_VERSION=dev

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV APP_VERSION=${BUILD_VERSION}
ENV HEALTH_STATUS_PATH=/tmp/smartmeter-faker-health.json
ENV HEALTHCHECK_MAX_AGE_SECONDS=30

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY modbus_bridge.py ./
COPY healthcheck.py ./
COPY run.sh /run.sh

RUN chmod a+x /run.sh

EXPOSE 5020

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD ["python", "healthcheck.py"]

CMD ["/run.sh"]
