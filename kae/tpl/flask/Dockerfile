FROM python:3.6.6-alpine
MAINTAINER yuyang <yyangplus@gmail.com>

RUN mkdir -p /kae/app
ADD . /kae/app

WORKDIR /kae/app

RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.ustc.edu.cn/g' /etc/apk/repositories && \
apk update && \
apk add --no-cache alpine-sdk && \
pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt && \
apk del alpine-sdk

EXPOSE 5000

ENTRYPOINT ["gunicorn", "{{entrypoint}}", "-c", "gunicorn_config.py"]
