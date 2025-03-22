import os
import json
import time
from datetime import datetime
from typing import Optional

from line_works.client import LineWorks
from line_works.mqtt.enums.notification_type import NotificationType
from line_works.mqtt.enums.packet_type import PacketType
from line_works.mqtt.models.packet import MQTTPacket
from line_works.mqtt.models.payload.message import MessagePayload
from line_works.openapi.talk.models.flex_content import FlexContent
from line_works.tracer import LineWorksTracer


class CommandHandler:
    def __init__(self, works: LineWorks):
        self.works = works

    def log_command(self, channel_no: str, command: str, message: str) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"- [{timestamp}] Channel: {channel_no}, Command: {command}, Message: {message}\n"
        
        # Update log.md
        with open("log/log.md", "a", encoding="utf-8") as f:
            f.write(log_entry)

    def handle(self, payload: MessagePayload) -> None:
        if not payload.channel_no:
            return

        match payload.loc_args1:
            case "test":
                self.works.send_text_message(payload.channel_no, "ok")
                self.log_command(payload.channel_no, "test", "ok")
            case "/msg":
                self.works.send_text_message(payload.channel_no, f"{payload!r}")
                self.log_command(payload.channel_no, "/msg", str(payload))
            case "/flex":
                with open("src/sample_flex.json") as f:
                    j = json.load(f)
                self.works.send_flex_message(
                    payload.channel_no,
                    flex_content=FlexContent(altText="test", contents=j),
                )
                self.log_command(payload.channel_no, "/flex", "sent flex message")
            case "!help":
                help_message = (
                    "test: test\n"
                    "/msg: show message payload\n"
                    "/flex: send flex message\n"
                    "!help: show this message\n"
                    "!speed: measure send/receive message speed\n"
                    "!sticker: send sticker"
                )
                self.works.send_text_message(payload.channel_no, help_message)
                self.log_command(payload.channel_no, "!help", "showed help")
            case "!speed":
                start_time = time.time()
                self.works.send_text_message(payload.channel_no, "start")
                end_time = time.time()
                elapsed_time = end_time - start_time
                self.works.send_text_message(payload.channel_no, f"{elapsed_time:.2f} sec")
                self.log_command(payload.channel_no, "!speed", f"{elapsed_time:.2f} sec")


def receive_publish_packet(w: LineWorks, p: MQTTPacket) -> None:
    payload = p.payload

    if not isinstance(payload, MessagePayload):
        return

    CommandHandler(w).handle(payload)


if __name__ == "__main__":
    works_id = os.getenv('WORKS_ID')
    password = os.getenv('WORKS_PASSWORD')

    if not works_id or not password:
        raise ValueError("WORKS_ID and WORKS_PASSWORD environment variables must be set")

    works = LineWorks(works_id=works_id, password=password)

    my_info = works.get_my_info()
    print(f"{my_info=}")

    tracer = LineWorksTracer(works=works)
    tracer.add_trace_func(PacketType.PUBLISH, receive_publish_packet)
    tracer.trace()