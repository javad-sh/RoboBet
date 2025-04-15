FROM ghcr.io/puppeteer/puppeteer:latest

# Install Python
RUN apt-get update && apt-get install -y python3 python3-pip && \
    apt-get clean

# Set workdir
WORKDIR /app

# Copy project files
COPY . .

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Run script
CMD ["python3", "main.py"]
