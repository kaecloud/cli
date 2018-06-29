FROM python:3.5.5-alpine
MAINTAINER yuyang <yyangplus@gmail.com>

RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.ustc.edu.cn/g' /etc/apk/repositories && \
apk update && \
apk add --no-cache git openssh && \
pip install git+https://github.com/kaecloud/cli.git@v0.0.1-alpha1
