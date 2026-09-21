# Dev-parity image for docker-compose (source is bind-mounted over /app).
# For production, switch to: npm run build && CMD ["npm", "start"]
FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .

EXPOSE 3000
CMD ["npm", "run", "dev"]