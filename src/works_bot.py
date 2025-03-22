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
import datetime

class BotLogger:
    def __init__(self):
        self.start_time = datetime.datetime.now()
        self.last_receive_time = None
        self.message_count = 0
        self.message_types = {}
        self.command_count = 0
        self.command_types = {}
        self.hourly_stats = {}
        
    def update_stats(self, payload: MessagePayload) -> None:
        self.message_count += 1
        
        # メッセージタイプの統計
        message_type = type(payload).__name__
        self.message_types[message_type] = self.message_types.get(message_type, 0) + 1
        
        # コマンドの統計
        if payload.loc_args1:
            self.command_count += 1
            command = payload.loc_args1
            self.command_types[command] = self.command_types.get(command, 0) + 1
        
        # 時間帯別の統計
        current_hour = datetime.datetime.now().strftime('%H')
        self.hourly_stats[current_hour] = self.hourly_stats.get(current_hour, 0) + 1
        
        self.last_receive_time = datetime.datetime.now()
        
    def generate_stats(self) -> Dict:
        stats = {
            'start_time': self.start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'last_receive_time': self.last_receive_time.strftime('%Y-%m-%d %H:%M:%S') if self.last_receive_time else 'N/A',
            'total_messages': self.message_count,
            'message_types': self.message_types,
            'total_commands': self.command_count,
            'command_types': self.command_types,
            'hourly_stats': self.hourly_stats
        }
        return stats

def receive_publish_packet(w: LineWorks, p: MQTTPacket) -> None:
    payload = p.payload

    if not isinstance(payload, MessagePayload):
        return

    if not payload.channel_no:
        return

    # ログ記録
    logger.update_stats(payload)
    
    # メッセージ処理
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
        print("ERROR: WORKS_ID and WORKS_PASSWORD environment variables are required")
        exit(1)

    # ロガーの初期化
    logger = BotLogger()
    
    # LINE WORKSクライアントの初期化
    works = LineWorks(works_id=works_id, password=password)
    
    # ボットの実行
    tracer = LineWorksTracer(works=works)
    tracer.add_trace_func(PacketType.PUBLISH, receive_publish_packet)
    tracer.trace()