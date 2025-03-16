FROM python:3.12 AS base

ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONFAULTHANDLER=1

FROM base AS python-deps


RUN pip install pipenv
RUN apt-get update && apt-get install -y --no-install-recommends gcc

COPY Pipfile .
COPY Pipfile.lock .
RUN PIPENV_VENV_IN_PROJECT=1 pipenv install --deploy

FROM base AS runtime

COPY --from=python-deps /.venv /.venv
ENV PATH="/.venv/bin:$PATH"
ENV FLASK_APP=gamecafe:create_app

RUN useradd --create-home appuser

RUN mkdir /config
RUN chown -R appuser:appuser /config

RUN mkdir /data
RUN chown -R appuser:appuser /data

WORKDIR /home/appuser
USER appuser

COPY . .

EXPOSE 80
CMD ["/bin/sh", "/home/appuser/docker-entrypoint.sh"]
