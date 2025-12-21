# main.py - Football Manager Application

# Import app from routes module (all routes are registered there)
from routes import app

if __name__ == "__main__":
    import logging

    import uvicorn

    # Configure logging to see print statements
    logging.basicConfig(level=logging.INFO)

    uvicorn.run(app, host="0.0.0.0", log_level="info")
