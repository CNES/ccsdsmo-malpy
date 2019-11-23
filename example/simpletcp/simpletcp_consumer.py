#! /bin/python

import sys
sys.path.append('../../src')

import mal
import transport
import encoding


def main():

    host = '127.0.0.1'
    port = 8009

    s = transport.TCPSocket()
    enc = encoding.PickleEncoder()
    request = mal.RequestConsumerHandler(s, enc, "myprovider", "live_session")
    request.connect((host, port))
    print("[*] Connected to %s %d" %(host, port))
    request.request("Hello world!".encode('utf8'))
    message = request.receive_response()
    print("[*] Received '{}'".format(message.msg_parts.decode('utf8')))

if __name__ == "__main__":
    main()
