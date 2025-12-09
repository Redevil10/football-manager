# main.py - Football Manager Application

# Import app from routes module (all routes are registered there)
from routes import app


if __name__ == "__main__":
    import uvicorn
    import logging

    # Configure logging to see print statements
    logging.basicConfig(level=logging.INFO)

    uvicorn.run(app, host="0.0.0.0", port=7860, log_level="info")
