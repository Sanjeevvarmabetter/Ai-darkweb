FROM python:3.11-slim

# Install Tor and clean up
RUN apt-get update && \
    apt-get install -y tor && \
    rm -rf /var/lib/apt/lists/*
    
WORKDIR /app

# Copy requirements FIRST to leverage Docker caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project files
COPY . .

EXPOSE 8501

# Create startup script
RUN echo '#!/bin/bash\n\
tor &\n\
echo "Waiting for Tor to bootstrap ..."\n\
sleep 10\n\
python -m streamlit run app.py --server.port=8501 --server.address=0.0.0.0\n\
' > /app/start.sh

RUN chmod +x /app/start.sh

CMD ["/app/start.sh"]