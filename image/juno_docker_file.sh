#!/bin/bash

tag="$1"
cd juno_server
git checkout $tag
git reset --hard FETCH_HEAD
git pull
cd -
image=hub.mobvista.com/as/juno:$tag
docker build -t $image -f junobuild.docker .
docker push $image

# cat junobuild.docker
FROM golang:1.14.0-alpine AS builder
WORKDIR /data/juno_server/
RUN apk add --no-cache git make openssh bash
RUN go env -w GOPRIVATE=gitlab.*.com
COPY gitinfo/.gitconfig /root/.gitconfig
COPY gitinfo/.ssh /root/.ssh
COPY juno_server /data/juno_server
RUN make build

FROM  alpine:3.9.5
WORKDIR /data/juno_server/
COPY --from=builder /data/juno_server/output /data/juno_server
COPY conf conf
COPY data data
RUN mkdir -p /data/model_update/model_from_rsync
RUN apk add tzdata && cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && echo "Asia/Shanghai" > /etc/timezone && apk del tzdata
ENTRYPOINT ["./bin/juno_server","serve"]




#!/bin/bash
host=`docker network inspect --format='{{range .IPAM.Config}}{{.Gateway}}{{end}}' bridge`
tag="$1"
[ "$tag" == "" ] && tag=`docker image ls|grep juno|head -n 1|awk '{print $2}'`
image=hub.mobvista.com/as/juno:$tag
echo "docker run --add-host=mongohost:$host --add-host=dmphost:$host --add-host=consulhost:$host  --add-host=redishost:$host -d $image"
#docker
containerId=`docker ps -a|grep juno_server|awk '{print $1}'`
[ "$containerId" != "" ] && docker stop $containerId && docker rm $containerId
sleep 1
docker pull $image
docker run --name=juno_server -v /data/recommend/juno/log:/data/juno_server/log -v /data/recommend/juno/data:/data/juno_server/data -p 12066:12066 -p 12077:12077 --add-host=mongohost:$host --add-host=dmphost:$host --add-host=consulhost:$host --add-host=redishost:$host -d $image