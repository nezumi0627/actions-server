"""A custom library that provides requests not defined in line-works-sdk.

Author:
    github.com/nezumi0627

Description:
    Adds custom requests to the existing line-works-sdk library.

Using sdk Link(line-works-sdk v3.4):
    https://github.com/nanato12/line-works-sdk/releases/tag/v3.4
"""

import logging
import time
from datetime import datetime
from typing import Any, ClassVar, TypedDict

from line_works import (
    LineWorks,  # Importing the existing line-works-sdk library
)
from requests.exceptions import HTTPError


class Name(TypedDict):
    """Name of the user."""

    firstName: str
    lastName: str
    displayName: str
    displayPhoneticName: str


class Photo(TypedDict):
    """Photo of the user."""

    photoHash: str
    originalPhotoUrl: str
    photoUrl: str
    editable: bool


class Organization(TypedDict):
    """Organization of the user."""

    organizationName: str
    orgUnits: list[str]


class WorksAt(TypedDict):
    """WorksAt of the user."""

    serviceType: str
    relationStatus: str
    privateContactNo: int
    guest: bool


class UserInfo(TypedDict):
    """UserInfo of the user."""

    userId: int
    name: Name
    nickName: str
    photo: Photo
    organizations: list[Organization]
    emails: list[str]
    telephones: list[str]
    messengers: list[str]
    important: bool
    worksAt: WorksAt
    enableDownload: bool
    isCounselor: bool
    isCounselContact: bool


class CustomLineWorks(LineWorks):
    """Extended library for Line Works."""

    BASE_URL: ClassVar[str] = "https://talk.worksmobile.com"

    def custom_request(
        self,
        endpoint: str,
        method: str = "GET",
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Executes a custom API request."""
        try:
            response = self.session.request(
                method=method,
                url=self.BASE_URL + endpoint,
                json=data,
                headers=self.session.headers,
            )
            response.raise_for_status()
            return response.json()
        except HTTPError as e:
            logging.error(f"Custom request error: {e}")
            raise

    @staticmethod
    def get_time_stamp() -> int:
        """Converts timestamp to string."""
        return int(time.time() * 1000)

    def get_user_info(
        self, user_id: str, domain_id: int = 0, client: str = "PC_WEB"
    ) -> dict[str, Any] | None:
        """Fetches specific user information."""
        endpoint = (
            f"/p/contact/v4/users/{user_id}?"
            f"domainId={domain_id}&"
            f"client={client}"
        )
        return self.custom_request(endpoint)

    def get_channel_info(
        self,
        channel_no: str,
        message_no: str,
        direction: int = 1,
        recent_message_count: int = 20,
    ) -> dict[str, Any] | None:
        """Fetches specific channel information."""
        endpoint = "/p/oneapp/client/chat/getChannelInfo"
        data = {
            "channelNo": channel_no,
            "direction": direction,
            "messageNo": message_no,
            "recentMessageCount": recent_message_count,
        }
        return self.custom_request(endpoint, method="POST", data=data)

    def get_issue(
        self, date_str: str, language: str = "ja_JP"
    ) -> dict[str, Any] | str:
        """Fetches bug information for the specified date."""
        try:
            # 日付をYYYY-MM-DD形式に変換
            if len(date_str) == 8:  # YYYYMMDD形式の場合
                date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
            else:
                date = date_str  # 既にYYYY-MM-DD形式の場合そのまま使用

            timestamp_ms = int(
                datetime.strptime(date, "%Y-%m-%d").timestamp() * 1000
            )
            endpoint = (
                f"/api/v2/issueDetail?date={timestamp_ms}&language={language}"
            )
            response = self.custom_request(endpoint)
            # レスポンスをログに記録
            logging.info(f"API response: {response}")

            # 取得したバグ情報を整形
            if isinstance(response, list):
                return response
            return {"error": "Unexpected response format"}
        except ValueError as e:
            logging.error(f"Date format error: {e}")
            return {"error": "YYYY-MM-DD"}
        except Exception as e:
            logging.error(f"Error during get_issue execution: {e}")
        return {"error": "An error occurred."}

    def get_service_status(self) -> dict[str, Any] | str:
        """Fetches the current service status."""
        return self.custom_request("/p/oneapp/client/status")

    def search_and_fetch_messages(
        self,
        keyword: str,
        start=0,
        display=10000,
        channel_no=None,
        msg_types="26",
    ) -> dict[str, Any]:
        """Searches for messages."""
        if msg_types is None:
            msg_types = (
                "1:3:4:5:6:7:8:10:11:12:13:14:16:17:19:22:23:24:25:26:27:28:"
                "29:30:37:39:44:46:47:48:49:96:97:98"
            )
        payload = {
            "keyword": keyword,
            "start": start,
            "display": display,
            "channelNo": channel_no,
            "msgType": msg_types,
            "timeStamp": self.get_time_stamp(),
        }
        return self.custom_request(
            "/p/oneapp/client/search/searchChannel",
            method="POST",
            data=payload,
        )

    def get_all_chats(self, domain_id: int, user_no: int) -> dict[str, Any]:
        """Fetches all chat information."""
        data = {
            "serviceId": "works",
            "userKey": {"domainId": domain_id, "userNo": user_no},
            "filter": "none",
            "updatePaging": True,
            "pagingCount": 100,
            "userInfoCount": 10,
            "updateTime": 0,
            "beforeMsgTime": 0,
            "isPin": False,
            "requestAgain": False,
        }
        return self.custom_request(
            "/p/oneapp/client/chat/getVisibleUserChannelList",
            method="POST",
            data=data,
        )

    def get_all_friends(self, domain_id: int, user_no: int) -> list[dict]:
        """Fetches all information of friends (1-on-1 chats)."""
        return self._get_channels(domain_id, user_no, target_channel_type=6)

    def get_all_groups(self, domain_id: int, user_no: int) -> list[dict]:
        """Fetches all information of groups (group chats)."""
        return self._get_channels(domain_id, user_no, target_channel_type=10)

    def _get_channels(
        self, domain_id: int, user_no: int, target_channel_type: int
    ) -> list[dict]:
        """Fetches chat information for the specified channel type (e.g., friends or groups).

        Args:
            domain_id (int): The domain ID for the user.
            user_no (int): The user number for the user.
            target_channel_type (int): The type of channel to fetch (6 for friends, 10 for groups).

        Returns:
            list[dict]: A list of chat information dictionaries matching the specified channel type.
        """
        try:
            all_chats = self.get_all_chats(domain_id, user_no).get(
                "result", []
            )
            if not isinstance(all_chats, list):
                logging.error(
                    "Unexpected structure in get_all_chats response: "
                    f"{all_chats}"
                )
                return []

            return [
                chat
                for chat in all_chats
                if chat.get("channelType") == target_channel_type
            ]

        except Exception as e:
            logging.error(
                "Error fetching channel information for type "
                f"{target_channel_type}: {e}"
            )
            return []
