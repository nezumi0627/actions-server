"""コマンド関連の定数を管理するモジュール."""

from typing import Final

# コマンドプレフィックス
COMMAND_PREFIX: Final[str] = "!"  # TODO: PREFIXの変更機能を実装する

# コマンド一覧
HELP_COMMAND: Final[str] = f"{COMMAND_PREFIX}help"
TEST_COMMAND: Final[str] = f"{COMMAND_PREFIX}test"
FLEX_COMMAND: Final[str] = f"{COMMAND_PREFIX}flex"
GET_DATA_COMMAND: Final[str] = f"{COMMAND_PREFIX}getdata"
USER_INFO_COMMAND: Final[str] = f"{COMMAND_PREFIX}userinfo"
SEARCH_COMMAND: Final[str] = f"{COMMAND_PREFIX}search"
GROUPS_COMMAND: Final[str] = f"{COMMAND_PREFIX}groups"
FRIENDS_COMMAND: Final[str] = f"{COMMAND_PREFIX}friends"

# 全コマンドのリスト
ALL_COMMANDS: Final[list[str]] = [
    HELP_COMMAND,
    TEST_COMMAND,
    FLEX_COMMAND,
    GET_DATA_COMMAND,
    USER_INFO_COMMAND,
    SEARCH_COMMAND,
    GROUPS_COMMAND,
    FRIENDS_COMMAND,
]
