# runner_image/Dockerfile
FROM python:3.11-slim

# create a non-root user and a home directory
RUN useradd -m runner && mkdir -p /home/runner/app && chown -R runner:runner /home/runner

WORKDIR /home/runner
USER runner

# Default command - will be overridden by the API's docker run command
CMD ["python"]
