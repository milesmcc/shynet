FROM python:alpine3.14

# Getting things ready
WORKDIR /usr/src/shynet

# Install dependencies & configure machine
ARG GF_UID="500"
ARG GF_GID="500"
RUN apk update && \
	apk add gettext curl bash npm libffi-dev rust cargo
	# libffi-dev and rust are used for the cryptography package,
	# which we indirectly rely on. Necessary for aarch64 support.

# Collect GeoIP Database
RUN curl -m 180 "https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-ASN&license_key=kKG1ebhL3iWVd0iv&suffix=tar.gz" | tar -xvz -C /tmp && \
	curl -m 180 "https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-City&license_key=kKG1ebhL3iWVd0iv&suffix=tar.gz" | tar -xvz -C /tmp && \
	mv /tmp/GeoLite2*/*.mmdb /etc && \
	apk del curl

# Move dependency files
COPY poetry.lock pyproject.toml ./
COPY package.json package-lock.json ../
# Django expects node_modules to be in its parent directory.

# Install more dependencies
RUN apk add --no-cache postgresql-libs && \
	apk add --no-cache --virtual .build-deps gcc musl-dev postgresql-dev && \
	npm i -P --prefix .. && \
	pip install poetry==1.1.7

# Install Python dependencies
RUN poetry config virtualenvs.create false && \
    poetry install --no-dev --no-interaction --no-ansi

# Cleanup dependencies & setup user group
RUN apk --purge del .build-deps && \
	rm -rf /var/lib/apt/lists/* && \
	rm /var/cache/apk/* && \
	addgroup --system -g $GF_GID appgroup && \
	adduser appuser --system --uid $GF_UID -G appgroup

# Install Shynet
COPY shynet .
RUN python manage.py collectstatic --noinput && \
	python manage.py compilemessages

# Launch
USER appuser
EXPOSE 8080
HEALTHCHECK CMD bash -c 'wget -o /dev/null -O /dev/null --header "Host: ${ALLOWED_HOSTS%%,*}" "http://127.0.0.1:$PORT/healthz/?format=json"'
CMD [ "./entrypoint.sh" ]
