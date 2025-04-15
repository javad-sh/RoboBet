FROM selenium/standalone-chrome:latest

USER root

# نصب پایتون و pip
RUN apt-get update && apt-get install -y python3 python3-pip

# مسیر کار
WORKDIR /app

# کپی پروژه
COPY . .

# نصب پکیج‌های پایتون
RUN pip3 install --no-cache-dir -r requirements.txt

# اجرای اسکریپت
CMD ["python3", "main.py"]
