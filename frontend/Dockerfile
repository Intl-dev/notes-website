FROM node:20-slim
WORKDIR /app
COPY . .
RUN npm install -g http-server
EXPOSE 3000
CMD ["http-server", ".", "-p", "3000", "--cors"]
ENV PORT=3000
EXPOSE 3000