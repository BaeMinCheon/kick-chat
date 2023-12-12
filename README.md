# kick-chat

kick.com chat in the terminal

## About

kick-chat is a terminal chat client for [Kick](https://kick.com/) chat.
It aims to provide a simple and minimalistic way of listening to chat messages.
At the moment displaying emotes in the terminal is not supported :(

## Installation

```
pip install kick-chat
```

## How to use

Simply put Kick username as the first argument to the program call.

```
kick-chat xQc
```

## How to package with PyInstaller

```
pyinstaller main.py --onefile --hidden-import _cffi_backend
```

## License

Licensed under [GPLv3 License](./LICENSE).
