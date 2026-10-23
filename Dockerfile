FROM python:3.12-slim
WORKDIR /app
COPY requirements-backend.txt ./
RUN pip install --no-cache-dir -r requirements-backend.txt
COPY backend ./backend
COPY src ./src
COPY styles ./styles
COPY data ./data
COPY index.html ./index.html
ENV PORT=8000
EXPOSE 8000
CMD ["sh", "-c", "uvicorn backend.service:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
