ARG PYTHON_VERSION=3.15

# ---------------------------------------------------------------------------
# GeoIP databases
# ---------------------------------------------------------------------------
FROM alpine:3 AS geoip
COPY assets/GeoLite2-ASN_20191224.tar.gz assets/GeoLite2-City_20191224.tar.gz /tmp/
RUN mkdir /geoip && \
	tar -xz -C /tmp -f /tmp/GeoLite2-ASN_20191224.tar.gz && \
	tar -xz -C /tmp -f /tmp/GeoLite2-City_20191224.tar.gz && \
	mv /tmp/GeoLite2*/*.mmdb /geoip/

# ---------------------------------------------------------------------------
# Build stage: compilers, npm and poetry live only here
# ---------------------------------------------------------------------------
FROM python:${PYTHON_VERSION}-alpine AS build

WORKDIR /usr/src/shynet

RUN apk add --no-cache gcc musl-dev postgresql-dev libffi-dev gettext npm

# Python dependencies into an isolated venv which is copied to the runtime image
ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY poetry.lock pyproject.toml ./
RUN pip install --no-cache-dir poetry==2.5.2 && \
	poetry install --only main --no-root --no-interaction --no-ansi

# Frontend packages. Django expects node_modules in the parent directory.
COPY package.json package-lock.json ../
RUN npm ci --omit=dev --prefix ..

# Shynet itself: collect static files and compile translations
COPY shynet .
RUN python manage.py collectstatic --noinput && \
	python manage.py compilemessages

# ---------------------------------------------------------------------------
# Runtime stage
# ---------------------------------------------------------------------------
FROM python:${PYTHON_VERSION}-alpine

ARG GF_UID="500"
ARG GF_GID="500"

RUN apk add --no-cache bash postgresql-libs && \
	addgroup --system -g $GF_GID appgroup && \
	adduser appuser --system --uid $GF_UID -G appgroup && \
	mkdir -p /var/local/shynet/db/ && \
	chown -R appuser:appgroup /var/local/shynet

ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV PYTHONUNBUFFERED=1

WORKDIR /usr/src/shynet

COPY --from=geoip /geoip/*.mmdb /etc/
COPY --from=build /opt/venv /opt/venv
COPY --from=build /usr/src/shynet .

USER appuser
EXPOSE 8080
HEALTHCHECK CMD bash -c 'H="${ALLOWED_HOSTS:-localhost}"; wget -o /dev/null -O /dev/null --header "Host: ${H%%,*}" "http://127.0.0.1:${PORT:-8080}/healthz/?format=json"'
CMD [ "./entrypoint.sh" ]
