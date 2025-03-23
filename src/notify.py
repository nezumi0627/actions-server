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
from datetime import datetime
from typing import Dict

from line_works.client import LineWorks
from line_works.openapi.talk.models.flex_content import FlexContent

from config.config import WORKS_ID, PASSWORD

logger = logging.getLogger(__name__)

NOTIFY_USER_ID = "913000043047576"


class SystemInfo:
    """システム情報を取得するクラス."""

    @staticmethod
    def get_os_info() -> str:
        """OS情報を取得.

        Returns:
            str: OS情報
        """
        return f"{platform.system()} {platform.release()}"

    @staticmethod
    def get_cpu_usage() -> str:
        """CPU使用率を取得.

        Returns:
            str: CPU使用率
        """
        return f"{psutil.cpu_percent(interval=1):.1f}%"

    @staticmethod
    def get_memory_usage() -> str:
        """メモリ使用率を取得.

        Returns:
            str: メモリ使用率
        """
        memory = psutil.virtual_memory()
        return f"{memory.percent:.1f}%"

    @staticmethod
    def get_ip_address() -> str:
        """IPアドレスを取得.

        Returns:
            str: IPアドレス
        """
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "取得できません"

    @staticmethod
    def get_disk_usage() -> str:
        """ディスク使用率を取得.

        Returns:
            str: ディスク使用率
        """
        disk = psutil.disk_usage('/')
        return f"{disk.percent:.1f}%"


class NotificationTemplate:
    """通知テンプレートを管理するクラス."""

    def __init__(self, template_path: str):
        """初期化.

        Args:
            template_path: テンプレートファイルのパス
        """
        self.template_path = template_path
        self.template: Dict = {}

    def load_template(self) -> None:
        """テンプレートファイルを読み込む."""
        with open(self.template_path, "r", encoding="utf-8") as f:
            self.template = json.load(f)

    def replace_variables(self, variables: Dict[str, str]) -> Dict:
        """テンプレート内の変数を置換する.

        Args:
            variables: 置換する変数の辞書

        Returns:
            Dict: 置換後のテンプレート
        """
        def replace_text(obj: Dict, variables: Dict) -> Dict:
            """再帰的にテキストを置換する."""
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if isinstance(value, str) and "$" in value:
                        obj[key] = variables.get(value, value)
                    elif isinstance(value, dict):
                        replace_text(value, variables)
            return obj

        return replace_text(self.template.copy(), variables)


def get_system_info() -> Dict[str, str]:
    """システム情報を取得.

    Returns:
        Dict[str, str]: システム情報の辞書
    """
    return {
        "$os": SystemInfo.get_os_info(),
        "$cpu": SystemInfo.get_cpu_usage(),
        "$memory": SystemInfo.get_memory_usage(),
        "$ip": SystemInfo.get_ip_address(),
        "$disk": SystemInfo.get_disk_usage()
    }


def format_notification_message(result: str) -> str:
    """通知メッセージをフォーマットする.

    Args:
        result: 実行結果のメッセージ

    Returns:
        str: フォーマットされたメッセージ
    """
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    return f"""
実行状態: {"正常" if "正常" in result else "エラー"}
実行時間: {current_time}
実行結果: {result}
"""


def send_flex_notification(result: str) -> None:
    """Flexメッセージとして通知を送信する.

    Args:
        result: 実行結果のメッセージ
    """
    works = LineWorks(works_id=WORKS_ID, password=PASSWORD)
    
    try:
        # テンプレートを読み込む
        template = NotificationTemplate("src/flex_messages/notification.json")
        template.load_template()
        
        # 変数を置換
        variables = {
            "$status": "正常" if "正常" in result else "エラー",
            "$time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "$result": result,
            **get_system_info()
        }
        flex_template = template.replace_variables(variables)
        
        # メッセージを送信
        works.send_flex_message(
            NOTIFY_USER_ID,
            flex_content=FlexContent(alt_text="実行結果", contents=flex_template)
        )
        
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}", file=sys.stderr)


def main() -> None:
    """メイン関数."""
    if len(sys.argv) != 2:
        print("使用方法: python notify.py 実行結果のメッセージ", file=sys.stderr)
        sys.exit(1)
    
    result = sys.argv[1]
    send_flex_notification(result)


if __name__ == "__main__":
    main()