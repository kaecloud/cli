FROM golang:1.11-alpine as builder
ADD . /src
RUN cd /src && go build -o app


FROM alpine:latest
RUN apk --no-cache add ca-certificates && \
    mkdir -p /kae/app

WORKDIR /kae/app

COPY --from=builder /src/app .

CMD ["app"]
