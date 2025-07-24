# Use an official Python runtime as a parent image
FROM python:3.12-slim-bookworm

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
# For this project, we only need dnspython
RUN pip install dnspython

# Expose the port the app runs on
EXPOSE 5353/udp

# Run the app. We use python3 directly as the venv is not needed in the container
CMD ["python3", "src/app.py"]
