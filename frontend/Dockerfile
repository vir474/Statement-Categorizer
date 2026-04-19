FROM node:20-alpine AS builder

WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci

COPY . .
# VITE_API_URL is passed as build arg so the static bundle knows where to find the API
ARG VITE_API_URL=http://localhost
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

# Serve the built assets with nginx
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
# Simple nginx config for SPA routing (the main nginx.conf handles routing at the proxy level)
RUN echo 'server { listen 80; root /usr/share/nginx/html; location / { try_files $uri /index.html; } }' \
    > /etc/nginx/conf.d/default.conf
EXPOSE 80
