import os
import json
import time
from typing import Optional

from line_works.client import LineWorks
from line_works.mqtt.enums.notification_type import NotificationType
from line_works.mqtt.models.payload.message import MessagePayload
from line_works.openapi.talk.models.flex_content import FlexContent
from line_works.tracer import LineWorksTracer

PREFIX = '!'  # Command prefix

HELP_MESSAGE = (
    f"{PREFIX}help: show this message\n"
    f"{PREFIX}speed: measure send/receive message speed\n"
    f"{PREFIX}getdata: receive and process data\n"
    f"{PREFIX}flex: send flex message\n"
)
FLEX_FILE_PATH = 'src/sample_flex.json'


class CommandHandler:
    def __init__(self, works: LineWorks):
        self.works = works
        self._last_command_user: Optional[str] = None
        self._getdata_flag: bool = False

    def handle(self, payload: MessagePayload) -> None:
        """Handle message payload"""
        if not payload.channel_no:
            return

        if payload.notification_type == NotificationType.NOTIFICATION_STICKER:
            self._handle_sticker_message(payload)
        else:
            self._handle_text_message(payload)

    def _handle_text_message(self, payload: MessagePayload) -> None:
        """Handle text message"""
        command = payload.loc_args1
        if command == f'{PREFIX}help':
            self.works.send_text_message(payload.channel_no, HELP_MESSAGE)
        elif command == f'{PREFIX}speed':
            self._measure_speed(payload)
        elif command == f'{PREFIX}getdata':
            self._handle_getdata(payload)
        elif command == f'{PREFIX}flex':
            self._send_flex_message(payload)
        elif self._getdata_flag and self._last_command_user == payload.user_no:
            self._process_received_data(payload)

    def _handle_getdata(self, payload: MessagePayload) -> None:
        """Prepare to receive data"""
        if not self._getdata_flag:
            # First time getdata command, enter "getdata mode"
            self._getdata_flag = True
            self._last_command_user = payload.user_no
            self.works.send_text_message(payload.channel_no, "Getdata mode started. Please send your data.")
        else:
            # If getdata mode is already active, proceed to receive data only if it's from the same user
            if self._last_command_user == payload.user_no:
                self._process_received_data(payload)
            else:
                self.works.send_text_message(payload.channel_no, "You are not authorized to send data at this time.")

    def _send_flex_message(self, payload: MessagePayload) -> None:
        """Send flex message"""
        with open(FLEX_FILE_PATH) as f:
            flex_data = json.load(f)
        flex_content = FlexContent(altText="test", contents=flex_data)
        self.works.send_flex_message(payload.channel_no, flex_content)

    def _measure_speed(self, payload: MessagePayload) -> None:
        """Measure message send/receive speed"""
        start_time = time.time()
        self.works.send_text_message(payload.channel_no, "start")
        elapsed_time = time.time() - start_time
        self.works.send_text_message(payload.channel_no, f"{elapsed_time:.2f} sec")

    def _process_received_data(self, payload: MessagePayload) -> None:
        """Process received data"""
        self.works.send_text_message(payload.channel_no, f"Received data: {payload!r}")
        self._getdata_flag = False
        self._last_command_user = None

    def _handle_sticker_message(self, payload: MessagePayload) -> None:
        """Handle sticker message"""
        self.works.send_sticker_message(payload.channel_no, payload.sticker)


def receive_publish_packet(works: LineWorks, packet) -> None:
    """Handle publish packet"""
    payload = packet.payload
    if isinstance(payload, MessagePayload):
        CommandHandler(works).handle(payload)


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
    tracer.add_trace_func('PUBLISH', receive_publish_packet)
    tracer.trace()


if __name__ == "__main__":
    main()
