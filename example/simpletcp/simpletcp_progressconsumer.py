#! /bin/python3

import sys
sys.path.append('../../src')

from malpy.mo import mal
from malpy.transport.simpletcp import TCPSocket
from malpy import encoding


def main():

    host = '127.0.0.1'
    port = 8009

    s = TCPSocket()
    enc = encoding.PickleEncoder()
    progress = mal.ProgressConsumerHandler(s, enc, "myprovider")
    progress.connect((host, port))
    print("[*] Connected to %s %d" % (host, port))
    progress.progress("value1".encode('utf8'))
    try:
        message = progress.receive_ack()
    except Exception as e:
        print("Got an error")
        sys.exit(1)
    result = b""
    while True:
        partial_result = progress.receive_update()
        if progress.interaction_terminated:
            print("[**] Response: {}".format(partial_result.msg_parts))
            break
        else:
            print("[**] Received part: {}".format(partial_result.msg_parts[0].internal_value))
            result += partial_result.msg_parts[0].internal_value
    print("[*] Received:\n{}\n{}\n{}".format('-'*10, result.decode('utf8'), '-'*10))

if __name__ == "__main__":
    main()
