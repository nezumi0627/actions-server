import os
import json
import time
from typing import Optional, Dict

from line_works.client import LineWorks
from line_works.mqtt.enums.packet_type import PacketType
from line_works.mqtt.models.packet import MQTTPacket
from line_works.mqtt.models.payload.message import MessagePayload
from line_works.openapi.talk.models.flex_content import FlexContent
from line_works.tracer import LineWorksTracer


def receive_publish_packet(w: LineWorks, p: MQTTPacket) -> None:
    payload = p.payload

    if not isinstance(payload, MessagePayload):
        return

    if not payload.channel_no:
        return

    print(f"{payload!r}")

    match payload.loc_args1:
        case "test":
            w.send_text_message(payload.channel_no, "ok")
        case "/msg":
            w.send_text_message(payload.channel_no, f"{payload!r}")
        case "/flex":
            with open("src/sample_flex.json") as f:
                j: Dict[str, any] = json.load(f)
            w.send_flex_message(
                payload.channel_no,
                flex_content=FlexContent(altText="test", contents=j),
            )
        case "!help":
            help_message: str = (
                "test: test\n"
                "/msg: show message payload\n"
                "/flex: send flex message\n"
                "!help: show this message\n"
                "!speed: measure send/receive message speed\n"
            )
            w.send_text_message(payload.channel_no, help_message)
        case "!speed":
            start_time: float = time.time()
            w.send_text_message(payload.channel_no, "start")
            end_time: float = time.time()
            elapsed_time: float = end_time - start_time
            w.send_text_message(payload.channel_no, f"{elapsed_time:.2f} sec")

if __name__ == "__main__":
    works_id: Optional[str] = os.getenv('WORKS_ID')
    password: Optional[str] = os.getenv('WORKS_PASSWORD')

    if not works_id or not password:
        raise ValueError("WORKS_ID and WORKS_PASSWORD environment variables must be set")

    works = LineWorks(works_id=works_id, password=password)

    my_info = works.get_my_info()
    print(f"{my_info=}")

    tracer = LineWorksTracer(works=works)
    tracer.add_trace_func(PacketType.PUBLISH, receive_publish_packet)
    tracer.trace()