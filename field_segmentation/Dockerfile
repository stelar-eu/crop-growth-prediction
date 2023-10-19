# Use an official Python runtime as a parent image
FROM python:3.10

WORKDIR /app

# Install any needed packages specified in requirements.txt
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Install ffmpeg (needed for cv2)
RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y

# Copy the rest of the working directory contents into the container at /app
COPY segmentation_pipeline.py ./

# Run app.py when the container launches
ENTRYPOINT ["python", "segmentation_pipeline.py"]

# Pass in the other arguments to the entrypoint
CMD ["-h"]
