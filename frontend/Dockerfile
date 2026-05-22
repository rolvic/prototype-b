FROM nginx:1.27-alpine
ENV PORT=8080 \
    BACKEND_URL=http://localhost:8000 \
    BACKEND_HOST=localhost
COPY nginx.conf /etc/nginx/templates/default.conf.template
COPY index.html /usr/share/nginx/html/index.html
EXPOSE 8080
