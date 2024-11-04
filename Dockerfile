# 使用官方的 Python 镜像作为基础镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 复制当前目录的内容到工作目录
COPY . /app

RUN apt-get update -qq -y && \
    apt-get install -y \
        cron \
        libasound2 \
        libatk-bridge2.0-0 \
        libgtk-4-1 \
        libnss3 \
        unzip \
        xdg-utils && \
    rm -rf /var/lib/apt/lists/*
ADD https://storage.googleapis.com/chrome-for-testing-public/130.0.6723.91/linux64/chrome-linux64.zip chrome-linux64.zip
RUN unzip chrome-linux64.zip && \
    rm chrome-linux64.zip && \
    mv chrome-linux64 /opt/chrome/ && \
    ln -s /opt/chrome/chrome /usr/local/bin/

ADD https://storage.googleapis.com/chrome-for-testing-public/130.0.6723.91/linux64/chromedriver-linux64.zip chromedriver-linux64.zip
RUN unzip -j chromedriver-linux64.zip chromedriver-linux64/chromedriver && \
    rm chromedriver-linux64.zip && \
    mv chromedriver /usr/local/bin/ && \
    pip install --no-cache-dir -r requirements.txt

# 添加 crontab 文件到 /etc/cron.d/
COPY cron /etc/cron.d/mapcron

# 给 crontab 文件添加执行权限
RUN chmod 0644 /etc/cron.d/mapcron

# 应用 crontab 文件
RUN crontab /etc/cron.d/mapcron

# 创建一个日志文件以便 cron 可以写入日志
RUN touch /var/log/cron.log

# 启动 cron 服务并运行脚本
CMD cron && tail -f /var/log/cron.log