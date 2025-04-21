import logging
import os

# Ensure log directory exists
LOG_DIR = os.path.dirname(__file__)
LOG_FILE = os.path.join(LOG_DIR, "security_audit.log")

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("jwt_audit")
