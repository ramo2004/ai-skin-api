# Use Python 3.10 base image
FROM python:3.10

# Set working directory inside container
WORKDIR /app

# Copy only the requirements file first to leverage Docker caching
COPY requirements.txt /app/

# Install dependencies 
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . /app

# Ensure no .env files are copied into the container
RUN rm -f /app/.env

# Expose port 8080 (FastAPI)
EXPOSE 8080

# Run the FastAPI application using Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
