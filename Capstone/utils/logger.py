import logging
from pathlib import Path

def setup_logger():
    """Setup and configure logger"""
    # Create logs directory if it doesn't exist
    Path('logs').mkdir(exist_ok=True)
    
    # Configure logger
    logger = logging.getLogger('multi_agent')
    logger.setLevel(logging.INFO)
    
    # Create file handler
    file_handler = logging.FileHandler('logs/app.log')
    file_handler.setLevel(logging.INFO)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger 