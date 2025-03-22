import os
import json

from line_works.client import LineWorks
from line_works.mqtt.enums.notification_type import NotificationType
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

    if payload.loc_args1 == "test":
        w.send_text_message(payload.channel_no, "ok")

    elif payload.loc_args1 == "/msg":
        w.send_text_message(payload.channel_no, f"{payload!r}")

    elif payload.loc_args1 == "/flex":
        with open("src/sample_flex.json") as f:
            j: dict = json.load(f)
        w.send_flex_message(
            payload.channel_no,
            flex_content=FlexContent(altText="test", contents=j),
        )

    if payload.notification_type == NotificationType.NOTIFICATION_STICKER:
        w.send_text_message(payload.channel_no, "スタンプ")
        w.send_text_message(payload.channel_no, f"{payload.sticker=}")

        w.send_sticker_message(payload.channel_no, payload.sticker)


# 環境変数から認証情報を取得
WORKS_ID = os.getenv('WORKS_ID')
PASSWORD = os.getenv('WORKS_PASSWORD')

if not WORKS_ID or not PASSWORD:
    raise ValueError("WORKS_ID and WORKS_PASSWORD environment variables must be set")

works = LineWorks(works_id=WORKS_ID, password=PASSWORD)

my_info = works.get_my_info()
print(f"{my_info=}")

tracer = LineWorksTracer(works=works)
tracer.add_trace_func(PacketType.PUBLISH, receive_publish_packet)
tracer.trace()