import os
import json
import time
from typing import Optional
from datetime import datetime
from typing import Any
from line_works.client import LineWorks
from line_works.mqtt.enums.notification_type import NotificationType
from line_works.mqtt.models.payload.message import MessagePayload
from line_works.mqtt.enums.packet_type import PacketType
from line_works.openapi.talk.models.flex_content import FlexContent
from line_works.tracer import LineWorksTracer
from dotenv import load_dotenv  
from line_works.mqtt.models.packet import MQTTPacket
from custom_line_works import CustomLineWorks
import json

load_dotenv(".env")

class CommandHandler:
    PREFIX = '!'  # Command prefix
    HELP_MESSAGE = (
        f"{PREFIX}help: show this message\n"
        f"{PREFIX}speed: measure send/receive message speed\n"
        f"{PREFIX}getdata: receive and process data\n"
        f"{PREFIX}flex: send flex message\n"
        f"{PREFIX}userinfo: show user info\n"
        f"{PREFIX}search: search messages\n"
    )
    FLEX_FILE_PATH = 'src/sample_flex.json'

    # データ取得状態を管理するためのクラス変数
    DATA_RETRIEVAL_STATE: dict[str, dict[str, Any]] = {}

    def __init__(self, works: LineWorks):
        self._works = works
        self._last_command_user: Optional[str] = None

    @classmethod
    def get_data(cls, works: LineWorks, channel_no: str, payload: MessagePayload) -> None:
        """データ取得モードを開始.

        Args:
            works: LineWorksクライアント
            channel_no: チャンネル番号
            payload: メッセージペイロード
        """
        cls.DATA_RETRIEVAL_STATE[channel_no] = {
            "user_no": str(payload.user_no),
            "waiting_for_data": True,
            "data": None,
        }
        works.send_text_message(
            channel_no,
            "データの取得を開始しました。\n"
            "データの取得を中止する場合は「キャンセル」と入力してください。",
        )

    def _handle_data_retrieval(
        self, payload: MessagePayload
    ) -> bool:
        """データ取得状態の処理を行う.

        Args:
            payload: メッセージペイロード

        Returns:
            bool: データ取得状態の処理を行った場合はTrue
        """
        state = self.DATA_RETRIEVAL_STATE.get(payload.channel_no)
        if not state:
            return False

        if not state.get("waiting_for_data", False):
            return False

        # 送信者が一致しない場合は処理しない
        if str(state.get("user_no")) != str(payload.user_no):
            return False

        # キャンセル処理
        if payload.loc_args1 == "キャンセル":
            state["waiting_for_data"] = False
            self._works.send_text_message(
                payload.channel_no, "データ取得を中止しました。"
            )
            return True

        # データを保存
        state["data"] = payload

        # 取得したデータの詳細を送信
        self._works.send_text_message(
            payload.channel_no, f"[Get Data] Payload:\n{payload!r}"
        )

        # データ取得状態をリセット
        state["waiting_for_data"] = False

        return True

    def handle(self, packet: MQTTPacket) -> None:
        """Handle incoming message payload"""
        payload = packet.payload
        if not payload.channel_no:
            return

        if payload.notification_type == NotificationType.NOTIFICATION_STICKER:
            self._handle_sticker_message(payload)
        else:
            self._handle_text_message(payload)

    def _handle_text_message(self, payload: MessagePayload) -> None:
        """Handle text message commands"""
        command = payload.loc_args1
        if command == f'{self.PREFIX}help':
            self._works.send_text_message(payload.channel_no, self.HELP_MESSAGE)
        elif command == f'{self.PREFIX}speed':
            self._measure_speed(payload)
        elif command == f'{self.PREFIX}getdata':
            self.get_data(self._works, payload.channel_no, payload)
        elif command == f'{self.PREFIX}flex':
            self._send_flex_message(payload)
        elif command.startswith("!userinfo:"):
            self.user_info(self._works, payload.channel_no, command)
        elif command.startswith("!search:"):
            self.search(self._works, payload.channel_no, command)
        else:
            # データ取得モードの処理
            if self._handle_data_retrieval(payload):
                return

    @staticmethod
    def user_info(works: LineWorks, channel_no: str, text: str) -> None:
        """指定されたユーザーIDの詳細情報をFlexメッセージで送信します.

        Args:
            works: LineWorksクライアントインスタンス
            channel_no: メッセージを送信するチャンネル番号
            text: ユーザーID取得のためのコマンドテキスト
        """
        # コマンドからユーザーIDを抽出
        if not text.startswith("!userinfo:"):
            works.send_text_message(
                channel_no, "!userinfo:{user_id} の形式で入力してください"
            )
            return

        user_id = text.split(":")[-1].strip()
        if not user_id:
            works.send_text_message(
                channel_no, "ユーザーIDを指定してください。"
            )
            return

        # プロファイル情報を取得
        custom_works = CustomLineWorks(
            works_id=works.works_id, password=works.password
        )
        user_info = custom_works.get_user_info(user_id)

        if not user_info:
            works.send_text_message(
                channel_no, f"ID: {user_id} の情報は取得できません。"
            )
            return

        # Flexメッセージテンプレートを読み込み
        with open("user_info.json", "r", encoding="utf-8") as f:
            flex_message = FlexContent(altText="User Info", contents=json.load(f))

        # JSONをコピーして編集
        contents = flex_message.contents.copy()

        # テンプレートの値を置換
        contents_str = json.dumps(contents)
        contents_str = contents_str.replace(
            "{user_id}", str(user_info.get("userId", " "))
        )
        contents_str = contents_str.replace(
            "{display_name}",
            user_info.get("name", {}).get("displayName", "未設定"),
        )
        contents_str = contents_str.replace(
            "{original_photo_url}",
            user_info.get("photo", {}).get(
                "originalPhotoUrl", "https://via.placeholder.com/300"
            ),
        )
        contents_str = contents_str.replace(
            "{service_type}",
            user_info.get("worksAt", {}).get("serviceType", "未設定"),
        )

        # privateContactNoが0以外の場合のみ表示
        private_contact_no = user_info.get("worksAt", {}).get(
            "privateContactNo", 0
        )
        contents_str = contents_str.replace(
            "{private_contact_no}",
            str(private_contact_no) if private_contact_no != 0 else "未登録",
        )

        # JSONに戻す
        flex_message.contents = json.loads(contents_str)

        # Flexメッセージを送信
        works.send_flex_message(channel_no, flex_content=flex_message)

    def format_search_result(self, result: list) -> str:
        """search関数の検索結果をフォーマットする.

        Args:
            result: 検索結果のリスト

        Returns:
            フォーマットされた文字列
        """
        if not result:
            return "検索結果が見つかりませんでした。"

        messages = result  # メッセージリスト
        first_time = min(message["messageUnixTime"] for message in messages)
        last_time = max(message["messageUnixTime"] for message in messages)
        name_counts: dict[str, int] = {}

        # 名前ごとにメッセージ数をカウント
        for message in messages:
            name = message["name"]
            name_counts[name] = name_counts.get(name, 0) + 1

        total_count = sum(name_counts.values())
        first_time_str = datetime.fromtimestamp(first_time).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        last_time_str = datetime.fromtimestamp(last_time).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        # 名前ごとのメッセージ数をリスト表示
        name_summary = "\n".join(
            f"{name}: {count} \n" for name, count in name_counts.items()
        )
        return (
            f"合計回数 : {total_count} \n\n"
            f"最初のメッセージ : {first_time_str}\n\n"
            f"最後のメッセージ : {last_time_str}\n\n"
            f"-------送信者一覧-------\n{name_summary}"
        )

    def convert_timestamp_to_datetime(self, timestamp_ms):
        """ミリ秒単位のタイムスタンプをdatetimeオブジェクトに変換する関数."""
        return datetime.fromtimestamp(timestamp_ms / 1000)

    def search(self, works: LineWorks, channel_no: str, text: str) -> None:
        """Searchメッセージを送信.

        Args:
            works: LineWorksクライアント
            channel_no: チャンネル番号
            text: 検索対象のtext
        """
        if not text.startswith("!search:"):
            works.send_text_message(
                channel_no,
                "検索をするには、\n"
                "!search:検索したいキーワード の形式で入力してください。",
            )
            return

        search_text = text.split(":")[-1].strip()
        if not search_text:
            works.send_text_message(
                channel_no, "検索したいキーワードを指定してください。"
            )
            return

        custom_works = CustomLineWorks(
            works_id=works.works_id, password=works.password
        )
        search_result = custom_works.search_and_fetch_messages(
            keyword=search_text,
            start=0,
            display=10000,
            channel_no=channel_no,
        )
        result = search_result.get("result", [])
        formatted_result = self.format_search_result(result)

        if formatted_result:
            works.send_text_message(channel_no, formatted_result)
        else:
            works.send_text_message(
                channel_no, "検索結果が見つかりませんでした。"
            )

    def _send_flex_message(self, payload: MessagePayload) -> None:
        """Send flex message"""
        with open(self.FLEX_FILE_PATH) as f:
            flex_data = json.load(f)
        flex_content = FlexContent(altText="test", contents=flex_data)
        self._works.send_flex_message(payload.channel_no, flex_content)

    def _measure_speed(self, payload: MessagePayload) -> None:
        """Measure send/receive speed of messages"""
        start_time = time.time()
        self._works.send_text_message(payload.channel_no, "start")
        elapsed_time = time.time() - start_time
        self._works.send_text_message(payload.channel_no, f"{elapsed_time:.2f} sec")

    def _handle_sticker_message(self, payload: MessagePayload) -> None:
        """Handle sticker message"""
        self._works.send_sticker_message(payload.channel_no, payload.sticker)


def receive_publish_packet(works: LineWorks, packet: MQTTPacket) -> None:
    """Handle publish packet and forward to CommandHandler"""
    payload = packet.payload
    if isinstance(payload, MessagePayload):
        CommandHandler(works).handle(packet)


def main() -> None:
    """Application entry point"""
    works_id = os.getenv('WORKS_ID')
    password = os.getenv('WORKS_PASSWORD')
    if not works_id or not password:
        raise ValueError("WORKS_ID and WORKS_PASSWORD environment variables must be set")

    works = LineWorks(works_id=works_id, password=password)
    my_info = works.get_my_info()
    print(f"My info: {my_info}")

    tracer = LineWorksTracer(works=works)
    tracer.add_trace_func(PacketType.PUBLISH, receive_publish_packet)
    tracer.trace()


if __name__ == "__main__":
    main()
