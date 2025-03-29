"""Line WORKS Notification System.

This module provides functionality to send notifications to specific users
using the LINE WORKS API.
"""

import json
import logging
import os
import platform
import socket
import sys
from datetime import datetime
from typing import Dict

import psutil
from dotenv import load_dotenv
from line_works.openapi.talk.models.flex_content import FlexContent

from custom_line_works import CustomLineWorks

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
                    if isinstance(value, str):
                        # {{}}形式の変数を置換
                        for var_name, var_value in variables.items():
                            value = value.replace(f"{{{{ {var_name} }}}}", var_value)
                        obj[key] = value
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
    """LINE WORKS APIを使用して通知メッセージを送信します。"""
    # 通知テンプレートの読み込み
    template = NotificationTemplate("src/flex_messages/notification.json")
    template.load_template()

    # 変数の値を設定
    variables = {
        "status": "完了",  # 実際のワークフロー状態
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # 実行時間
        "result": result,  # 実行結果
        **get_system_info()  # システム情報
    }

    # 変数を置換
    flex_content = template.replace_variables(variables)

    # JSON文字列に変換して再度パース
    flex_content_str = json.dumps(flex_content, ensure_ascii=False)
    flex_content_dict = json.loads(flex_content_str)

    # LINE WORKS APIを使用して通知を送信
    line_works = CustomLineWorks(
        works_id=WORKS_ID,
        password=PASSWORD
    )
    line_works.send_flex_message(
        to=int(NOTIFY_USER_ID),
        flex_content=FlexContent(
            altText="ワークフロー実行結果通知",
            contents=flex_content_dict
        )
    )

def main() -> None:
    """Main execution function."""
    if len(sys.argv) != 2:
        logger.error("Usage: python notify.py <result>")
        sys.exit(1)
    send_flex_notification(sys.argv[1])

if __name__ == "__main__":
    main()