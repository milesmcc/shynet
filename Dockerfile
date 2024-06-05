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
COPY assets/GeoLite2-ASN_20191224.tar.gz GeoLite2-ASN.tar.gz
COPY assets/GeoLite2-City_20191224.tar.gz GeoLite2-City.tar.gz
RUN apk add --no-cache curl && \
	tar -xvz -C /tmp < GeoLite2-ASN.tar.gz && \
	tar -xvz -C /tmp < GeoLite2-City.tar.gz && \
	mv /tmp/GeoLite2*/*.mmdb /etc && \
	rm GeoLite2-ASN.tar.gz GeoLite2-City.tar.gz && \
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
	poetry run pip install "Cython<3.0" "pyyaml==5.4.1" "django-allauth==0.45.0" --no-build-isolation && \
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
