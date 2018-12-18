# 先build静态文件
FROM node:10-alpine as nodebuilder
RUN mkdir -p /kae/app
ADD . /kae/app

WORKDIR /kae/app
RUN npm config set registry http://registry.cnpmjs.org && \
    npm install && \
    npm run build

# 通过node来运行
FROM node:10-alpine as nodebuilder
RUN mkdir -p /kae/app

ADD . /kae/app

WORKDIR /kae/app
# 将build得到的文件从构建容器拷贝出来
COPY --from=nodebuilder /kae/app/dist ./dist

CMD ["npm", "start"]
