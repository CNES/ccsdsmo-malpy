import time
from enum import IntEnum
from .maltypes import QoSLevel, SessionType, InteractionType, number


class MAL_IP_STAGES(IntEnum):
    SEND = 0
    SUBMIT = 1
    SUBMIT_ACK = 2
    REQUEST = 3
    REQUEST_RESPONSE = 4
    INVOKE = 5
    INVOKE_ACK = 6
    INVOKE_RESPONSE = 7
    PROGRESS = 8
    PROGRESS_ACK = 9
    PROGRESS_UPDATE = 10
    PROGRESS_RESPONSE = 11
    PUBSUB_REGISTER = 12
    PUBSUB_REGISTER_ACK = 13
    PUBSUB_PUBLISH_REGISTER = 14
    PUBSUB_PUBLISH_REGISTER_ACK = 15
    PUBSUB_PUBLISH = 16
    PUBSUB_NOTIFY = 17
    PUBSUB_DEREGISTER = 18
    PUBSUB_DEREGISTER_ACK = 19
    PUBSUB_PUBLISH_DEREGISTER = 20
    PUBSUB_PUBLISH_DEREGISTER_ACK = 21


class MAL_IP_ERRORS(IntEnum):
    SUBMIT_ERROR = 2
    REQUEST_ERROR = 4
    INVOKE_ACK_ERROR = 6
    INVOKE_RESPONSE_ERROR = 7
    PROGRESS_ACK_ERROR = 9
    PROGRESS_UPDATE_ERROR = 10
    PROGRESS_RESPONSE_ERROR = 11
    PUBSUB_REGISTER_ACK_ERROR = 13
    PUBSUB_PUBLISH_REGISTER_ERROR = 14
    PUBSUB_PUBLISH_ERROR = 16
    PUBSUB_NOTIFY_ERROR = 17


class MalformedMessageError(Exception):
    pass


class InvalidIPStageError(Exception):
    pass


class BackendShutdown(Exception):
    pass


class MALHeader(object):
    """
    A MALHeader objects in the python representation of the
    MAL message header
    """

    # TODO: This object is a great candidate for a Cython cpdef struct
    # which will allow fast copies and attribute affectations.

    __slots__ = ['version_number', 'ip_type', 'ip_stage',
                 'area', 'service', 'operation', 'area_version',
                 'is_error_message', 'qos_level', 'session',
                 'transaction_id', 'priority', 'uri_from',
                 'uri_to', 'timestamp', 'network_zone',
                 'session_name', 'domain', 'auth_id']

    def __init__(self):
        self.version_number = None
        self.ip_type = None
        self.ip_stage = None
        self.area = None
        self.service = None
        self.operation = None
        self.area_version = None
        self.is_error_message = None
        self.qos_level = None
        self.session = None
        self.transaction_id = None
        self.priority = None
        self.uri_from = None
        self.uri_to = None
        self.timestamp = None
        self.network_zone = None
        self.session_name = None
        self.domain = None
        self.auth_id = None

    def copy(self):
        instance = self.__class__()
        instance.version_number = self.version_number
        instance.ip_type = self.ip_type
        instance.ip_stage = self.ip_stage
        instance.area = self.area
        instance.service = self.service
        instance.operation = self.operation
        instance.area_version = self.area_version
        instance.is_error_message = self.is_error_message
        instance.qos_level = self.qos_level
        instance.session = self.session
        instance.transaction_id = self.transaction_id
        instance.priority = self.priority
        instance.uri_from = self.uri_from
        instance.uri_to = self.uri_to
        instance.timestamp = self.timestamp
        instance.network_zone = self.network_zone
        instance.session_name = self.session_name
        instance.domain = self.domain
        instance.auth_id = self.auth_id
        return instance


class MALMessage(object):
    """
    A simple structure to hold a decoded MAL header
    and a set of encoded message parts.
    """

    def __init__(self, header=None, msg_parts=[]):
        self.header = header or MALHeader()
        self.msg_parts = msg_parts

    def __len__(self):
        def _sublen(k):
            if type(k) is list:
                return sum([_sublen(x) for x in k])
            else:
                return len(k)

        return _sublen(self.msg_parts)


class Handler(object):
    AREA = None
    AREA_VERSION = 1
    SERVICE = None
    OPERATION = None

    def __init__(self, transport, encoding):
        self.transport = transport
        self.encoding = encoding
        self.transport.parent = self
        self.encoding.parent = self

    def send_message(self, message):
        message = self.encoding.encode(message)
        return self.transport.send(message)

    def receive_message(self):
        message = self.transport.recv()     
        return self.encoding.decode(message)


class ConsumerHandler(Handler):
    """
    A consumer handler is a logical structure composed of a set of
    MAL message processing functions for the consumer side of a MAL
    operation. This set of functions depends on the interaction pattern
    of the operation (send, submit, progress etc.).
    The lifespan of the consumer handler is the lifespan of the
    transaction (from the initiation of the operation from the consumer,
    to the final response of the provider)
    """

    IP_TYPE = None
    _transaction_id_counter = 0

    @classmethod
    def get_new_transaction_id(cls):
        cls._transaction_id_counter += 1
        return cls._transaction_id_counter

    def __init__(self, transport, encoding, provider_uri="", consumer_uri="", 
                 session=SessionType.LIVE, session_name="", domain=[], network_zone=None,
                 priority=0, auth_id=b"", qos_level=QoSLevel.BESTEFFORT):
        super().__init__(transport, encoding)
        self.consumer_uri = consumer_uri
        self.provider_uri = provider_uri
        self.session = session
        self.session_name = session_name
        self.domain = domain
        self.network_zone = network_zone
        self.priority = priority
        self.auth_id = auth_id
        self.qos_level = qos_level
        self.interaction_terminated = False
        self.transaction_id = self.get_new_transaction_id()

    def create_message_header(self, ip_stage):
        header = MALHeader()
        header.ip_type = self.IP_TYPE
        header.ip_stage = ip_stage
        header.area = self.AREA
        header.service = self.SERVICE
        header.operation = self.OPERATION
        header.area_version = self.AREA_VERSION
        header.is_error_message = None
        header.qos_level = self.qos_level
        header.session = self.session
        header.transaction_id = self.transaction_id
        header.priority = self.priority
        header.uri_from = self.consumer_uri
        header.uri_to = self.provider_uri
        header.timestamp = time.time()
        header.network_zone = self.network_zone
        header.session_name = self.session_name
        header.domain = self.domain
        header.auth_id = self.auth_id
        return header

    def connect(self, uri):
        self.transport.connect(uri)


class ProviderHandler(Handler):
    """
    A provider handler is a logical structure composed of a set of
    MAL message processing functions for the provider side of a MAL
    operation. This set of functions depends on the interaction pattern
    of the operation (send, submit, progress etc.).
    The lifespan of the provider handler is the lifespan of the
    transaction (from the initiation of the operation from the consumer,
    to the final response of the provider)
    """

    AREA = None
    AREA_VERSION = 1
    SERVICE = None
    OPERATION = None

    def __init__(self, transport, encoding):
        super().__init__(transport, encoding)

    def define_header(self, received_message_header):
        self.response_header = received_message_header.copy()
        uri_from = self.response_header.uri_to
        self.response_header.uri_to = self.response_header.uri_from
        self.response_header.uri_from = uri_from

    def create_message_header(self, ip_stage, is_error_message=False):
        header = self.response_header.copy()
        header.ip_stage = ip_stage
        header.is_error_message = is_error_message
        return header


class SendProviderHandler(ProviderHandler):
    """
    A provider handler for operations belonging to the SEND
    interaction pattern
    """

    def receive_send(self):
        message = self.receive_message()
        ip_stage = message.header.ip_stage
        is_error_message = message.header.is_error_message
        if not is_error_message and ip_stage == MAL_IP_STAGES.SEND:
            self.interaction_terminated = True
            return message
        else:
            raise InvalidIPStageError("In %s. Expected SEND. Got %s" %
                                      (self.__class__.__name__, ip_stage))


class SendConsumerHandler(ConsumerHandler):
    """
    A consumer handler for operations belonging to the SEND
    interaction pattern
    """

    IP_TYPE = InteractionType.SEND

    def send(self, body):
        header = self.create_message_header(MAL_IP_STAGES.SEND)
        message = MALMessage(header=header, msg_parts=body)
        self.send_message(message)
        self.interaction_terminated = True


class SubmitProviderHandler(ProviderHandler):
    """
    A provider handler for operations belonging to the SEND
    interaction pattern
    """

    def receive_submit(self):
        message = self.receive_message()
        self.define_header(message.header)
        ip_stage = message.header.ip_stage
        is_error_message = message.header.is_error_message
        if not is_error_message and ip_stage == MAL_IP_STAGES.SUBMIT:
            return message
        else:
            raise InvalidIPStageError("In %s. Expected SUBMIT. Got %s" %
                                      (self.__class__.__name__, ip_stage))

    def ack(self, body, async_send=False):
        header = self.create_message_header(MAL_IP_STAGES.SUBMIT_ACK)
        message = MALMessage(header=header, msg_parts=body)
        self.interaction_terminated = True
        return self.send_message(message)

    def error(self, body):
        header = self.create_message_header(MAL_IP_ERRORS.SUBMIT_ERROR)
        message = MALMessage(header=header, msg_parts=body)
        self.interaction_terminated = True
        return self.send_message(message)


class SubmitConsumerHandler(ConsumerHandler):
    """
    A consumer handler for operations belonging to the SEND
    interaction pattern
    """

    IP_TYPE = InteractionType.SUBMIT

    def submit(self, body):
        header = self.create_message_header(MAL_IP_STAGES.SUBMIT)
        message = MALMessage(header=header, msg_parts=body)
        self.send_message(message)

    def receive_ack(self):
        message = self.receive_message()
        ip_stage = message.header.ip_stage
        is_error_message = message.header.is_error_message
        if not is_error_message and ip_stage == MAL_IP_STAGES.SUBMIT_ACK:
            self.interaction_terminated = True
            return message
        elif is_error_message and ip_stage == MAL_IP_ERRORS.SUBMIT_ERROR:
            self.interaction_terminated = True
            raise RuntimeError(message)
        else:
            raise InvalidIPStageError("In %s. Expected SUBMIT_ACK. Got %s" %
                                      (self.__class__.__name__, ip_stage))


class RequestProviderHandler(ProviderHandler):
    """
    A provider handler for operations belonging to the SEND
    interaction pattern
    """

    def receive_request(self):
        message = self.receive_message()
        self.define_header(message.header)
        ip_stage = message.header.ip_stage
        is_error_message = message.header.is_error_message
        if not is_error_message and ip_stage == MAL_IP_STAGES.REQUEST:
            return message
        else:
            raise InvalidIPStageError("In %s. Expected REQUEST. Got %s" %
                                      (self.__class__.__name__, ip_stage))

    def response(self, body, async_send=False):
        header = self.create_message_header(MAL_IP_STAGES.REQUEST_RESPONSE)
        message = MALMessage(header=header, msg_parts=body)
        self.interaction_terminated = True
        return self.send_message(message)

    def error(self, body):
        header = self.create_message_header(MAL_IP_ERRORS.REQUEST_ERROR)
        message = MALMessage(header=header, msg_parts=body)
        self.interaction_terminated = True
        return self.send_message(message)


class RequestConsumerHandler(ConsumerHandler):
    """
    A consumer handler for operations belonging to the SEND
    interaction pattern
    """

    IP_TYPE = InteractionType.REQUEST

    def request(self, body):
        header = self.create_message_header(MAL_IP_STAGES.REQUEST)
        message = MALMessage(header=header, msg_parts=body)
        return self.send_message(message)

    def receive_response(self):
        message = self.receive_message()
        ip_stage = message.header.ip_stage
        is_error_message = message.header.is_error_message
        if not is_error_message and ip_stage == MAL_IP_STAGES.REQUEST_RESPONSE:
            self.interaction_terminated = True
            return message
        elif is_error_message and ip_stage == MAL_IP_ERRORS.REQUEST_ERROR:
            self.interaction_terminated = True
            raise RuntimeError(message)
        else:
            raise InvalidIPStageError("In %s. Expected REQUEST_ERROR. Got %s" %
                                      (self.__class__.__name__, ip_stage))


class InvokeProviderHandler(ProviderHandler):
    """
    A provider handler for operations belonging to the SEND
    interaction pattern
    """

    def receive_invoke(self):
        message = self.receive_message()
        self.define_header(message.header)
        ip_stage = message.header.ip_stage
        is_error_message = message.header.is_error_message
        if not is_error_message and ip_stage == MAL_IP_STAGES.INVOKE:
            return message
        else:
            raise InvalidIPStageError("In %s. Expected INVOKE. Got %s" %
                                      (self.__class__.__name__, ip_stage))

    def ack(self, body, async_send=False):
        header = self.create_message_header(MAL_IP_STAGES.INVOKE_ACK)
        message = MALMessage(header=header, msg_parts=body)
        return self.send_message(message)

    def ack_error(self, body):
        header = self.create_message_header(MAL_IP_ERRORS.INVOKE_ACK_ERROR)
        message = MALMessage(header=header, msg_parts=body)
        return self.send_message(message)

    def response(self, body, async_send=False):
        header = self.create_message_header(MAL_IP_STAGES.INVOKE_RESPONSE)
        message = MALMessage(header=header, msg_parts=body)
        self.interaction_terminated = True
        return self.send_message(message)

    def response_error(self, body):
        header = self.create_message_header(MAL_IP_ERRORS.INNVOKE_ERROR)
        message = MALMessage(header=header, msg_parts=body)
        self.interaction_terminated = True
        return self.send_message(message)


class InvokeConsumerHandler(ConsumerHandler):
    """
    A consumer handler for operations belonging to the SEND
    interaction pattern
    """

    IP_TYPE = InteractionType.INVOKE

    def invoke(self, body):
        header = self.create_message_header(MAL_IP_STAGES.INVOKE)
        message = MALMessage(header=header, msg_parts=body)
        self.send_message(message)
        self.interaction_terminated = True

    def receive_ack(self):
        message = self.receive_message()
        ip_stage = message.header.ip_stage
        is_error_message = message.header.is_error_message
        if not is_error_message and ip_stage == MAL_IP_STAGES.INVOKE_ACK:
            return message
        elif is_error_message and ip_stage == MAL_IP_ERRORS.INVOKE_ACK_ERROR:
            raise RuntimeError(message)
        else:
            raise InvalidIPStageError("In %s. Expected INVOKE_ACK. Got %s" %
                                      (self.__class__.__name__, ip_stage))

    def receive_response(self):
        message = self.receive_message()
        ip_stage = message.header.ip_stage
        is_error_message = message.header.is_error_message
        if not is_error_message and ip_stage == MAL_IP_STAGES.INVOKE_RESPONSE:
            self.interaction_terminated = True
            return message
        elif is_error_message and ip_stage == MAL_IP_ERRORS.INVOKE_RESPONSE_ERROR:
            self.interaction_terminated = True
            raise RuntimeError(message)
        else:
            raise InvalidIPStageError("In %s. Expected INVOKE_RESPONSE. Got %s" %
                                      (self.__class__.__name__, ip_stage))


class ProgressProviderHandler(ProviderHandler):
    """
    A provider handler for operations belonging to the SEND
    interaction pattern
    """

    def receive_progress(self):
        message = self.receive_message()
        self.define_header(message.header)
        ip_stage = message.header.ip_stage
        is_error_message = message.header.is_error_message
        if not is_error_message and ip_stage == MAL_IP_STAGES.PROGRESS:
            return message
        else:
            raise InvalidIPStageError("In %s. Expected PROGRESS. Got %s" %
                                      (self.__class__.__name__, ip_stage))

    def ack(self, body, async_send=False):
        header = self.create_message_header(MAL_IP_STAGES.PROGRESS_ACK)
        message = MALMessage(header=header, msg_parts=body)
        return self.send_message(message)

    def ack_error(self, body):
        header = self.create_message_header(MAL_IP_ERRORS.PROGRESS_ACK_ERROR)
        message = MALMessage(header=header, msg_parts=body)
        return self.send_message(message)

    def update(self, body):
        header = self.create_message_header(MAL_IP_STAGES.PROGRESS_UPDATE)
        message = MALMessage(header=header, msg_parts=body)
        return self.send_message(message)

    def update_error(self, body):
        header = self.create_message_header(MAL_IP_ERRORS.PROGRESS_UPDATE_ERROR)
        message = MALMessage(header=header, msg_parts=body)
        return self.send_message(message)

    def response(self, body, async_send=False):
        header = self.create_message_header(MAL_IP_STAGES.PROGRESS_RESPONSE)
        message = MALMessage(header=header, msg_parts=body)
        self.interaction_terminated = True
        return self.send_message(message)

    def response_error(self, body):
        header = self.create_message_header(MAL_IP_ERRORS.PROGRESS_RESPONSE_ERROR)
        message = MALMessage(header=header, msg_parts=body)
        self.interaction_terminated = True
        return self.send_message(message)


class ProgressConsumerHandler(ConsumerHandler):
    """
    A consumer handler for operations belonging to the SEND
    interaction pattern
    """

    IP_TYPE = InteractionType.PROGRESS

    def progress(self, body):
        header = self.create_message_header(MAL_IP_STAGES.PROGRESS)
        message = MALMessage(header=header, msg_parts=body)
        self.send_message(message)

    def receive_ack(self):
        message = self.receive_message()
        ip_stage = message.header.ip_stage
        is_error_message = message.header.is_error_message
        if not is_error_message and ip_stage == MAL_IP_STAGES.PROGRESS_ACK:
            return message
        elif is_error_message and ip_stage == MAL_IP_ERRORS.PROGRESS_ACK_ERROR:
            raise RuntimeError(message)
        else:
            raise InvalidIPStageError("In %s. Expected PROGRESS_ACK. Got %s" %
                                      (self.__class__.__name__, ip_stage))

    def receive_update(self):
        """ As it is not possible to know beforehand if the received message is
        an update or the final response, we only do receive_update. The content of
        the header message will let us know te corresponding state.
        """
        message = self.receive_message()
        ip_stage = message.header.ip_stage
        is_error_message = message.header.is_error_message
        if not is_error_message and ip_stage == MAL_IP_STAGES.PROGRESS_UPDATE:
            return message
        elif not is_error_message and ip_stage == MAL_IP_STAGES.PROGRESS_RESPONSE:
            self.interaction_terminated = True
            return message
        elif is_error_message and ip_stage == MAL_IP_ERRORS.PROGRESS_UPDATE_ERROR:
            self.interaction_terminated = True
            raise RuntimeError(message)
        elif is_error_message and ip_stage == MAL_IP_ERRORS.PROGRESS_RESPONSE_ERROR:
            self.interaction_terminated = True
            raise RuntimeError(message)
        else:
            raise InvalidIPStageError("In %s. Expected PROGRESS_UPDATE or PROGRESS_RESPONSE. Got %s" %
                                      (self.__class__.__name__, ip_stage))

#    def receive_response(self):
#        message = self.receive_message()
#        ip_stage = message.header.ip_stage
#        if ip_stage == MAL_IP_STAGES.PROGRESS_RESPONSE:
#            self.interaction_terminated = True
#            return message
#        elif ip_stage == MAL_IP_STAGES.PROGRESS_RESPONSE_ERROR:
#            self.interaction_terminated = True
#            raise RuntimeError(message)
#        else:
#            raise InvalidIPStageError("In %s. Expected PROGRESS_RESPONSE. Got %s" %
#                                      (self.__class__.__name__, ip_stage))


class PubSubProviderHandler(ProviderHandler):

    def receive_registration_message(self):
        message = self.receive_message()
        self.define_header(message.header)
        ip_stage = message.header.ip_stage
        is_error_message = message.header.is_error_message
        if not is_error_message and ip_stage == MAL_IP_STAGES.PUBSUB_REGISTER:
            return message
        elif not is_error_message and ip_stage == MAL_IP_STAGES.PUBSUB_DEREGISTER:
            return message
        else:
            raise InvalidIPStageError("In %s. Expected PUBSUB_REGISTER or PUBSUB_DEREGISTER. Got %s" %
                                      (self.__class__.__name__, ip_stage))

    def register_ack(self, body):
        header = self.create_message_header(MAL_IP_STAGES.PUBSUB_REGISTER_ACK)
        message = MALMessage(header=header, msg_parts=body)
        self.send_message(message)

    def register_error(self, body):
        header = self.create_message_header(MAL_IP_STAGES.PUBSUB_REGISTER_ACK_ERROR)
        message = MALMessage(header=header, msg_parts=body)
        self.send_message(message)

    def deregister_ack(self, body):
        header = self.create_message_header(MAL_IP_STAGES.PUBSUB_DEREGISTER_ACK)
        message = MALMessage(header=header, msg_parts=body)
        self.send_message(message)

    def deregister_error(self, body):
        header = self.create_message_header(MAL_IP_STAGES.PUBSUB_DEREGISTER_ACK_ERROR)
        message = MALMessage(header=header, msg_parts=body)
        self.send_message(message)

    def notify(self, body):
        header = self.create_message_header(MAL_IP_STAGES.PUBSUB_NOTIFY)
        message = MALMessage(header=header, msg_parts=body)
        self.send_message(message)

    def notify_error(self, body):
        header = self.create_message_header(MAL_IP_STAGES.PUBSUB_NOTIFY_ERROR)
        message = MALMessage(header=header, msg_parts=body)
        self.send_message(message)

    def publish_register(self, body):
        header = self.create_message_header(MAL_IP_STAGES.PUBSUB_PUBLISH_REGISTER)
        message = MALMessage(header=header, msg_parts=body)
        self.send_message(message)

    def receive_publish_register_ack(self):
        message = self.receive_message()
        ip_stage = message.header.ip_stage
        is_error_message = message.header.is_error_message
        if not is_error_message and ip_stage == MAL_IP_STAGES.PUBSUB_PUBLISH_REGISTER_ACK:
            return message
        elif is_error_message and ip_stage == MAL_IP_ERRORS.PUBSUB_PUBLISH_REGISTER_ERROR:
            raise RuntimeError(message)
        else:
            raise InvalidIPStageError("In %s. Expected PUBSUB_PUBLISH_REGISTER_ACK. Got %s" %
                                      (self.__class__.__name__, ip_stage))

    def publish_deregister(self, body):
        header = self.create_message_header(MAL_IP_STAGES.PUBSUB_PUBLISH_DEREGISTER)
        message = MALMessage(header=header, msg_parts=body)
        self.send_message(message)

    def receive_publish_deregister_ack(self):
        message = self.receive_message()
        ip_stage = message.header.ip_stage
        is_error_message = message.header.is_error_message
        if not is_error_message and ip_stage == MAL_IP_STAGES.PUBSUB_PUBLISH_DEREGISTER_ACK:
            return message
        else:
            raise InvalidIPStageError("In %s. Expected PUBSUB_PUBLISH_REGISTER_ACK. Got %s" %
                                      (self.__class__.__name__, ip_stage))

    def publish(self, body):
        header = self.create_message_header(MAL_IP_STAGES.PUBSUB_PUBLISH)
        message = MALMessage(header=header, msg_parts=body)
        self.send_message(message)

    def receive_publish_error(self):
        message = self.receive_message()
        ip_stage = message.header.ip_stage
        is_error_message = message.header.is_error_message
        if is_error_message and ip_stage == MAL_IP_ERRORS.PUBSUB_PUBLISH_ERROR:
            return message
        else:
            raise InvalidIPStageError("In %s. Expected PUBSUB_PUBLISH_ERROR. Got %s" %
                                      (self.__class__.__name__, ip_stage))


class PubSubBrokerHandler(ProviderHandler):

    def receive_registration_message(self):
        message = self.receive_message()
        self.define_header(message.header)
        ip_stage = message.header.ip_stage
        is_error_message = message.header.is_error_message
        if not is_error_message and ip_stage == MAL_IP_STAGES.PUBSUB_REGISTER:
            return message
        elif not is_error_message and ip_stage == MAL_IP_STAGES.PUBSUB_DEREGISTER:
            return message
        else:
            raise InvalidIPStageError("In %s. Expected PUBSUB_REGISTER or PUBSUB_DEREGISTER. Got %s" %
                                      (self.__class__.__name__, ip_stage))

    def register_ack(self, body):
        header = self.create_message_header(MAL_IP_STAGES.PUBSUB_REGISTER_ACK)
        message = MALMessage(header=header, msg_parts=body)
        self.send_message(message)

    def register_error(self, body):
        header = self.create_message_header(MAL_IP_STAGES.PUBSUB_REGISTER_ACK_ERROR)
        message = MALMessage(header=header, msg_parts=body)
        self.send_message(message)

    def deregister_ack(self, body):
        header = self.create_message_header(MAL_IP_STAGES.PUBSUB_DEREGISTER_ACK)
        message = MALMessage(header=header, msg_parts=body)
        self.send_message(message)

    def deregister_error(self, body):
        header = self.create_message_header(MAL_IP_STAGES.PUBSUB_DEREGISTER_ACK_ERROR)
        message = MALMessage(header=header, msg_parts=body)
        self.send_message(message)

    def notify(self, body):
        header = self.create_message_header(MAL_IP_STAGES.PUBSUB_NOTIFY)
        message = MALMessage(header=header, msg_parts=body)
        self.send_message(message)

    def notify_error(self, body):
        header = self.create_message_header(MAL_IP_STAGES.PUBSUB_NOTIFY_ERROR)
        message = MALMessage(header=header, msg_parts=body)
        self.send_message(message)

    def receive_publish_registration_message(self):
        message = self.receive_message()
        ip_stage = message.header.ip_stage
        is_error_message = message.header.is_error_message
        if not is_error_message and ip_stage == MAL_IP_STAGES.PUBSUB_PUBLISH_REGISTER:
            return message
        elif not is_error_message and ip_stage == MAL_IP_STAGES.PUBSUB_PUBLISH_DEREGISTER:
            return message
        else:
            raise InvalidIPStageError("In %s. Expected PUBSUB_PUBLISH_REGISTER or PUBSUB_PUBLISH_DEREGISTER. Got %s" %
                                      (self.__class__.__name__, ip_stage))

    def publish_register_ack(self, body):
        header = self.create_message_header(MAL_IP_STAGES.PUBSUB_PUBLISH_REGISTER_ACK)
        message = MALMessage(header=header, msg_parts=body)
        self.send_message(message)

    def publish_register_error(self, body):
        header = self.create_message_header(MAL_IP_STAGES.PUBSUB_PUBLISH_REGISTER_ERROR)
        message = MALMessage(header=header, msg_parts=body)
        self.send_message(message)

    def receive_publish_deregister(self):
        message = self.receive_message()
        ip_stage = message.header.ip_stageis_error_message = message.header.is_error_message
        if not is_error_message and ip_stage == MAL_IP_STAGES.PUBSUB_PUBLISH_DEREGISTER:
            return message
        else:
            raise InvalidIPStageError("In %s. Expected PUBSUB_PUBLISH_DEREGISTER. Got %s" %
                                      (self.__class__.__name__, ip_stage))

    def publish_deregister_ack(self, body):
        header = self.create_message_header(MAL_IP_STAGES.PUBSUB_PUBLISH_DEREGISTER_ACK)
        message = MALMessage(header=header, msg_parts=body)
        self.send_message(message)

    def receive_publish(self):
        message = self.receive_message()
        ip_stage = message.header.ip_stage
        is_error_message = message.header.is_error_message
        if not is_error_message and ip_stage == MAL_IP_STAGES.PUBSUB_PUBLISH:
            return message
        else:
            raise InvalidIPStageError("In %s. Expected PUBSUB_PUBLISH. Got %s" %
                                      (self.__class__.__name__, ip_stage))

    def publish_error(self, body):
        header = self.create_message_header(MAL_IP_STAGES.PUBSUB_PUBLISH_ERROR)
        message = MALMessage(header=header, msg_parts=body)
        self.send_message(message)


class PubSubConsumerHandler(ConsumerHandler):

    def register(self, body):
        header = self.create_message_header(MAL_IP_STAGES.PUBSUB_REGISTER)
        message = MALMessage(header=header, msg_parts=body)
        self.send_message(message)

    def receive_register_ack(self):
        message = self.receive_message()
        ip_stage = message.header.ip_stage
        is_error_message = message.header.is_error_message
        if not is_error_message and ip_stage == MAL_IP_STAGES.PUBSUB_REGISTER_ACK:
            return message
        elif is_error_message and ip_stage == MAL_IP_ERRORS.PUBSUB_REGISTER_ACK_ERROR:
            raise RuntimeError(message)
        else:
            raise InvalidIPStageError("In %s. Expected PUBSUB_REGISTER_ACK. Got %s" %
                                      (self.__class__.__name__, ip_stage))

    def deregister(self, body):
        header = self.create_message_header(MAL_IP_STAGES.PUBSUB_DEREGISTER)
        message = MALMessage(header=header, msg_parts=body)
        self.send_message(message)

    def receive_deregister_ack(self):
        message = self.receive_message()
        ip_stage = message.header.ip_stage
        is_error_message = message.header.is_error_message
        if not is_error_message and ip_stage == MAL_IP_STAGES.PUBSUB_DEREGISTER_ACK:
            return message
        elif is_error_message and ip_stage == MAL_IP_STAGES.PUBSUB_DEREGISTER_ACK_ERROR:
            raise RuntimeError(message)
        else:
            raise InvalidIPStageError("In %s. Expected PUBSUB_DEREGISTER_ACK. Got %s" %
                                      (self.__class__.__name__, ip_stage))

    def receive_notify(self):
        message = self.receive_message()
        ip_stage = message.header.ip_stage
        is_error_message = message.header.is_error_message
        if not is_error_message and  ip_stage == MAL_IP_STAGES.PUBSUB_NOTIFY:
            return message
        elif is_error_message and ip_stage == MAL_IP_ERRORS.PUBSUB_NOTIFY_ERROR:
            raise RuntimeError(message)
        else:
            raise InvalidIPStageError("In %s. Expected PUBSUB_NOTIFY. Got %s" %
                                      (self.__class__.__name__, ip_stage))

