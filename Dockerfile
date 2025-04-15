FROM python:3.11-slim

# به‌روزرسانی و نصب وابستگی‌ها
RUN apt-get update && apt-get install -y \
    wget unzip curl gnupg \
    libglib2.0-0 libnss3 libgconf-2-4 libfontconfig1 libxss1 libxcomposite1 \
    libxcursor1 libxdamage1 libxi6 libxtst6 libappindicator1 libdbusmenu-glib4 libdbusmenu-gtk3-4 \
    fonts-liberation xdg-utils libatk-bridge2.0-0 libgtk-3-0 libasound2 \
    && rm -rf /var/lib/apt/lists/*

# نصب Google Chrome
RUN curl -fsSL https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && apt-get install -y google-chrome-stable && \
    rm -rf /var/lib/apt/lists/*

# کپی فایل نیازمندی‌ها و نصب پکیج‌های پایتون (شامل chromedriver-autoinstaller)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# کپی کد پروژه به داخل کانتینر
COPY . /app
WORKDIR /app

# اجرای برنامه
CMD ["python", "main.py"]
