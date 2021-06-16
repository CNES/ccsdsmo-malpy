import socket as pythonsocket
import time
import pickle
import http.client

from email.header import Header, decode_header, make_header
from io import BytesIO
from malpydefinitions import MALPY_ENCODING
from mo import mal

from .abstract_transport import MALSocket


def _encode_uri(uri):
    return '{}:{}'.format(uri[0], uri[1])


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

class HTTPSocket(MALSocket):
    _messagesize = 1024

    def __init__(self, socket=None, CONTEXT=None, HOST=None, URI = None):
        self.expect_response = None
        self.CONTEXT=CONTEXT
        if socket:
            self.socket = socket
        else:
            self.socket = pythonsocket.socket(pythonsocket.AF_INET,
                                              pythonsocket.SOCK_STREAM)
        self._HOST=HOST
        self._PORT=URI


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
        #self.socket.connect(uri)
        self._HOST=uri[0]
        self._PORT=uri[1]
        self.client = http.client.HTTPSConnection(self._HOST, self._PORT, context=self.CONTEXT)
        self.client.set_debuglevel(1)
		
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
            "X-MAL-URI-From": _encode_uri(message.header.uri_from),
            "X-MAL-URI-To": message.header.uri_to,
            "X-MAL-Timestamp": _encode_time(message.header.timestamp),
            "X-MAL-QoSlevel": message.header.qos_level.name,
            "X-MAL-Priority": str(message.header.priority),
            "X-MAL-Domain": ".".join([ _encode_ascii(x) for x in message.header.domain ]),
            "X-MAL-Network-Zone": _encode_ascii(message.header.network_zone),
            "X-MAL-Session": message.header.session,
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
            print("passe par là {}".format(_encode_uri(self.uri)))
            request = self._send_post_request(target=_encode_uri(self.uri), body=body, headers=headers)
            headers, body=self._receive_post_response()
            print("headers [{}] , body [{}]".format(headers,body))
            return (headers, body)
        else:
            print("passe par ici")
            return (_encode_uri(self.uri), body, headers, 200)

    def recv(self, headers, body):
        if self.expect_response is None:
            self.expect_response = False
     #   message = self.socket.recv(self._messagesize)
     #   if self.expect_response:
     #       headers, body = _read_post_response(message)
     #   else:
     #       headers, body = _read_post_request(message)

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
        #return self.socket.getsockname()
        return (self._HOST,self._PORT)

    def _send_post_request(self, target, headers, body):

	#modif httpsconnection request method header body en sendpostrequest
        self.client.request('POST', url=target, body=body, headers=headers)

    def _receive_post_response(self):
	#devenir httpsConnection getresponse  ajout erreur
        response=self.client.getresponse()
        headers=response.headers
        body=response.read().decode('utf-8')
        return headers, body

    def _receive_post_request(self,request):
        message=self.socket.recv()
        Header,Body=pickle.loads(message)
        return headers, body

    def _send_post_response(target, status, headers, body):
        request_dict={
        "target":"",
        "status":"",
        "headers":"",
        "body":""
        }
        self.socket.send(request_dict)


