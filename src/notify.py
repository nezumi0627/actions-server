"""Line WORKS Notification System.

This module provides functionality to send notifications to specific users
using the LINE WORKS API.
"""

import logging
import json
import sys
import psutil
import platform
import socket
import os
from datetime import datetime
from typing import Dict

from custom_line_works import CustomLineWorks
from line_works.openapi.talk.models.flex_content import FlexContent

from dotenv import load_dotenv

# Logger setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

file_handler = logging.FileHandler('notify.log', encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

# Load environment variables from .env file
load_dotenv()

# Environment variables
NOTIFY_USER_ID = os.getenv('NOTIFY_USER_ID', '307463507')
WORKS_ID = os.getenv('WORKS_ID')
PASSWORD = os.getenv('WORKS_PASSWORD')

class SystemInfo:
    """Retrieves system information."""

    @staticmethod
    def os_info() -> str:
        return f"{platform.system()} {platform.release()}"

    @staticmethod
    def cpu_usage() -> str:
        return f"{psutil.cpu_percent(interval=1):.1f}%"

    @staticmethod
    def memory_usage() -> str:
        return f"{psutil.virtual_memory().percent:.1f}%"

    @staticmethod
    def ip_address() -> str:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]

    @staticmethod
    def disk_usage() -> str:
        return f"{psutil.disk_usage('/').percent:.1f}%"

class NotificationTemplate:
    """Handles loading and replacing variables in notification templates."""

    def __init__(self, template_path: str):
        self.template_path = template_path
        self.template: Dict = {}

    def load_template(self) -> None:
        with open(self.template_path, "r", encoding="utf-8") as f:
            self.template = json.load(f)

    def replace_variables(self, variables: Dict[str, str]) -> Dict:
        def replace_text(obj: Dict, variables: Dict) -> Dict:
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if isinstance(value, str) and "$" in value:
                        obj[key] = variables.get(value, value)
                    elif isinstance(value, dict):
                        replace_text(value, variables)
            return obj

        return replace_text(self.template.copy(), variables)

def get_system_info() -> Dict[str, str]:
    """Returns a dictionary of system information."""
    return {
        "$os": SystemInfo.os_info(),
        "$cpu": SystemInfo.cpu_usage(),
        "$memory": SystemInfo.memory_usage(),
        "$ip": SystemInfo.ip_address(),
        "$disk": SystemInfo.disk_usage()
    }

def get_github_info() -> Dict[str, str]:
    """Returns GitHub Actions information."""
    return {
        "$github_url": os.getenv('GITHUB_SERVER_URL', '') + '/' + 
                       os.getenv('GITHUB_REPOSITORY', '') + '/' + 
                       os.getenv('GITHUB_RUN_ID', '')
    }

def send_flex_notification(result: str) -> None:
    """Sends a notification message using LINE WORKS API."""
    try:
        works = CustomLineWorks(works_id=WORKS_ID, password=PASSWORD)
        template = NotificationTemplate("src/flex_messages/notification.json")
        template.load_template()

        variables = {
            "$status": "OK" if result else "ERROR",
            "$time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "$result": result,
            **get_system_info(),
            **get_github_info()
        }
        flex_template = template.replace_variables(variables)

        works.send_flex_message(
            to=int(NOTIFY_USER_ID),
            flex_content=FlexContent(altText="Notification", contents=flex_template)
        )
    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
        raise

def main() -> None:
    """Main execution function."""
    if len(sys.argv) != 2:
        logger.error("Usage: python notify.py <result>")
        sys.exit(1)
    send_flex_notification(sys.argv[1])

if __name__ == "__main__":
    main()