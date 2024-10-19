#! /bin/python3

import sys
sys.path.append('../../src')

from malpy.mo import mal
from malpy.transport.tcp import TCPSocket
from malpy.encoding.pickle import PickleEncoder


def main():

    host = '127.0.0.1'
    port = 8009

    s = TCPSocket()
    enc = PickleEncoder()
    request = mal.RequestConsumerHandler(s, enc, "myprovider", "live_session")
    request.connect((host, port))
    print("[*] Connected to %s %d" % (host, port))
    request.request(mal.String("Hello world!"))
    message = request.receive_response(mal.String)
    print("[*] Received '{}'".format(message.msg_parts.internal_value))


if __name__ == "__main__":
    main()
