import socket as pythonsocket
import time
import http.client, urllib.parse
from email.header import Header, decode_header, make_header

from malpydefinitions import MALPY_ENCODING
from mo import mal

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


class HTTPSocket(TCPSocket):

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
            "Content-Length": len(message.multi_part),
            "X-MAL-Authentication-Id": message.header.auth_id.hex(),
            "X-MAL-URI-From": message.header.uri_from,
            "X-MAL-URI-To": message.header.uri_to,
            "X-MAL-Timestamp": _encode_time(message.header.timestamp),
            "X-MAL-QoSlevel": _encode_qos_level(message.header.qos_level),
            "X-MAL-Priority": str(message.header.priority),
            "X-MAL-Domain": ".".join([ _encode_ascii(x) for x in message.header.domain ]),
            "X-MAL-Network-Zone": _encode_ascii(message.header.network_zone),
            "X-MAL-Session": _encode_session(message.header.session),
            "X-MAL-Session-Name": _encode_ascii(message.header.session_name),
            "X-MAL-Interaction-Type": _encode_ip_type(message.header.ip_type),
            "X-MAL-Interaction-Stage": str(message.header.ip_stage),
            "X-MAL-Transaction-Id": str(message.header.transaction_id),
            "X-MAL-Service-Area": str(message.header.area),
            "X-MAL-Service": str(message.header.service),
            "X-MAL-Operation": str(message.header.operation),
            "X-MAL-Area-Version": str(message.header.area_version),
            "X-MAL-Is-Error-Message": "True" if message.header.is_error_message else "False",
            "X-MAL-Version-Number": str(message.header.version_number)
        }
        if self.encoding == MALPY_ENCODING.XML:
            headers['Content-Type'] = "application/mal-xml"
        else:
            headers['Content-Type'] = "application/mal"
            raise NotImplementedError("Only the XML Encoding is implemented with the HTTP Transport.")
        body = message.multi_part
        self.socket.request("POST", uri, body=body, headers=headers)

    def recv(self):

        response = self.socket.getreponse()
        #if (response.status >= 400):
        #    raise RuntimeError(response.status, response.reason)

        headers = dict(response.getheaders())
        malheader = MALHeader()
        malheader.auth_id = b''.fromhex(headers['X-MAL-Authentication-Id'])
        malheader.uri_from = headers['X-MAL-URI-From']
        malheader.uri_to = headers['X-MAL-URI-To']
        malheader.timestamp = _decode_time(headers['X-MAL-Timestamp'])
        malheader.qos_level = _encode_qos_level(headers['X-MAL-QoSlevel'])
        malheader.priority = int(headers['X-MAL-Priority'])
        malheader.domain = _decode_ascii(headers['X-MAL-Domain']).split('.')
        malheader.network_zone = _decode_ascii(headers['X-MAL-Network-Zone'])
        malheader.session = _decode_session(headers['X-MAL-Session'])
        malheader.session_name = _decode_ascii(headers['X-MAL-Session-Name'])
        malheader.ip_type = _decode_ip_type(headers['X-MAL-Interaction-Type'])
        malheader.ip_stage = int(headers['X-MAL-InteractionStage'])
        malheader.transaction_id = int(headers['X-MAL-Transaction-Id'])
        malheader.area = int(headers['X-MAL-Service-Area'])
        malheader.service = int(headers['X-MAL-Service'])
        malheader.operation = int(headers['X-MAL-Operation'])
        malheader.area_version = int(headers['X-MAL-Area-Version'])
        malheader.is_error_message = (headers["X-MAL-Is-Error-Message"] == "True")
        malheader.version_number = headers['X-MAL-Version-Number']

        if self.encoding == MALPY_ENCODING.XML and headers['Content-Type'] != "application/mal-xml":
            raise RuntimeError("Unexpected encoding. Expected 'application/mal-xml', got '{}'".format(headers['Content-Type']))

        body = response.read()

        return MalMessage(header, body)

    @property
    def uri(self):
        return self.socket.getsockname()

    def _encode_time(t):
        s = time.strftime("%Y-%jT%H:%M:%S", time.localtime(t))
        # Time is in seconds.
        # We retrieve the decimal part only
        # 0.xxxxx and from that 1 -> 4 chars => .xxx
        s += ("%.9f" % (t % 1,))[1:5]
        return s

    def _decode_time(s):
        return time.mktime(time.strptime(s[:-4], "%Y-%jT%H:%M:%S")) + float(s[-4:])

    def _encode_qos_level(qos_level):
        d = {
            mal.QOS_LEVELS.BESTEFFORT: "BESTEFFORT",
            mal.QOS_LEVELS.ASSURED: "ASSURED",
            mal.QOS_LEVELS.QUEUED: "QUEUED",
            mal.QOS_LEVELS.TIMELY: "TIMELY"
        }
        return d[qos_level]

    def _decode_qos_level(qos_level):
        d = {
            "BESTEFFORT": mal.QOS_LEVELS.BESTEFFORT,
            "ASSURED": mal.QOS_LEVELS.ASSURED,
            "QUEUED": mal.QOS_LEVELS.QUEUED,
            "TIMELY": mal.QOS_LEVELS.TIMELY
        }
        return d[qos_level]

    def _encode_session(session):
        d = {
            mal.SESSION_TYPES.LIVE: "LIVE",
            mal.SESSION_TYPES.SIMULATION: "SIMULATION",
            mal.SESSION_TYPES.REPLAY: "REPLAY"
        }
        return d[session]

    def _decode_session(session):
        d = {
            "LIVE": mal.SESSION_TYPES.LIVE,
            "SIMULATION": mal.SESSION_TYPES.SIMULATION,
            "REPLAY": mal.SESSION_TYPES.REPLAY
        }
        return d[session]

    def _encode_ip_type(ip_type):
        d = {
            mal.IP_TYPE.SEND: "SEND",
            mal.IP_TYPE.SUBMIT: "SUBMIT",
            mal.IP_TYPE.REQUEST: "REQUEST",
            mal.IP_TYPE.INVOKE: "INVOKE",
            mal.IP_TYPE.PROGRESS: "PROGRESS",
            mal.IP_TYPE.PUBSUB: "PUBSUB"
        }
        return d[ip_type]

    def _decode_ip_type(ip_type):
        d = {
            "SEND": mal.IP_TYPE.SEND,
            "SUBMIT": mal.IP_TYPE.SUBMIT,
            "REQUEST": mal.IP_TYPE.REQUEST,
            "INVOKE": mal.IP_TYPE.INVOKE,
            "PROGRESS": mal.IP_TYPE.PROGRESS,
            "PUBSUB": mal.IP_TYPE.PUBSUB
        }
        return d[ip_type]

    def _encode_ascii(s):
        return Header(s, "us-ascii").encode()

    def _decode_ascii(s):
        return make_header(decode_header(s))

    def _build_post_request(target, headers, body):
        version = 'HTTP/1.1'
        method = 'POST'
        request = "{method} {target} {version}\r\n".format(method=method, target=target, version=version)
        for h in headers:
            request += "{tocken}: {value}\r\n".format(tocken=h, value=headers[h])
        request+= "\r\n"
        return request

    def _build_post_response(target, status, headers, body):
        version = 'HTTP/1.1'
        request = "{version} {statuscode} {statusmessage}\r\n".format(version=version, statuscode=status.code(statusmessage=status.message))
        for h in headers:
            request += "{tocken}: {value}\r\n".format(tocken=h, value=headers[h])

        request+= "\r\n"
        return request

