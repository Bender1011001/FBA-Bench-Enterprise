FROM node:20-alpine

WORKDIR /app

COPY package*.json ./

RUN npm ci

COPY . .

RUN addgroup -S app && adduser -S -G app app
RUN chown -R app:app /app
USER app

EXPOSE 5173

CMD ["npm", "run", "dev"]