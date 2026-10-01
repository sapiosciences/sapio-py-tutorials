import multiprocessing

# Gunicorn provides multithreading within the webhook server for better concurrent request handling.
# This port must match the EXPOSE value in the Dockerfile when deploying.
bind = "0.0.0.0:8080"
workers = multiprocessing.cpu_count() * 2 + 1
timeout = 1800
