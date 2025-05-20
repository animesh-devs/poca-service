FROM python:3.9-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose port
EXPOSE 8000

# Command to run the application
CMD ["bash", "-c", "python init_db.py --force && python3 ./clean_db_create_test_data.py && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
