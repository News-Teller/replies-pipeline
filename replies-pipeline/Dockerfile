# Use an official Python runtime as a parent image
FROM python:3.8.3-slim

# Add requirements.txt before rest of repo for caching
COPY requirements.txt /app/

# Set the working directory to /app
WORKDIR /app
ADD . /app

# Upgrade pip
RUN pip install --upgrade pip

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

#RUN pip install --user psycopg2==2.8.6

CMD ["python", "run.py"]
#CMD [ "python", "./run.py" ]