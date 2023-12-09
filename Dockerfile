FROM python:alpine3.14

# Getting things ready
WORKDIR /usr/src/shynet

# Install dependencies & configure machine
ARG GF_UID="500"
ARG GF_GID="500"
RUN apk update && \
	apk add --no-cache gettext bash npm postgresql-libs && \
	test "$(arch)" != "x86_64" && apk add libffi-dev rust cargo || echo "amd64 build, skipping Rust installation"
	# libffi-dev and rust are used for the cryptography package,
	# which we indirectly rely on. Necessary for aarch64 support.

# MaxMind scans GitHub for exposed license keys and deactivates them. This
# (encoded) license key is intened to be public; it is not configured with any
# billing, and can only access MaxMind's public databases. These databases used
# to be available for download without authentication, but they are now auth
# gated. It is very important that the Shynet community have a simple,
# easily-pullable Docker image with all "batteries included." As a result, we
# intentionally "expose" this API key to the community. The "fix" is for MaxMind
# to offer these free, public datasets in a way that doesn't require an API key.
ARG MAXMIND_LICENSE_KEY_BASE64="Z2tySDgwX1htSEtmS3d4cDB1SnlMWTdmZ1hMMTQxNzRTQ2o5X21taw=="

RUN echo $MAXMIND_LICENSE_KEY_BASE64 > .mmdb_key

# Collect GeoIP Database
RUN apk add --no-cache curl && \
	curl -m 180 "https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-ASN&license_key=$(base64 -d .mmdb_key)&suffix=tar.gz" | tar -xvz -C /tmp && \
	curl -m 180 "https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-City&license_key=$(base64 -d .mmdb_key)&suffix=tar.gz" | tar -xvz -C /tmp && \
	mv /tmp/GeoLite2*/*.mmdb /etc && \
	apk --purge del curl

# Move dependency files
COPY poetry.lock pyproject.toml ./
COPY package.json package-lock.json ../
# Django expects node_modules to be in its parent directory.

# Install more dependencies and cleanup build dependencies afterwards
RUN apk add --no-cache --virtual .build-deps gcc musl-dev postgresql-dev libressl-dev libffi-dev && \
	npm i -P --prefix .. && \
	pip install poetry==1.2.2 && \
	poetry config virtualenvs.create false && \
	poetry run pip install "Cython<3.0" "pyyaml==5.4.1" --no-build-isolation && \
	poetry install --no-dev --no-interaction --no-ansi && \
	apk --purge del .build-deps

# Setup user group
RUN addgroup --system -g $GF_GID appgroup && \
	adduser appuser --system --uid $GF_UID -G appgroup && \
	mkdir -p /var/local/shynet/db/ && \
	chown -R appuser:appgroup /var/local/shynet

# Install Shynet
COPY shynet .
RUN python manage.py collectstatic --noinput && \
	python manage.py compilemessages

# Launch
USER appuser
EXPOSE 8080
HEALTHCHECK CMD bash -c 'wget -o /dev/null -O /dev/null --header "Host: ${ALLOWED_HOSTS%%,*}" "http://127.0.0.1:${PORT:-8080}/healthz/?format=json"'
CMD [ "./entrypoint.sh" ]
