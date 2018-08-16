FROM python:3.5.5-alpine
MAINTAINER yuyang <yyangplus@gmail.com>

ADD . /tmp/kae
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.ustc.edu.cn/g' /etc/apk/repositories && \
    apk update && \
    apk add --no-cache git openssh && \
    cd /tmp/kae && \
    python setup.py install && \
    rm -rf /tmp/kae
