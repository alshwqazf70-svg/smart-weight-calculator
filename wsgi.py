
"""
WSGI entry point for Render.com and production servers.
"""
from app import app as application

# Expose as app too for gunicorn app:app
app = application

if __name__ == "__main__":
    application.run()
