FROM node:20-alpine

WORKDIR /app

# Allow overriding registry and timeouts (useful behind proxies/mirrors)
ARG NPM_REGISTRY=https://registry.npmjs.org/
ENV NPM_CONFIG_REGISTRY=${NPM_REGISTRY} \
    NPM_CONFIG_FETCH_TIMEOUT=60000 \
    NPM_CONFIG_FETCH_RETRIES=3

COPY package.json package-lock.json* ./
RUN npm install

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "--port", "5173"]
