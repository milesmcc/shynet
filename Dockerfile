FROM python:3-alpine

WORKDIR /usr/src/shynet
COPY Pipfile.lock Pipfile ./
COPY shynet .

RUN apk update && \
	apk add gettext curl bash && \
	# URL from https://github.com/shlinkio/shlink/issues/596 :)
	curl "https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-ASN&license_key=G4Lm0C60yJsnkdPi&suffix=tar.gz" | tar -xvz -C /tmp && \
	curl "https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-City&license_key=G4Lm0C60yJsnkdPi&suffix=tar.gz" | tar -xvz -C /tmp && \
	mv /tmp/GeoLite2*/*.mmdb /etc && \
	apk del curl && \
	apk add --no-cache postgresql-libs && \
	apk add --no-cache --virtual .build-deps gcc musl-dev postgresql-dev && \
	pip install pipenv && \
	pipenv install --system --deploy && \
	apk --purge del .build-deps && \
	rm -rf /var/lib/apt/lists/* && \
	rm /var/cache/apk/*

ARG GF_UID="500"
ARG GF_GID="500"

# add group & user
RUN python manage.py collectstatic --noinput && \
	python manage.py compilemessages && \
	addgroup --system -g $GF_GID appgroup && \
	adduser appuser --system --uid $GF_UID -G appgroup

USER appuser
EXPOSE 8080
ENTRYPOINT [ "./entrypoint.sh" ]
