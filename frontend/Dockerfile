FROM node:20 as build

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

# No need to remove build-time only dependencies as we use a full node image
# and the build stage is discarded in the final image anyway.

COPY . .
RUN npm run build

# Development Stage
FROM build as dev
CMD ["npm", "run", "dev", "--", "--host"]

# Production Stage
FROM nginx:alpine

# Security Gate: Run as non-root
# Configure nginx to run as non-root
RUN touch /var/run/nginx.pid && \
    chown -R nginx:nginx /var/run/nginx.pid && \
    chown -R nginx:nginx /var/cache/nginx && \
    chown -R nginx:nginx /etc/nginx/conf.d

COPY --from=build /app/dist /usr/share/nginx/html

# Update default config to listen on 8080 (non-privileged)
RUN sed -i 's/listen       80;/listen       8080;/g' /etc/nginx/conf.d/default.conf

USER nginx

EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
