import logging
from collections import deque
import streamlit as st
import os

# 1. The Shared Buffer
# We keep this as a global variable in this module so app.py can read it
log_buffer = deque(maxlen=100)

class StreamlitLogHandler(logging.Handler):

  def __init__(self):
    super().__init__()
    # Internal list to store raw messages or formatted strings
    self.captured_logs = {"All": []}

  def emit(self, record):
    msg = self.format(record)
    self.capture_log_dict(msg)
    log_buffer.append(msg)
  
  def capture_log_dict(self, msg):
    log_module = str(msg).split(' | ')[2].capitalize()
    if log_module not in self.captured_logs.keys():
      self.captured_logs[log_module] = []
    self.captured_logs["All"].append(msg)
    self.captured_logs[log_module].append(msg)
    
  def get_logs(self, module="All"):
    """Returns the captured logs as a standard list."""
    return self.captured_logs[module]

  def get_modules(self):
    """Returns the modules in the captured logs"""
    return list(self.captured_logs.keys())
  
  def clear_history(self):
    """Wipes the internal list and the global buffer."""
    self.captured_logs.clear()
    self.captured_logs = {"All": []}
    log_buffer.clear()

@st.cache_resource
def setup_logging():
    root_logger = logging.getLogger("ledgerly")
    root_logger.setLevel(logging.INFO)

    # Check if our specific handler already exists
    existing_handler = next((h for h in root_logger.handlers if isinstance(h, StreamlitLogHandler)), None)
    
    if not existing_handler:
        st_handler = StreamlitLogHandler()
        st_formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(module)s | %(message)s', datefmt='%H:%M:%S')
        st_handler.setFormatter(st_formatter)
        root_logger.addHandler(st_handler)
        return st_handler
    
    return existing_handler