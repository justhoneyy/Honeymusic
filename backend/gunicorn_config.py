import multiprocessing
import os

bind = f"0.0.0.0:{os.getenv('PORT', 5000)}"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'sync'
timeout = 120
keepalive = 5
max_requests = 1000
max_requests_jitter = 50
accesslog = '-'
errorlog = '-'
loglevel = 'info'
graceful_timeout = 30
