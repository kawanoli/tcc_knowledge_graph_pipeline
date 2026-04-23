# Use a slim Python image to reduce the base footprint
FROM python:3.10-slim

# Set environment variables for memory management and logging
# MALLOC_ARENA_MAX=2 prevents memory fragmentation in C-extensions (like those used by spaCy/numpy)
# PYTHONUNBUFFERED=1 ensures logs are printed immediately
# PYTHONDONTWRITEBYTECODE=1 stops Python from generating .pyc files
ENV MALLOC_ARENA_MAX=2 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies required for building ML/NLP packages
# The 'rm -rf' step ensures we don't store apt cache, keeping the image small
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first to leverage Docker's layer caching
COPY requirements.txt .

# Install Python dependencies and download the spaCy model
# --no-cache-dir prevents pip from saving downloaded wheels to RAM/disk, saving memory
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    python -m spacy download pt_core_news_sm

# Copy the rest of the application code
COPY . .

# Create the input folder expected by the application
RUN mkdir -p tccs

# Define the default command to execute the pipeline
CMD ["python", "main.py"]