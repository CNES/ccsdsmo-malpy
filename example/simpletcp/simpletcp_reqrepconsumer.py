#! /bin/python3

import sys
sys.path.append('../../src')

from malpy.mo import mal
from malpy.transport import tcp
from malpy import encoding


class MyRequestConsumerHandler(mal.RequestConsumerHandler):
    AREA = 100
    AREA_VERSION = 1
    SERVICE = 1
    OPERATION = 1


def main():

    host = '127.0.0.1'
    port = 8009

    s = tcp.TCPSocket()
    enc = encoding.PickleEncoder()
    request = MyRequestConsumerHandler(s, enc, "myprovider")
   
    request.connect((host, port))
    print("[*] Connected to %s %d" % (host, port))
    request.request("Hello world!".encode('utf8'))
    try:
        message = request.receive_response()
        print("[*] Received '{}'".format(message.msg_parts.decode('utf8')))
    except mal.MALError as e:
        print("[!] Received an error")
        print(e)
    except RuntimeError as e:
        print(e)

if __name__ == "__main__":
    main()
