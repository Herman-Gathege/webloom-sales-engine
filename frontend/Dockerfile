# Build the SPA, then serve the built files with Nginx.
#
# The browser only ever talks to Nginx: it serves the app at / and proxies
# /api to the API container. That means no CORS to configure, and the client's
# default VITE_API_BASE_URL of "/api/v1" is exactly right — so we do not bake a
# hostname into the bundle.

FROM node:22-alpine AS build

WORKDIR /app

# Copy the manifests first so `npm ci` is cached until dependencies change.
COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:1.27-alpine AS serve

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=5 \
  CMD wget --spider -q http://127.0.0.1/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
