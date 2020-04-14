FROM python:3

WORKDIR /usr/src/shynet

RUN pip install pipenv
COPY Pipfile.lock ./
COPY Pipfile ./
RUN pipenv install --system --deploy

COPY shynet .
RUN python manage.py collectstatic --noinput

ARG GF_UID="500"
ARG GF_GID="500"

# add group & user
RUN groupadd -r -g $GF_GID appgroup && \
   useradd appuser -r -u $GF_UID -g appgroup

USER appuser

EXPOSE 8080

CMD [ "./webserver.sh" ]