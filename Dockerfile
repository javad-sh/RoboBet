FROM python:3.11-slim

# نصب ابزارهای لازم و به‌روزرسانی
RUN apt-get update && apt-get install -y \
    wget gnupg \
    && rm -rf /var/lib/apt/lists/*

# اضافه کردن کلید و مخزن Google Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list

# به‌روزرسانی دوباره و نصب Google Chrome
RUN apt-get update && apt-get install -y google-chrome-stable

# بقیه دستورات داکرفایل (مثل نصب پکیج‌های پایتون)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app
WORKDIR /app

CMD ["python", "main.py"]