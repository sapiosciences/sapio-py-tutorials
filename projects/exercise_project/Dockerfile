# This file should typically remain unchanged. Using this, you can build a Docker image to run a
# webhook server off of. How that server is deployed is up to you and/or the customer.
FROM python:3.13-slim
ENV SapioWebhooksDebug=False
ENV SapioWebhooksInsecure=False

RUN python -m pip install --upgrade pip

# Create a non-privileged user for extra security. Install the requirements. Create an /app/ directory.
ADD requirements.txt .
RUN useradd sapio -u 1000 -s /bin/sh && \
pip install -r requirements.txt && \
mkdir -p /app

# Copy to the app folder. Swap to the sapio user. Make /app/ our working directory.
ADD . /app/
USER sapio
WORKDIR /app

# Open 8080 and run the server.
EXPOSE 8080
ENTRYPOINT gunicorn server:app
