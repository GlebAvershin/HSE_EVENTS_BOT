# Stage 1: Build the React SPA
FROM node:20-alpine AS builder

WORKDIR /app

# Accept API URL as build arg
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=${VITE_API_URL}

# Install dependencies
COPY admin-panel/package.json admin-panel/package-lock.json* ./
RUN npm ci

# Copy source and build
COPY admin-panel/ .
RUN npm run build

# Stage 2: Serve with Nginx
FROM nginx:alpine

# Copy custom nginx config
COPY docker/nginx-admin.conf /etc/nginx/conf.d/default.conf

# Copy built assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
