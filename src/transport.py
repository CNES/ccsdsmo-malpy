import socket as pythonsocket

import http.client, urllib.parse
from email.header import Header

class MALSocket(object):

    def bind(self, uri):
        raise NotImplementedError("This is to be implemented.")

    def connect(self, uri):
        raise NotImplementedError("This is to be implemented.")

    def unbind(self):
        raise NotImplementedError("This is to be implemented.")

    def disconnect(self):
        raise NotImplementedError("This is to be implemented.")

    def send(self, message):
        raise NotImplementedError("This is to be implemented.")

    def recv(self):
        raise NotImplementedError("This is to be implemented.")
        message = b""
        return message

class TCPSocket(MALSocket):

    _messagesize = 1024

    def __init__(self, socket = None):
        if socket:
            self.socket = socket
        else:
            self.socket = pythonsocket.socket(pythonsocket.AF_INET, pythonsocket.SOCK_STREAM)

    def bind(self, uri):
        """ @param uri: (host, port) """
        self.socket.bind(uri)

    def listen(self, unacceptedconnectnb=0):
        self.socket.listen(unacceptedconnectnb)

    def waitforconnection(self):
        conn, _ = self.socket.accept()
        return TCPSocket(conn)

    def connect(self, uri):
        """ @param uri: (host, port) """
        self.socket.connect(uri)

    def unbind(self):
        self.socket.close()

    def disconnect(self):
        self.socket.close()

    def send(self, message):
        self.socket.send(message)

    def recv(self):
        return self.socket.recv(self._messagesize)

    @property
    def uri(self):
        return self.socket.getsockname()


class HTTPSocket(MALSocket):

    _messagesize = 1024

    def __init__(self, socket = None):
        if socket:
            self.socket = socket
        else:
            self.socket = pythonsocket.socket(pythonsocket.AF_INET, pythonsocket.SOCK_STREAM)

    def bind(self, uri):
        """ @param uri: (host, port) """
        self.socket.bind(uri)

    def listen(self, unacceptedconnectnb=0):
        self.socket.listen(unacceptedconnectnb)

    def waitforconnection(self):
        conn, _ = self.socket.accept()
        return TCPSocket(conn)

    def connect(self, uri):
        """ @param uri: (host, port) """
        self.socket = http.client.HTTPConnection(uri)

    def unbind(self):
        self.socket.close()

    def disconnect(self):
        self.socket.close()

    def send(self, message):
        headers = {
            "Content-Type": "application/mal",
            "Content-Length": len(message.multi_part)
            "X-MAL-Authentication-Id": message.header.auth_id.hex(),
            "X-MAL-URI-From": message.header.uri_from,
            "X-MAL-URI-To": message.header.uri_to,
            "X-MAL-URI-From": message.header.uri_from,
            "X-MAL-Timestamp": _format_time(message.header.timestamp)
            "X-MAL-QoSlevel": _format_qos_level(message.header.qos_level),
            "X-MAL-Priority": str(message.header.priority),
            "X-MAL-Domain": ".".join([ _format_ascii(x) for x in message.header.domain ]),
            "X-MAL-Network-Zone": _format_ascii(message.header.network_zone),
            "X-MAL-Session": _format_session(message.header.session),
            "X-MAL-Session-Name": _format_ascii(message.header.session_name),
            "X-MAL-Interaction-Type": message.header.ip_type,
            "X-MAL-Interaction-Stage": str(message.header.ip_stage),
            "X-MAL-Transaction-Id": str(message.header.transaction_id),
            "X-MAL-Service-Area": str(message.header.area),
            "X-MAL-Service": str(message.header.service),
            "X-MAL-Operation": str(message.header.operation),
            "X-MAL-Area-Version": str(message.header.area_version),
            "X-MAL-Is-Error-Message": "True" if message.header.is_error_message else "False",
            "X-MAL-Encoding": message.header.encoding,
            "X-MAL-Version-Number": message.header.version_number
        }
        body = message.multi_part
        self.socket.request("POST", uri, body=body, headers=headers)

    def recv(self):
        response = self.socket.getreponse()
        if (response.status >= 400):
            RuntimeException((response.status, response.reason))
        return response.read()

    @property
    def uri(self):
        return self.socket.getsockname()

    def _format_time(t):
        s = time.strftime("%Y-%jT%H:%M:%S", time.localtime(t))
        # Time is in seconds.
        # We retrieve the decimal part only
        # 0.xxxxx and from that 1 -> 4 chars => .xxx
        s += ("%.9f" % (t % 1,))[1:5]
        return s

    def _format_qos_level(qos_level):
        d = {
            mal.QOS_LEVELS.BESTEFFORT: "BESTEFFORT",
            mal.QOS_LEVELS.ASSURED: "ASSURED",
            mal.QOS_LEVELS.QUEUED: "QUEUED",
            mal.QOS_LEVELS.TIMELY: "TIMELY"
        }
        return d[qos_level]

    def _format_session(session):
        d = {
            mal.SESSION_TYPES.LIVE: "LIVE",
            mal.SESSION_TYPES.SIMULATION: "SIMULATION",
            mal.SESSION_TYPES.REPLAY: "REPLAY"
        }
        return d[session]


    def _format_ip_type(ip_type):
        d = {
            mal.IP_TYPE.SEND: "SEND",
            mal.IP_TYPE.SUBMIT: "SUBMIT",
            mal.IP_TYPE.REQUEST: "REQUEST",
            mal.IP_TYPE.INVOKE: "INVOKE",
            mal.IP_TYPE.PROGRESS: "PROGRESS",
            mal.IP_TYPE.PUBSUB: "PUBSUB"
        }
        return d[ip_type]

    def _format_ascii(s):
        return Header(s, "us-ascii").encode()
