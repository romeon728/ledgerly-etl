import logging
from collections import deque
import streamlit as st

# 1. The Shared Buffer
# We keep this as a global variable in this module so app.py can read it
log_buffer = deque(maxlen=100)

class StreamlitLogHandler(logging.Handler):
  def emit(self, record):
    msg = self.format(record)
    log_buffer.append(msg)

def setup_logging():
  root_logger = logging.getLogger()
  root_logger.setLevel(logging.INFO)

  if not root_logger.handlers:
    # Console Handler
    console_handler = logging.StreamHandler()
    # Adding filename to console as well
    console_handler.setFormatter(logging.Formatter('[%(filename)s] %(message)s'))
    
    # Streamlit Handler
    st_handler = StreamlitLogHandler()
    # Clean, professional format for your UI
    # Example: 2025-01-01 12:00:00 | INFO | parser.py:42 | Starting parse...
    st_formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(filename)s:%(lineno)d | %(message)s', datefmt='%H:%M:%S')
    st_handler.setFormatter(st_formatter)
    
    root_logger.addHandler(console_handler)
    root_logger.addHandler(st_handler)