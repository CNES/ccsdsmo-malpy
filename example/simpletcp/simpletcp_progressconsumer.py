#! /bin/python3

# SPDX-FileCopyrightText: 2025 Olivier Churlaud <olivier@churlaud.com>
# SPDX-FileCopyrightText: 2025 CNES
#
# SPDX-License-Identifier: MIT

import sys
sys.path.append('../../src')

from malpy.mo import mal
from malpy.transport import tcp
from malpy import encoding


def main():

    host = '127.0.0.1'
    port = 8009

    s = tcp.TCPSocket()
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
