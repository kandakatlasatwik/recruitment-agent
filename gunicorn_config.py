import os
import multiprocessing

# Bind to the PORT provided by Render
bind = f"0.0.0.0:{os.environ.get('PORT', '5000')}"

# Only 1 worker to save memory on free tier
workers = 1

# Worker class - sync uses less memory
worker_class = "sync"

# Timeout for long-running Gemini API calls
timeout = 180  # 3 minutes

# Preload app to save memory
preload_app = True

# Restart workers periodically to prevent memory leaks
max_requests = 100
max_requests_jitter = 20

# Graceful timeout
graceful_timeout = 30

# Keep alive
keepalive = 5

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Error handling
capture_output = True
enable_stdio_inheritance = True

print(f"🔧 Gunicorn config loaded: {workers} worker(s), timeout={timeout}s")
