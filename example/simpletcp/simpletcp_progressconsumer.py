#! /bin/python

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
    progress = mal.ProgressConsumerHandler(s, enc, "myprovider", "live_session")
    progress.connect((host, port))
    print("[*] Connected to %s %d" % (host, port))
    progress.progress("value1".encode('utf8'))
    progress.receive_ack()
    result = b""
    while True:
        partial_result = progress.receive_update()
        if progress.interaction_terminated:
            print("[**] Response: {}".format(partial_result.msg_parts))
            break
        else:
            print("[**] Received part: {}".format(partial_result.msg_parts))
            result += partial_result.msg_parts
    print("[*] Received:\n{}\n{}\n{}".format('-'*10, result.decode('utf8'), '-'*10))

if __name__ == "__main__":
    main()
