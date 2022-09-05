FROM node:16-alpine AS frontend

WORKDIR /static

RUN apk update
RUN apk add openssh-client git
RUN ssh-keyscan github.com >> /root/.ssh/known_hosts
RUN --mount=type=ssh git clone git@github.com:ndawn/edge_auctions_client.git .

RUN npm install -g yarn
RUN yarn
RUN yarn build

FROM nginx

WORKDIR /static

COPY --from=frontend /static /static
COPY ./static.conf /etc/nginx/conf.d/default.conf

CMD ["nginx", "-g", "daemon off;"]
