#!/usr/bin/env python3

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from client import Client

def copy_cert():
    execution_path = os.path.dirname(sys.argv[0])
    cert_path = os.path.join(execution_path , 'cacert.pem')
    mei_path = os.path.dirname(__file__)
    cffi_path = os.path.join(mei_path, "curl_cffi")
    if not os.path.exists(cffi_path):
        os.makedirs(cffi_path)
    new_path = os.path.join(cffi_path, "cacert.pem")
    import shutil
    shutil.copyfile(cert_path, new_path)
    print("original_cert_path: " + cert_path)
    print("copied_cert_path: " + new_path)

def main(argv=sys.argv) -> int:
    if len(argv) < 2:
        print("Usage: kick-chat <channel_name> <keyword:optional>")
        return 1
    if getattr( sys , 'frozen' , None ):
        copy_cert()
    if len(argv) == 2:
        client = Client(username=argv[1])
    if len(argv) > 2:
        client = Client(username=argv[1], keyword=argv[2])
    client.listen()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())