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

# class KeywordPair:
#     def __init__(self, keyword, slug):
#         self.keyword = keyword
#         self.slug = slug
    
#     def __str__(self):
#         return f"KeywordPair({self.keyword},{self.slug})"

#     def __eq__(self, other):
#         is_keyword_same = self.keyword == other.keyword
#         is_slug_same = self.slug == other.slug
#         return is_keyword_same and is_slug_same
    
#     def __hash__(self):
#         return hash(self.keyword + self.slug)

class Client:
    def __init__(self, *, username: str, keyword = ""):
        self.username = username
        self.keyword = keyword.lower()
        self.slug_set = set()
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
            parse(data["created_at"]).astimezone(tz=None).strftime("%y-%m-%d %H:%M:%S")
        )
        message = data["content"]
        user = data["sender"]["username"]
        r, g, b = hex_to_rgb(data["sender"]["identity"]["color"])
        fgColorString = f"\033[38;2;{r};{g};{b}m"
        print(f"[{time}] {fgColorString}{user}{RESET}: {message}")
        self.log_chat(time, user, data["sender"]["slug"], message)
        self.filter_with_keyword(time, user, data["sender"]["slug"], message)

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
            on_message=self.on_message, # The callback on_message doesn't throw any exception. So, you should check your codes if new codes in on_message don't work.
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
        chatlog_path = os.path.join(execution_path, "chatlogs")
        if not os.path.exists(chatlog_path):
            os.makedirs(chatlog_path)
        username_path = os.path.join(chatlog_path, self.username)
        if not os.path.exists(username_path):
            os.makedirs(username_path)
        chatlog_filename = f"{year}-{month}-{day}_{hour}-{minute}-{second}.csv"
        self.chat_log_path = os.path.join(username_path, chatlog_filename)
        with open(self.chat_log_path, "w+") as chat_log:
            if chat_log is None:
                print("[Error] Failed to create the file for chat log. Contact to the engineer for a help.")
            else:
                print(f"[Success] The file for chat log has been created at {self.chat_log_path}")
            chat_log.write("Time,Username,Slug,Content\n")
        if self.keyword != "":
            filter_filename = "marble.csv"
            self.filter_path = os.path.join(execution_path, filter_filename)
            if os.path.exists(self.filter_path):
                print(f"[Success] The file for filtering has been found at {self.filter_path}")
                with open(self.filter_path, "r") as filter:
                    contents = filter.readlines()
                    for index in range(1, len(contents)):
                        content = contents[index]
                        data = content.split(",")
                        self.slug_set.add(data[0])
            else:
                with open(self.filter_path, "w+") as filter:
                    if filter is None:
                        print("[Error] Failed to create the file for filtering. Contact to the engineer for a help.")
                    else:
                        print(f"[Success] The file for filtering has been created at {self.filter_path}")
                    filter.write("Slug\n")
        else:
            print("[Notify] The filtering has been deactivated because you did not enter any keyword.")

    def log_chat(self, time, username, slug, content):
        with open(self.chat_log_path, "a") as chat_log:
            chat_log.write(f"{time},{username},{slug},{content}\n")

    def filter_with_keyword(self, time, username, slug, content):
        is_filter_path_valid = self.filter_path != ""
        is_keyword_found = self.keyword in content.lower()
        is_new_user = slug not in self.slug_set
        if is_filter_path_valid and is_keyword_found and is_new_user:
            self.slug_set.add(slug)
            with open(self.filter_path, "a") as filter:
                filter.write(f"{slug}\n")
