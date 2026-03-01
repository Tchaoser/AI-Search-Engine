# -----------------------
# Base image
# -----------------------
FROM python:3.12-slim

# -----------------------
# System + Node
# -----------------------
RUN apt-get update && \
    apt-get install -y curl gnupg lsb-release build-essential && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# -----------------------
# Non-root user
# -----------------------
RUN useradd -ms /bin/bash appuser

# -----------------------
# Workdir
# -----------------------
WORKDIR /app

# -----------------------
# Backend
# -----------------------
COPY backend ./backend
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# -----------------------
# Frontend deps
# -----------------------
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install

# -----------------------
# Frontend source
# -----------------------
COPY frontend ./

# -----------------------
# BUILD FRONTEND AT IMAGE BUILD TIME
# -----------------------
RUN npm run build

# -----------------------
# Permissions
# -----------------------
RUN chown -R appuser:appuser /app

# -----------------------
# Writable backend dirs
# -----------------------
RUN mkdir -p /app/backend/logs /app/backend/data && \
    chown -R appuser:appuser /app/backend

# -----------------------
# Startup
# -----------------------
WORKDIR /app
COPY start.sh ./start.sh
RUN chmod +x start.sh && chown appuser:appuser ./start.sh

# -----------------------
# Env
# -----------------------
ENV PYTHONPATH=/app

# -----------------------
# Drop privileges
# -----------------------
USER appuser

# -----------------------
# Run
# -----------------------
CMD ["./start.sh"]
