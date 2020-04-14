FROM python:3

WORKDIR /usr/src/shynet

RUN apt update
RUN apt install -y gettext

# URL from https://github.com/shlinkio/shlink/issues/596 :)
RUN curl "https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-ASN&license_key=G4Lm0C60yJsnkdPi&suffix=tar.gz" | tar -xvz -C /tmp
RUN curl "https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-City&license_key=G4Lm0C60yJsnkdPi&suffix=tar.gz" | tar -xvz -C /tmp
RUN mv /tmp/GeoLite2*/*.mmdb /etc

RUN pip install pipenv
COPY Pipfile.lock ./
COPY Pipfile ./
RUN pipenv install --system --deploy

COPY shynet .
RUN python manage.py collectstatic --noinput
RUN python manage.py compilemessages

ARG GF_UID="500"
ARG GF_GID="500"

# add group & user
RUN groupadd -r -g $GF_GID appgroup && \
   useradd appuser -r -u $GF_UID -g appgroup

USER appuser

EXPOSE 8080

CMD [ "./webserver.sh" ]