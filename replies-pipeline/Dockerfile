# Use an official Python runtime as a parent image
FROM python:3.8.3-slim

# Run as non-root user
RUN useradd -ms /bin/bash appuser
USER appuser

# Upgrade pip
RUN pip install --upgrade pip

# Set working directory
RUN mkdir -p /home/appuser/app
WORKDIR /home/appuser/app

ENV PYTHONPATH=/home/appuser/app
ENV PATH="/home/appuser/.local/bin:${PATH}"

# Install packages from requirements.txt
COPY --chown=appuser:appuser requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Set transformer cache folder
RUN mkdir ./transformers_cache
ENV TRANSFORMERS_CACHE="/home/appuser/transformers_cache"

# Copy app files
COPY --chown=appuser:appuser ./*.py ./

CMD ["python", "run.py"]