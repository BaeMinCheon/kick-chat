import json
import os
import sys

import rel
import websocket
from curl_cffi import requests
from dateutil.parser import parse

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from kick_chat.constants import RESET, SOCKET_URL
from kick_chat.utils import hex_to_rgb


class Client:
    def __init__(self, *, username: str):
        self.create_file()
        self.chatroom_id = self.username_to_id(username)

    def username_to_id(self, username: str) -> int:
        res = requests.get(
            f"https://kick.com/api/v1/channels/{username}",
            impersonate="chrome110",
        )
        res.raise_for_status()
        data = res.json()
        return data["chatroom"]["id"]

    def subscribe(self, ws):
        ws.send(
            json.dumps(
                {
                    "event": "pusher:subscribe",
                    "data": {
                        "channel": f"chatrooms.{self.chatroom_id}.v2",
                        "auth": "",
                    },
                }
            )
        )

    def messageEvent(self, ws, data):
        time = (
            parse(data["created_at"]).astimezone(tz=None).strftime("%H:%M:%S")
        )
        message = data["content"]
        user = data["sender"]["username"]
        r, g, b = hex_to_rgb(data["sender"]["identity"]["color"])
        fgColorString = f"\033[38;2;{r};{g};{b}m"
        print(f"[{time}] {fgColorString}{user}{RESET}: {message}")
        self.log_chat(time, user, data["sender"]["slug"], message)

    def on_message(self, ws, message):
        res = json.loads(message)
        match res["event"]:
            case "pusher:connection_established":
                self.subscribe(ws)
            case "pusher_internal:subscription_succeeded":
                print("Subscribed ...")
            case "App\\Events\\ChatMessageEvent":
                data = json.loads(res["data"])
                self.messageEvent(ws, data)

    def on_open(self, ws):
        print("Connected ...")

    def listen(self):
        ws = websocket.WebSocketApp(
            SOCKET_URL,
            on_open=self.on_open,
            on_message=self.on_message,
        )
        ws.run_forever(dispatcher=rel, reconnect=5)
        rel.signal(2, rel.abort)
        rel.dispatch()
    
    def create_file(self):
        import datetime
        now = datetime.datetime.now()
        year = now.year
        month = now.month
        day = now.day
        hour = now.hour
        minute = now.minute
        second = now.second
        execution_path = os.path.dirname(sys.argv[0])
        year_path = os.path.join(execution_path, str(year))
        if not os.path.exists(year_path):
            os.makedirs(year_path)
        month_path = os.path.join(year_path, str(month))
        if not os.path.exists(month_path):
            os.makedirs(month_path)
        day_path = os.path.join(month_path, str(day))
        if not os.path.exists(day_path):
            os.makedirs(day_path)
        file_name = f"{year}-{month}-{day}_{hour}-{minute}-{second}.csv"
        self.chat_log_path = os.path.join(day_path, file_name)
        with open(self.chat_log_path, "w+") as chat_log:
            if chat_log is None:
                print("[Error] Failed to create the file for chat log. Contact to the engineer for a help.")
            else:
                print(f"[Success] The file for chat log has been created at {self.chat_log_path}")
            chat_log.write("Time,Username,Slug,Content\n")

    def log_chat(self, time, username, slug, content):
        with open(self.chat_log_path, "a") as chat_log:
            chat_log.write(f"{time},{username},{slug},{content}\n")