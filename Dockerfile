FROM python:3.11-slim

# به‌روزرسانی و نصب وابستگی‌ها
RUN apt-get update && apt-get install -y \
    wget unzip curl gnupg \
    libglib2.0-0 libnss3 libgconf-2-4 libfontconfig1 libxss1 libxcomposite1 \
    libxcursor1 libxdamage1 libxi6 libxtst6 libappindicator1 libdbusmenu-glib4 libdbusmenu-gtk3-4 \
    fonts-liberation xdg-utils libatk-bridge2.0-0 libgtk-3-0 libasound2 \
    && rm -rf /var/lib/apt/lists/*

# نصب Chrome
RUN apt-get update && apt-get install -y google-chrome-stable

# دریافت نسخه Chrome و نصب ChromeDriver متناظر
RUN CHROME_VERSION=$(google-chrome --version | cut -d ' ' -f 3 | cut -d '.' -f 1-3) \
    && CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROME_VERSION") \
    && wget -q -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip" \
    && unzip /tmp/chromedriver.zip -d /usr/local/bin/ \
    && rm /tmp/chromedriver.zip \
    && chmod +x /usr/local/bin/chromedriver
# کپی فایل نیازمندی‌ها و نصب پکیج‌های پایتون (شامل chromedriver-autoinstaller)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# کپی کد پروژه به داخل کانتینر
COPY . /app
WORKDIR /app

# اجرای برنامه
CMD ["python", "main.py"]
