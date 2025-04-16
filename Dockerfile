USER root

# Install Python, pip, and supervisor
RUN apt-get update && apt-get install -y python3 python3-pip supervisor

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install Python packages
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy supervisor configuration
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Run supervisor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]