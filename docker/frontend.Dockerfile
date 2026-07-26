# --- Development Stage ---
FROM node:20-alpine AS development

WORKDIR /app

# Copy package configuration
COPY frontend/package.json frontend/package-lock.json* /app/

# Install node dependencies
RUN npm install

# Copy application files
COPY frontend /app

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]


# --- Builder Stage ---
FROM node:20-alpine AS builder

WORKDIR /app

COPY frontend/package.json frontend/package-lock.json* /app/
RUN npm install --frozen-lockfile || npm install

COPY frontend /app
RUN npm run build


# --- Production Stage ---
FROM nginx:1.25-alpine AS production

COPY --from=builder /app/dist /usr/share/nginx/html
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
