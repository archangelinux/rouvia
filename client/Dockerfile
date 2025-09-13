# Stage 1: Install dependencies
FROM node:18-alpine AS deps
WORKDIR /app
COPY client/package.json client/package-lock.json* ./
RUN npm ci

# Stage 2: Build the Next.js application
FROM node:18-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY client/ .
RUN npm run build

# Stage 3: Run the Next.js application
FROM node:18-alpine AS runner
WORKDIR /app

# Set environment variables for Next.js standalone output
ENV NODE_ENV production

# Create a non-root user
RUN addgroup --system --gid 1001 nextjs
RUN adduser --system --uid 1001 nextjs
USER nextjs

# Copy the standalone output from the builder stage
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

EXPOSE 3000

ENV PORT 3000

CMD ["node", "server.js"]
