#! /bin/python

import sys
sys.path.append('../../src')

from mo import mal
from transport import http
import encoding


def main():

    host = '127.0.0.1'
    port = 8009

    s = http.HTTPSocket()
    enc = encoding.XMLEncoder()
    request = mal.RequestConsumerHandler(s, enc, "myprovider", mal.SessionType.LIVE)
    request.connect((host, port))
    print("[*] Connected to %s %d" % (host, port))
    request.request(mal.String("Hello world!"))
    message = request.receive_response()
    print("[*] Received '{}'".format(message.msg_parts.decode('utf8')))


if __name__ == "__main__":
    main()
