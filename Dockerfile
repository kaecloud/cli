FROM python:3.5.5-alpine
MAINTAINER yuyang <yyangplus@gmail.com>

ADD . /tmp/kae
RUN cd /tmp/kae && \
    python setup.py install && \
    rm -rf /tmp/kae
