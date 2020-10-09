import socket as pythonsocket
import time
from email.header import Header, decode_header, make_header
from io import BytesIO
from malpydefinitions import MALPY_ENCODING
from mo import mal

from .abstract_transport import MALSocket


def _encode_uri(uri):
    return 'http://{}:{}'.format(uri[0], uri[1])


def _decode_uri(uri):
    splitted_uri = uri.split(':')
    host = splitted_uri[1][2:]  # Remove //
    port = splitted_uri[2]
    return (host, port)


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
        mal.QoSLevel.BESTEFFORT: "BESTEFFORT",
        mal.QoSLevel.ASSURED: "ASSURED",
        mal.QoSLevel.QUEUED: "QUEUED",
        mal.QoSLevel.TIMELY: "TIMELY"
    }
    return d[qos_level]


def _decode_qos_level(qos_level):
    d = {
        "BESTEFFORT": mal.QoSLevel.BESTEFFORT,
        "ASSURED": mal.QoSLevel.ASSURED,
        "QUEUED": mal.QoSLevel.QUEUED,
        "TIMELY": mal.QoSLevel.TIMELY
    }
    return d[qos_level]


def _encode_session(session):
    d = {
        mal.SessionType.LIVE: "LIVE",
        mal.SessionType.SIMULATION: "SIMULATION",
        mal.SessionType.REPLAY: "REPLAY"
    }
    return d[session]


def _decode_session(session):
    d = {
        "LIVE": mal.SessionType.LIVE,
        "SIMULATION": mal.SessionType.SIMULATION,
        "REPLAY": mal.SessionType.REPLAY
    }
    return d[session]


def _encode_ip_type(ip_type):
    d = {
        mal.InteractionType.SEND: "SEND",
        mal.InteractionType.SUBMIT: "SUBMIT",
        mal.InteractionType.REQUEST: "REQUEST",
        mal.InteractionType.INVOKE: "INVOKE",
        mal.InteractionType.PROGRESS: "PROGRESS",
        mal.InteractionType.PUBSUB: "PUBSUB"
    }
    return d[ip_type]


def _decode_enum(value, enumeration):
    for k in enumeration:
        if k.name == value:
            return k
    raise ValueError("{} not found in enumeration {}".format(value, enumeration))


def _encode_ascii(s):
    return Header(s, "us-ascii").encode()


def _decode_ascii(s):
    return str(make_header(decode_header(s)))


class Status:
    def __init__(self, code, message=""):
        self.code = code
        self.message = message


#TODO: check if http uses \r\n \n or anything x...


def _build_post_request(target, headers, body):
    version = 'HTTP/1.1'
    method = 'POST'
    request = "{method} {target} {version}\n".format(
        method=method, target=target, version=version
        ).encode('utf-8')
    for h in headers:
        request += "{token}: {value}\n".format(
            token=h, value=headers[h]
            ).encode('utf-8')
    request += b"\n"
    request += body

    return request


def _read_post_request(request):
    iorequest = BytesIO(request)
    statusline = iorequest.readline().decode('utf8')[:-1]

    method, target, version = statusline.split(' ')
    if version != 'HTTP/1.1':
        msg = "MALpy cannot handle other versions than 'HTTP/1.1', got '{}'".format(version)
        raise RuntimeError(msg)
    if method != 'POST':
        msg = "MALpy only handles POST message, got {}".format(method)
        raise RuntimeError(msg)

    headers = dict()
    while True:
        line = iorequest.readline().decode('utf8')
        if line == "\n":
            break
        else:
            line = line[:-1]  # Remove \n
            key, *values = line.split(': ')
            headers[key] = ': '.join(values)
    body = iorequest.read()
    return headers, body


def _build_post_response(target, status, headers, body):
    version = 'HTTP/1.1'
    request = "{version} {statuscode} {statusmessage}\n".format(
        version=version, statuscode=status.code, statusmessage=status.message
        ).encode('utf8')
    for h in headers:
        request += "{token}: {value}\n".format(
            token=h, value=headers[h]
            ).encode('utf8')

    request += b"\n"
    request += body
    return request


def _read_post_response(response):
    ioresponse = BytesIO(response)
    statusline = ioresponse.readline().decode('utf8')[:-1]
    version, statuscode, *statusmessage = statusline.split(' ')
    headers = dict()
    if version != 'HTTP/1.1':
        msg = "MALpy cannot handle other versions than 'HTTP/1.1', got ''{}'".format(version)
        raise RuntimeError(msg)
    if statuscode != '200':
        raise RuntimeError((statuscode, ' '.join(statusmessage)))
    else:
        while True:
            line = ioresponse.readline().decode('utf8')
            if line == "\n":
                break
            else:
                line = line[:-1]  # Remove \n
                key, *values = line.split(': ')
                headers[key] = ': '.join(values)
        body = ioresponse.read()
    return headers, body


class HTTPSocket(MALSocket):
    _messagesize = 1024

    def __init__(self, socket=None):
        self.expect_response = None
        if socket:
            self.socket = socket
        else:
            self.socket = pythonsocket.socket(pythonsocket.AF_INET,
                                              pythonsocket.SOCK_STREAM)

    def bind(self, uri):
        """ @param uri: (host, port) """
        self.socket.bind(uri)

    def listen(self, unacceptedconnectnb=0):
        self.socket.listen(unacceptedconnectnb)

    def waitforconnection(self):
        conn, _ = self.socket.accept()
        return HTTPSocket(conn)

    def connect(self, uri):
        """ @param uri: (host, port) """
        self.socket.connect(uri)

    def unbind(self):
        self.socket.close()

    def disconnect(self):
        self.socket.close()

    def send(self, message):
        if self.expect_response is None:
            self.expect_response = True
        headers = {
            "Content-Length": len(message),
            "X-MAL-Authentication-Id": message.header.auth_id.hex(),
            "X-MAL-URI-From": message.header.uri_from,
            "X-MAL-URI-To": message.header.uri_to,
            "X-MAL-Timestamp": _encode_time(message.header.timestamp),
            "X-MAL-QoSlevel": message.header.qos_level.name,
            "X-MAL-Priority": str(message.header.priority),
            "X-MAL-Domain": ".".join([ _encode_ascii(x) for x in message.header.domain ]),
            "X-MAL-Network-Zone": _encode_ascii(message.header.network_zone),
            "X-MAL-Session": message.header.session.name,
            "X-MAL-Session-Name": _encode_ascii(message.header.session_name),
            "X-MAL-Interaction-Type": message.header.ip_type.name,
            "X-MAL-Interaction-Stage": message.header.ip_stage.name,
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
        body = message.msg_parts
        if self.expect_response:
            request = _build_post_request(target=_encode_uri(self.uri), body=body, headers=headers)
        else:
            request = _build_post_response(target=_encode_uri(self.uri), body=body, headers=headers, status=Status(200))
        self.socket.send(request)

    def recv(self):
        if self.expect_response is None:
            self.expect_response = False
        message = self.socket.recv(self._messagesize)
        if self.expect_response:
            headers, body = _read_post_response(message)
        else:
            headers, body = _read_post_request(message)

        malheader = mal.MALHeader()
        malheader.auth_id = b''.fromhex(headers['X-MAL-Authentication-Id'])
        malheader.uri_from = headers['X-MAL-URI-From']
        malheader.uri_to = headers['X-MAL-URI-To']
        malheader.timestamp = _decode_time(headers['X-MAL-Timestamp'])
        malheader.qos_level = _decode_qos_level(headers['X-MAL-QoSlevel'])
        malheader.priority = int(headers['X-MAL-Priority'])
        malheader.domain = _decode_ascii(headers['X-MAL-Domain']).split('.')
        malheader.network_zone = _decode_ascii(headers['X-MAL-Network-Zone'])
        malheader.session = _decode_session(headers['X-MAL-Session'])
        malheader.session_name = _decode_ascii(headers['X-MAL-Session-Name'])
        malheader.ip_type = _decode_enum(headers['X-MAL-Interaction-Type'], mal.InteractionType)
        malheader.ip_stage = _decode_enum(headers['X-MAL-Interaction-Stage'], mal.MAL_IP_STAGES)
        malheader.transaction_id = int(headers['X-MAL-Transaction-Id'])
        malheader.area = int(headers['X-MAL-Service-Area'])
        malheader.service = int(headers['X-MAL-Service'])
        malheader.operation = int(headers['X-MAL-Operation'])
        malheader.area_version = int(headers['X-MAL-Area-Version'])
        malheader.is_error_message = (headers["X-MAL-Is-Error-Message"] == "True")
        malheader.version_number = headers['X-MAL-Version-Number']

        if self.encoding == MALPY_ENCODING.XML and headers['Content-Type'] != "application/mal-xml":
            raise RuntimeError("Unexpected encoding. Expected 'application/mal-xml', got '{}'".format(headers['Content-Type']))

        return mal.MALMessage(header=malheader, msg_parts=body)

    @property
    def uri(self):
        return self.socket.getsockname()
