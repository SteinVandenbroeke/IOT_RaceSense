# ==========================================
# STAGE 1: Builder
# ==========================================
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files and install dependencies
COPY package*.json ./
RUN npm ci

# Copy the rest of your SvelteKit code
COPY . .

RUN npm run build

# ==========================================
# STAGE 2: Runner
# ==========================================
FROM node:20-alpine

WORKDIR /app

# Copy ONLY the built files and node_modules from the builder
COPY --from=builder /app/build build/
COPY --from=builder /app/node_modules node_modules/
COPY package.json .

# Expose port 3000
EXPOSE 3000
ENV NODE_ENV=production

# Run the compiled Node app
CMD ["node", "build"]