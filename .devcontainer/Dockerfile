# [Choice] Python version: 3, 3.9, 3.8, 3.7, 3.6
ARG VARIANT="3.8"
FROM mcr.microsoft.com/vscode/devcontainers/python:0-${VARIANT}

# [Optional] Uncomment this section to install additional OS packages.
RUN wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
RUN sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt/ bullseye-pgdg main" >> /etc/apt/sources.list.d/postgresql.list'
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends postgresql-13-postgis-3 sqlite3 libgdal-dev libproj-dev libsqlite3-dev spatialite-bin libsqlite3-mod-spatialite

ENV PEPYS_SPATIALITE_PATH=/usr/lib/x86_64-linux-gnu/mod_spatialite.so
ENV SQLALCHEMY_WARN_20=1