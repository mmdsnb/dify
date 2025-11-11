FROM uv:python3.12-bookworm-slim

WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# 配置 uv 使用清华镜像源
ENV UV_INDEX_URL=https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple

# 配置 Debian APT 使用阿里云镜像源
RUN if [ ! -f "/etc/apt/sources.list" ]; then \
      echo "deb http://deb.debian.org/debian bookworm main" > /etc/apt/sources.list && \
      echo "deb http://deb.debian.org/debian bookworm-updates main" >> /etc/apt/sources.list && \
      echo "deb http://deb.debian.org/debian-security bookworm-security main" >> /etc/apt/sources.list; \
    fi

RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list && \
    sed -i 's/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list && \
    find /etc/apt/sources.list.d -type f -exec sed -i 's/deb.debian.org/mirrors.aliyun.com/g' {} + 2>/dev/null || true && \
    find /etc/apt/sources.list.d -type f -exec sed -i 's/security.debian.org/mirrors.aliyun.com/g' {} + 2>/dev/null || true

# 安装系统依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制项目配置文件
COPY pyproject.toml .

# 使用 uv 安装依赖（使用清华源）
RUN uv pip install --system --no-cache -r pyproject.toml

# 复制应用代码
ARG CACHEBUST=1
COPY app.py .

# 暴露端口
EXPOSE 5003

# 使用 gunicorn 启动应用
CMD ["gunicorn", "--bind", "0.0.0.0:5003", "--workers", "2", "--timeout", "120", "app:app"]
