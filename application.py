"""
WSGI entry point for Elastic Beanstalk
"""
from app.main import app

# This is what EB will import
application = app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(application, host="0.0.0.0", port=8000)