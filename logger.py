import os
import logging
from logging.handlers import RotatingFileHandler


if not os.path.exists('logs'):
    os.mkdir('logs')
    
logger= logging.getLogger('online_shopping_app')    

logger.setLevel(logging.INFO)

file_handler= RotatingFileHandler(
    'logs/app.log',
    maxBytes= 5 * 1024 * 1024,
    backupCount= 4
)

formatter= logging.Formatter(
        ('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    )
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

logger.propagate= False