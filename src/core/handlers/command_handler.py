"""コマンド処理を管理するモジュール."""

import datetime
import json
from typing import Any

from line_works import LineWorks

from core.constants.commands import (
    ALL_COMMANDS,
    FLEX_COMMAND,
    FRIENDS_COMMAND,
    GET_DATA_COMMAND,
    GROUPS_COMMAND,
    HELP_COMMAND,
    SEARCH_COMMAND,
    TEST_COMMAND,
    USER_INFO_COMMAND,
)
from core.utils import load_flex_message
from custom_line_works import CustomLineWorks

# データ取得状態を管理する辞書
DATA_RETRIEVAL_STATE: dict[str, dict[str, str | None]] = {}


class CommandHandler:
    """コマンド処理を管理するクラス."""

    def __init__(self) -> None:
        """初期化."""
        self.command_map: dict[str, Any] = {
            HELP_COMMAND: self.help,
            TEST_COMMAND: self.test,
            FLEX_COMMAND: self.flex,
            GET_DATA_COMMAND: self.get_data,
            USER_INFO_COMMAND: self.user_info,
            SEARCH_COMMAND: self.search,
            GROUPS_COMMAND: self.groups,
            FRIENDS_COMMAND: self.friends,
        }

    def handle_command(
        self,
        works: LineWorks,
        channel_no: str,
        text: str,
        payload: Any,
    ) -> None:
        """コマンドを処理する.

        Args:
            works: LineWorksクライアント
            channel_no: チャンネル番号
            text: 受信したテキスト
            payload: メッセージペイロード
        """
        # 有効なコマンドでない場合は処理しない
        if text not in ALL_COMMANDS:
            return

        # コマンドごとに処理
        if text == GET_DATA_COMMAND:
            self.command_map[text](works, channel_no, payload)
        elif text == USER_INFO_COMMAND:
            works.send_text_message(
                channel_no,
                "ユーザー情報を取得するには、\n"
                "!userinfo:{user_id} の形式で入力してください。",
            )
        elif text == SEARCH_COMMAND:
            works.send_text_message(
                channel_no,
                "検索をするには、\n"
                "!search:検索したいキーワード の形式で入力してください。",
            )
        else:
            self.command_map[text](works, channel_no, text)

    @staticmethod
    def help(works: LineWorks, channel_no: str) -> None:
        """ヘルプメッセージを送信.

        Args:
            works: LineWorksクライアント
            channel_no: チャンネル番号
        """
        help_message = load_flex_message("help.json")
        works.send_flex_message(channel_no, flex_content=help_message)

    @staticmethod
    def test(works: LineWorks, channel_no: str) -> None:
        """テストメッセージを送信.

        Args:
            works: LineWorksクライアント
            channel_no: チャンネル番号
        """
        works.send_text_message(channel_no, "I'm work :)")

    @staticmethod
    def flex(works: LineWorks, channel_no: str) -> None:
        """Flexメッセージを送信.

        Args:
            works: LineWorksクライアント
            channel_no: チャンネル番号
        """
        flex_message = load_flex_message("sample.json", "Flex Message")
        works.send_flex_message(channel_no, flex_content=flex_message)

    @classmethod
    def get_data(cls, works: LineWorks, channel_no: str, payload: Any) -> None:
        """データ取得モードを開始.

        Args:
            works: LineWorksクライアント
            channel_no: チャンネル番号
            payload: メッセージペイロード
        """
        global DATA_RETRIEVAL_STATE

        DATA_RETRIEVAL_STATE[channel_no] = {
            "user_no": str(payload.from_user_no),
            "waiting_for_data": True,
            "data": None,
        }
        works.send_text_message(
            channel_no,
            "データの取得を開始しました。\n"
            "データの取得を中止する場合は「キャンセル」と入力してください。",
        )

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
        flex_message = load_flex_message("user_info.json", "User Info")

        # JSONをコピーして編集
        contents = flex_message.contents.copy()

        # テンプレートの値を置換
        contents = json.dumps(contents).replace(
            "{user_id}", str(user_info.get("userId", "未設定"))
        )
        contents = contents.replace(
            "{display_name}",
            user_info.get("name", {}).get("displayName", "未設定"),
        )
        contents = contents.replace(
            "{original_photo_url}",
            user_info.get("photo", {}).get(
                "originalPhotoUrl", "https://via.placeholder.com/300"
            ),
        )
        contents = contents.replace(
            "{service_type}",
            user_info.get("worksAt", {}).get("serviceType", "未設定"),
        )

        # privateContactNoが0以外の場合のみ表示
        private_contact_no = user_info.get("worksAt", {}).get(
            "privateContactNo", 0
        )
        contents = contents.replace(
            "{private_contact_no}",
            str(private_contact_no) if private_contact_no != 0 else "未登録",
        )

        # JSONに戻す
        flex_message.contents = json.loads(contents)

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
        name_counts = {}

        # 名前ごとにメッセージ数をカウント
        for message in messages:
            name = message["name"]
            name_counts[name] = name_counts.get(name, 0) + 1

        total_count = sum(name_counts.values())
        first_time_str = datetime.datetime.fromtimestamp(first_time).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        last_time_str = datetime.datetime.fromtimestamp(last_time).strftime(
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
        return datetime.datetime.fromtimestamp(timestamp_ms / 1000)

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

    def groups(self, works: LineWorks, channel_no: str) -> None:
        """Send formatted groups message.

        Args:
            works: LineWorks client.
            channel_no: Channel number.
        """
        custom_works = CustomLineWorks(
            works_id=works.works_id, password=works.password
        )
        groups_result = custom_works.get_all_groups(
            domain_id=works.domain_id, user_no=works.contact_no
        )

        # Format the result into a clean and readable message
        formatted_result = self.format_groups_info(groups_result)
        works.send_text_message(channel_no, formatted_result)

    def format_groups_info(self, groups_result: list[dict]) -> str:
        """Formats groups information into a readable string.

        Args:
            groups_result: List of group information dictionaries.

        Returns:
            str: Formatted groups information.
        """
        if not groups_result:
            return "No groups found."

        formatted_list = []
        for group in groups_result:
            channel_extras = json.loads(group.get("channelExtras", "{}"))
            service_type = channel_extras.get("serviceType", "N/A")

            content = (
                f"Content:\n{group.get('content', 'N/A')}"
                if group.get("messageTypeCode", 0) == 1
                else ""
            )

            formatted_list.append(
                f"Title: {group.get('title', 'N/A')}\n"
                f"Channel No: {group.get('channelNo', 'N/A')}\n"
                f"User Count: {group.get('userCount', 'N/A')}\n"
                f"Bot Count: {group.get('botCount', 'N/A')}\n"
                f"Visible: {group.get('visible', 'N/A')}\n"
                f"Joined: {group.get('joined', 'N/A')}\n"
                f"Unread Count: {group.get('unreadCount', 'N/A')}\n"
                f"Last Message No: {group.get('lastMessageNo', 'N/A')}\n"
                f"{content}\n"
                f"Service Type: {service_type}\n"
                f"{'-' * 30}"
            )

        return "\n".join(formatted_list)

    def friends(self, works: LineWorks, channel_no: str) -> None:
        """Friendsメッセージを送信.

        Args:
            works: LineWorksクライアント
            channel_no: チャンネル番号
        """
        custom_works = CustomLineWorks(
            works_id=works.works_id, password=works.password
        )
        friends_result = custom_works.get_all_friends(
            domain_id=works.domain_id, user_no=works.contact_no
        )

        formatted_friends_list = []
        for friend in friends_result:
            formatted_friends_list.append(self.format_friend_info(friend))

        for i in range(0, len(formatted_friends_list), 5):
            formatted_friends = "\n".join(formatted_friends_list[i : i + 5])
            works.send_text_message(channel_no, formatted_friends)

    def format_friend_info(self, friend: dict) -> str:
        """Format friend information into a readable message.

        Args:
            friend: Friend information dictionary.

        Returns:
            Formatted friend information as a string.
        """
        # チャンネル情報を取得
        channel_id = friend.get("channelNo", "N/A")
        visibility = (
            "Visible" if friend.get("visible", False) else "Not Visible"
        )
        join_status = "Joined" if friend.get("joined", False) else "Not Joined"
        last_message_id = friend.get("lastMessageNo", "N/A")
        first_message_id = (
            "No conversation yet"
            if friend.get("firstMessageNo", 0) == 0
            else friend.get("firstMessageNo", "N/A")
        )
        content = (
            f"Content:\n{friend.get('content', 'N/A')}"
            if friend.get("messageTypeCode", 0) == 1
            and friend.get("content", "").strip() != ""
            else ""
        )
        last_updated_time = friend.get("updateTime", "N/A")
        service_type = json.loads(friend.get("channelExtras", "{}")).get(
            "serviceType", "N/A"
        )

        # フォーマットを組み立てる
        formatted_friend = (
            f"Channel ID: {channel_id}\n"
            f"Visibility: {visibility}\n"
            f"Join Status: {join_status}\n"
            f"Last Message ID: {last_message_id}\n"
            f"First Message ID: {first_message_id}\n"
            f"{content}\n"  # contentを条件に従って追加
            f"Last Updated Message Time: {last_updated_time}\n"
            f"Service Type: {service_type}\n"
        )

        # 自分の情報を除外するために、relationStatusが'me'でないユーザーのみ
        for user in friend.get("userList", []):
            if user.get("relationStatus") != "me":  # 自分の情報を除外
                user_name = user.get("name", "N/A")
                relation_status = user.get("relationStatus", "N/A")
                join_time = user.get("joinTime", "N/A")
                photo_hash = user.get("photoHash", "N/A")

                formatted_friend += (
                    f"  Name: {user_name}\n"
                    f"  Relation Status: {relation_status}\n"
                    f"  Join Time: {join_time}\n"
                    f"  Photo Hash: {photo_hash}\n"
                )

        # 最後に区切り線を追加
        formatted_friend += "-" * 30

        return formatted_friend
