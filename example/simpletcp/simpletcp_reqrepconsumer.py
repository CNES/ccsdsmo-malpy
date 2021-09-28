#! /bin/python3

import sys
sys.path.append('../../src')

from mo import mal
import transport.tcp
import encoding


def main():

    host = '127.0.0.1'
    port = 8009

    s = transport.tcp.TCPSocket()
    enc = encoding.PickleEncoder()
    request = mal.RequestConsumerHandler(s, enc, "myprovider", "live_session")
    request.connect((host, port))
    print("[*] Connected to %s %d" % (host, port))
    request.request("Hello world!".encode('utf8'))
    message = request.receive_response()
    print("[*] Received '{}'".format(message.msg_parts.decode('utf8')))


if __name__ == "__main__":
    main()
