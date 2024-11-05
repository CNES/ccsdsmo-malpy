import copy
import time
from enum import IntEnum

from .maltypes import InteractionTypeEnum, number


class MAL_INTERACTION_STAGES:
    # Send
    SEND = 1

    # Submit
    SUBMIT = 1
    SUBMIT_ACK = 2

    # Request
    REQUEST = 1
    REQUEST_RESPONSE = 2

    # Invoke
    INVOKE = 1
    INVOKE_ACK = 2
    INVOKE_RESPONSE = 3

    # Progress
    PROGRESS = 1
    PROGRESS_ACK = 2
    PROGRESS_UPDATE = 3
    PROGRESS_RESPONSE = 4

    # PubSub
    PUBSUB_REGISTER = 1
    PUBSUB_REGISTER_ACK = 2
    PUBSUB_PUBLISH_REGISTER = 3
    PUBSUB_PUBLISH_REGISTER_ACK = 4
    PUBSUB_PUBLISH = 5
    PUBSUB_NOTIFY = 6
    PUBSUB_DEREGISTER = 7
    PUBSUB_DEREGISTER_ACK = 8
    PUBSUB_PUBLISH_DEREGISTER = 9
    PUBSUB_PUBLISH_DEREGISTER_ACK = 10


class MAL_INTERACTION_ERRORS:
    SUBMIT_ERROR = 2
    REQUEST_ERROR = 2
    INVOKE_ACK_ERROR = 2
    INVOKE_RESPONSE_ERROR = 3
    PROGRESS_ACK_ERROR = 2
    PROGRESS_UPDATE_ERROR = 3
    PROGRESS_RESPONSE_ERROR = 5
    PUBSUB_REGISTER_ACK_ERROR = 2
    PUBSUB_PUBLISH_REGISTER_ERROR = 4
#    PUBSUB_PUBLISH_ERROR =
#    PUBSUB_NOTIFY_ERROR = 17


class MalformedMessageError(Exception):
    pass


class InvalidInteractionStageError(Exception):
    """ Error in case of invalid IP.
        Should be called as InvalidInteractionStageError((message.header.interaction_type, message.header.interaction_stage)) or
          InvalidInteractionStageError(classname=self.__class__.__name__, expected_ip=(InteractionTypeEnum.SEND, 1),
                              ip=(message.header.interaction_type, message.header.interaction_stage), message='You must have messed up something)
    """
    def __init__(self, ip, classname=None, expected_ip=None, message=None):
      errormessage = []
      if classname is not None:
          errormessage.append("In {}.".format(classname))
      if expected_ip is not None:
          expected_iptype = expected_ip[0].name
          expected_ipstage = expected_ip[1]
          errormessage.append("Expected {}:{}.".format(expected_iptype, expected_ipstage))

      iptype = ip[0].name
      ipstage = ip[1]
      errormessage.append("Got {}:{}.".format(iptype, ipstage))

      if message is not None:
          errormessage.append(message)
      super().__init__(" ".join(errormessage))


class BackendShutdown(Exception):
    pass


class MALHeader(object):
    """
    A MALHeader objects in the python representation of the
    MAL message header
    """

    # TODO: This object is a great candidate for a Cython cpdef struct
    # which will allow fast copies and attribute affectations.

    __slots__ = ['from_entity',
                 'authentication_id',
                 'to_entity',
                 'timestamp',
                 'interaction_type',
                 'interaction_stage',
                 'transaction_id',
                 'service_area',
                 'service',
                 'operation',
                 'area_version',
                 'is_error_message',
                 'supplements'
                 ]

    def __init__(self):
        self.from_entity = None
        self.authentication_id = None
        self.to_entity = None
        self.timestamp = None
        self.interaction_type = None
        self.interaction_stage = None
        self.transaction_id = None
        self.service_area = None
        self.service = None
        self.operation = None
        self.area_version = None
        self.is_error_message = None
        self.supplements = None

    def copy(self):
        instance = self.__class__()
        instance.from_entity = self.from_entity
        instance.authentication_id = self.authentication_id
        instance.to_entity = self.to_entity
        instance.timestamp = self.timestamp
        instance.interaction_type = self.interaction_type
        instance.interaction_stage = self.interaction_stage
        instance.transaction_id = self.transaction_id
        instance.service_area = self.service_area
        instance.service = self.service
        instance.operation = self.operation
        instance.area_version = self.area_version
        instance.is_error_message = self.is_error_message
        instance.supplements = copy.deepcopy(self.supplements)

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

    def __init__(self, transport, encoding):
        self.transport = transport
        self.encoding = encoding
        self.transport.parent = self
        self.encoding.parent = self

    def send_message(self, message):
        message = self.encoding.encode(message)
        return self.transport.send(message)

    def receive_message(self, signature):
        message = self.transport.recv()
        return self.encoding.decode(message, signature)


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
    AREA = None
    AREA_VERSION = 1
    SERVICE = None
    OPERATION = None
    INTERACTION_TYPE = None
    _transaction_id_counter = 0

    @classmethod
    def get_new_transaction_id(cls):
        cls._transaction_id_counter += 1
        return cls._transaction_id_counter

    def __init__(self, transport, encoding, provider_entity="", consumer_entity="",
                 authentication_id=b"", header_supplements=[]):
        super().__init__(transport, encoding)
        self.consumer_entity = consumer_entity
        self.provider_entity = provider_entity
        self.authentication_id = authentication_id
        self.interaction_terminated = False
        self.header_supplements = header_supplements
        self.transaction_id = self.get_new_transaction_id()

    def create_message_header(self, interaction_stage):
        header = MALHeader()
        header.from_entity = self.consumer_entity
        header.authentication_id = self.authentication_id
        header.to_entity = self.provider_entity
        header.timestamp = time.time()
        header.interaction_type = self.INTERACTION_TYPE
        header.interaction_stage = interaction_stage
        header.transaction_id = self.transaction_id
        header.service_area = self.AREA
        header.service = self.SERVICE
        header.operation = self.OPERATION
        header.area_version = self.AREA_VERSION
        header.is_error_message = None
        header.supplements = self.header_supplements
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

    INTERACTION_TYPE = None
    _transaction_id_counter = 0

    @classmethod
    def get_new_transaction_id(cls):
        cls._transaction_id_counter += 1
        return cls._transaction_id_counter

    def __init__(self, transport, encoding, broker_entity=None, provider_entity="",
                 authentication_id=b""):
        super().__init__(transport, encoding)
        self.broker_entity = broker_entity
        self.provider_entity = provider_entity
        self.response_header = None
        self.authenthication_id = authentication_id
        self.interaction_terminated = False
        self.transaction_id = self.get_new_transaction_id()

    def define_header(self, received_message_header):
        self.response_header = received_message_header.copy()
        self.response_header.from_entity = received_message_header.to_entity
        self.response_header.to_entity = received_message_header.from_entity

    def create_message_header(self, interaction_stage, is_error_message=False, to_entity=None,
                              header_supplements=[]):
        if not self.response_header:
            header = MALHeader()
            header.from_entity = self.provider_entity
            header.authentication_id = self.authentication_id
            header.to_entity = to_entity
            header.timestamp = time.time()
            header.interaction_type = self.INTERACTION_TYPE
            header.interaction_stage = interaction_stage
            header.transaction_id = self.transaction_id_counter
            header.service_area = self.AREA
            header.service = self.SERVICE
            header.operation = self.OPERATION
            header.area_version = self.AREA_VERSION
            header.is_error_message =  is_error_message
            header.supplements = header_supplements
        else:
            header = self.response_header.copy()
            header.interaction_stage = interaction_stage
            header.is_error_message = is_error_message

        # If parameter to_entity is defined
        if to_entity :
            header.to_entity = to_entity
        elif self.broker_entity:
            # if parameter to_entity is not defined and broker_entity is defined
            header.to_entity = self.broker_entity
        # else:
        #     # Nothing is defined, keep to_entity value
        return header


class SendProviderHandler(ProviderHandler):
    """
    A provider handler for operations belonging to the SEND
    interaction pattern
    """

    INTERACTION_TYPE = InteractionTypeEnum.SEND

    def receive_send(self, signature):
        message = self.receive_message(signature)
        interaction_type = message.header.interaction_type
        interaction_stage = message.header.interaction_stage
        is_error_message = message.header.is_error_message
        if not is_error_message and interaction_type == self.INTERACTION_TYPE and interaction_stage == MAL_INTERACTION_STAGES.SEND:
            self.interaction_terminated = True
            return message
        else:
            raise InvalidInteractionStageError(classname=self.__class__.__name__, expected_ip=(self.INTERACTION_TYPE, MAL_INTERACTION_STAGES.SEND), ip=(interaction_type, interaction_stage))


class SendConsumerHandler(ConsumerHandler):
    """
    A consumer handler for operations belonging to the SEND
    interaction pattern
    """

    INTERACTION_TYPE = InteractionTypeEnum.SEND

    def send(self, body):
        header = self.create_message_header(MAL_INTERACTION_STAGES.SEND)
        message = MALMessage(header=header, msg_parts=body)
        self.send_message(message)
        self.interaction_terminated = True


class SubmitProviderHandler(ProviderHandler):
    """
    A provider handler for operations belonging to the SEND
    interaction pattern
    """

    INTERACTION_TYPE = InteractionTypeEnum.SUBMIT

    def receive_submit(self, signature):
        message = self.receive_message(signature)
        self.define_header(message.header)
        interaction_type = message.header.interaction_type
        interaction_stage = message.header.interaction_stage
        is_error_message = message.header.is_error_message
        if not is_error_message and interaction_type == self.INTERACTION_TYPE and interaction_stage == MAL_INTERACTION_STAGES.SUBMIT:
            return message
        else:
            raise InvalidInteractionStageError(classname=self.__class__.__name__, expected_ip=(self.INTERACTION_TYPE, MAL_INTERACTION_STAGES.SUBMIT), ip=(interaction_type, interaction_stage))

    def ack(self, body):
        header = self.create_message_header(MAL_INTERACTION_STAGES.SUBMIT_ACK)
        message = MALMessage(header=header, msg_parts=body)
        self.interaction_terminated = True
        return self.send_message(message)

    def error(self, body):
        header = self.create_message_header(MAL_INTERACTION_ERRORS.SUBMIT_ERROR)
        header.is_error_message = True
        message = MALMessage(header=header, msg_parts=body)
        self.interaction_terminated = True
        return self.send_message(message)


class SubmitConsumerHandler(ConsumerHandler):
    """
    A consumer handler for operations belonging to the SEND
    interaction pattern
    """

    INTERACTION_TYPE = InteractionTypeEnum.SUBMIT

    def submit(self, body):
        header = self.create_message_header(MAL_INTERACTION_STAGES.SUBMIT)
        message = MALMessage(header=header, msg_parts=body)
        self.send_message(message)

    def receive_ack(self, signature):
        message = self.receive_message(signature)
        interaction_type = message.header.interaction_type
        interaction_stage = message.header.interaction_stage
        is_error_message = message.header.is_error_message
        if not is_error_message and interaction_type == self.INTERACTION_TYPE and interaction_stage == MAL_INTERACTION_STAGES.SUBMIT_ACK:
            self.interaction_terminated = True
            return message
        elif is_error_message and interaction_type == self.INTERACTION_TYPE and interaction_stage == MAL_INTERACTION_ERRORS.SUBMIT_ERROR:
            self.interaction_terminated = True
            raise RuntimeError(message)
        else:
            raise InvalidInteractionStageError(classname=self.__class__.__name__, expected_ip=(self.INTERACTION_TYPE, MAL_INTERACTION_STAGES.SUBMIT_ACK), ip=(interaction_type, interaction_stage))


class RequestProviderHandler(ProviderHandler):
    """
    A provider handler for operations belonging to the SEND
    interaction pattern
    """

    INTERACTION_TYPE = InteractionTypeEnum.REQUEST

    def receive_request(self, signature):
        message = self.receive_message(signature)
        self.define_header(message.header)
        interaction_type = message.header.interaction_type
        interaction_stage = message.header.interaction_stage
        is_error_message = message.header.is_error_message
        if not is_error_message and interaction_type == self.INTERACTION_TYPE and interaction_stage == MAL_INTERACTION_STAGES.REQUEST:
            return message
        else:
            raise InvalidInteractionStageError(classname=self.__class__.__name__, expected_ip=(self.INTERACTION_TYPE, MAL_INTERACTION_STAGES.REQUEST), ip=(interaction_type, interaction_stage))

    def response(self, body):
        header = self.create_message_header(MAL_INTERACTION_STAGES.REQUEST_RESPONSE)
        message = MALMessage(header=header, msg_parts=body)
        self.interaction_terminated = True
        return self.send_message(message)

    def error(self, body):
        header = self.create_message_header(MAL_INTERACTION_ERRORS.REQUEST_ERROR)
        header.is_error_message = True
        message = MALMessage(header=header, msg_parts=body)
        self.interaction_terminated = True
        return self.send_message(message)


class RequestConsumerHandler(ConsumerHandler):
    """
    A consumer handler for operations belonging to the SEND
    interaction pattern
    """

    INTERACTION_TYPE = InteractionTypeEnum.REQUEST

    def request(self, body):
        header = self.create_message_header(MAL_INTERACTION_STAGES.REQUEST)
        message = MALMessage(header=header, msg_parts=body)
        return self.send_message(message)

    def receive_response(self, signature):
        message = self.receive_message(signature)
        interaction_type = message.header.interaction_type
        interaction_stage = message.header.interaction_stage
        is_error_message = message.header.is_error_message
        if not is_error_message and interaction_type == self.INTERACTION_TYPE and interaction_stage == MAL_INTERACTION_STAGES.REQUEST_RESPONSE:
            self.interaction_terminated = True
            return message
        elif is_error_message and interaction_type == self.INTERACTION_TYPE and interaction_stage == MAL_INTERACTION_ERRORS.REQUEST_ERROR:
            self.interaction_terminated = True
            raise RuntimeError(message)
        else:
            raise InvalidInteractionStageError(classname=self.__class__.__name__, expected_ip=(self.INTERACTION_TYPE, MAL_INTERACTION_STAGES.REQUEST_RESPONSE), ip=(interaction_type, interaction_stage))


class InvokeProviderHandler(ProviderHandler):
    """
    A provider handler for operations belonging to the SEND
    interaction pattern
    """

    INTERACTION_TYPE = InteractionTypeEnum.INVOKE

    def receive_invoke(self, signature):
        message = self.receive_message(signature)
        self.define_header(message.header)
        interaction_type = message.header.interaction_type
        interaction_stage = message.header.interaction_stage
        is_error_message = message.header.is_error_message
        if not is_error_message and interaction_type == self.INTERACTION_TYPE and interaction_stage == MAL_INTERACTION_STAGES.INVOKE:
            return message
        else:
            raise InvalidInteractionStageError(classname=self.__class__.__name__, expected_ip=(self.INTERACTION_TYPE, MAL_INTERACTION_STAGES.INVOKE), ip=(interaction_type, interaction_stage))

    def ack(self, body):
        header = self.create_message_header(MAL_INTERACTION_STAGES.INVOKE_ACK)
        message = MALMessage(header=header, msg_parts=body)
        return self.send_message(message)

    def ack_error(self, body):
        header = self.create_message_header(MAL_INTERACTION_ERRORS.INVOKE_ACK_ERROR)
        header.is_error_message = True
        message = MALMessage(header=header, msg_parts=body)
        return self.send_message(message)

    def response(self, body):
        header = self.create_message_header(MAL_INTERACTION_STAGES.INVOKE_RESPONSE)
        message = MALMessage(header=header, msg_parts=body)
        self.interaction_terminated = True
        return self.send_message(message)

    def response_error(self, body):
        header = self.create_message_header(MAL_INTERACTION_ERRORS.INNVOKE_ERROR)
        header.is_error_message = True
        message = MALMessage(header=header, msg_parts=body)
        self.interaction_terminated = True
        return self.send_message(message)


class InvokeConsumerHandler(ConsumerHandler):
    """
    A consumer handler for operations belonging to the SEND
    interaction pattern
    """

    INTERACTION_TYPE = InteractionTypeEnum.INVOKE

    def invoke(self, body):
        header = self.create_message_header(MAL_INTERACTION_STAGES.INVOKE)
        message = MALMessage(header=header, msg_parts=body)
        self.send_message(message)
        self.interaction_terminated = True

    def receive_ack(self, signature):
        message = self.receive_message(signature)
        interaction_type = message.header.interaction_type
        interaction_stage = message.header.interaction_stage
        is_error_message = message.header.is_error_message
        if not is_error_message and interaction_type == self.INTERACTION_TYPE and interaction_stage == MAL_INTERACTION_STAGES.INVOKE_ACK:
            return message
        elif is_error_message and interaction_type == self.INTERACTION_TYPE and interaction_stage == MAL_INTERACTION_ERRORS.INVOKE_ACK_ERROR:
            raise RuntimeError(message)
        else:
            raise InvalidInteractionStageError(classname=self.__class__.__name__, expected_ip=(self.INTERACTION_TYPE, MAL_INTERACTION_STAGES.INVOKE_ACK), ip=(interaction_type, interaction_stage))

    def receive_response(self, signature):
        message = self.receive_message(signature)
        interaction_type = message.header.interaction_type
        interaction_stage = message.header.interaction_stage
        is_error_message = message.header.is_error_message
        if not is_error_message and interaction_type == self.INTERACTION_TYPE and interaction_stage == MAL_INTERACTION_STAGES.INVOKE_RESPONSE:
            self.interaction_terminated = True
            return message
        elif is_error_message and interaction_type == self.INTERACTION_TYPE and interaction_stage == MAL_INTERACTION_ERRORS.INVOKE_RESPONSE_ERROR:
            self.interaction_terminated = True
            raise RuntimeError(message)
        else:
            raise InvalidInteractionStageError(classname=self.__class__.__name__, expected_ip=(self.INTERACTION_TYPE, MAL_INTERACTION_STAGES.INVOKE_RESPONSE), ip=(interaction_type, interaction_stage))


class ProgressProviderHandler(ProviderHandler):
    """
    A provider handler for operations belonging to the SEND
    interaction pattern
    """

    INTERACTION_TYPE = InteractionTypeEnum.PROGRESS

    def receive_progress(self, signature):
        message = self.receive_message(signature)
        self.define_header(message.header)
        interaction_type = message.header.interaction_type
        interaction_stage = message.header.interaction_stage
        is_error_message = message.header.is_error_message
        if not is_error_message and interaction_type == self.INTERACTION_TYPE and interaction_stage == MAL_INTERACTION_STAGES.PROGRESS:
            return message
        else:
            raise InvalidInteractionStageError(classname=self.__class__.__name__, expected_ip=(self.INTERACTION_TYPE, MAL_INTERACTION_STAGES.PROGRESS), ip=(interaction_type, interaction_stage))

    def ack(self, body):
        header = self.create_message_header(MAL_INTERACTION_STAGES.PROGRESS_ACK)
        message = MALMessage(header=header, msg_parts=body)
        return self.send_message(message)

    def ack_error(self, body):
        header = self.create_message_header(MAL_INTERACTION_ERRORS.PROGRESS_ACK_ERROR)
        header.is_error_message = True
        message = MALMessage(header=header, msg_parts=body)
        return self.send_message(message)

    def update(self, body):
        header = self.create_message_header(MAL_INTERACTION_STAGES.PROGRESS_UPDATE)
        message = MALMessage(header=header, msg_parts=body)
        return self.send_message(message)

    def update_error(self, body):
        header = self.create_message_header(MAL_INTERACTION_ERRORS.PROGRESS_UPDATE_ERROR)
        header.is_error_message = True
        message = MALMessage(header=header, msg_parts=body)
        return self.send_message(message)

    def response(self, body):
        header = self.create_message_header(MAL_INTERACTION_STAGES.PROGRESS_RESPONSE)
        message = MALMessage(header=header, msg_parts=body)
        self.interaction_terminated = True
        return self.send_message(message)

    def response_error(self, body):
        header = self.create_message_header(MAL_INTERACTION_ERRORS.PROGRESS_RESPONSE_ERROR)
        header.is_error_message = True
        message = MALMessage(header=header, msg_parts=body)
        self.interaction_terminated = True
        return self.send_message(message)


class ProgressConsumerHandler(ConsumerHandler):
    """
    A consumer handler for operations belonging to the SEND
    interaction pattern
    """

    INTERACTION_TYPE = InteractionTypeEnum.PROGRESS

    def progress(self, body):
        header = self.create_message_header(MAL_INTERACTION_STAGES.PROGRESS)
        message = MALMessage(header=header, msg_parts=body)
        self.send_message(message)

    def receive_ack(self, signature):
        message = self.receive_message(signature)
        interaction_type = message.header.interaction_type
        interaction_stage = message.header.interaction_stage
        is_error_message = message.header.is_error_message
        if not is_error_message and interaction_type == self.INTERACTION_TYPE and interaction_stage == MAL_INTERACTION_STAGES.PROGRESS_ACK:
            return message
        elif is_error_message and interaction_type == self.INTERACTION_TYPE and interaction_stage == MAL_INTERACTION_ERRORS.PROGRESS_ACK_ERROR:
            raise RuntimeError(message)
        else:
            raise InvalidInteractionStageError(classname=self.__class__.__name__, expected_ip=(self.INTERACTION_TYPE, MAL_INTERACTION_STAGES.PROGRESS_ACK), ip=(interaction_type, interaction_stage))

    def receive_update(self, signature):
        """ As it is not possible to know beforehand if the received message is
        an update or the final response, we only do receive_update. The content of
        the header message will let us know te corresponding state.
        """
        message = self.receive_message(signature)
        interaction_type = message.header.interaction_type
        interaction_stage = message.header.interaction_stage
        is_error_message = message.header.is_error_message
        if not is_error_message and interaction_type == self.INTERACTION_TYPE and interaction_stage == MAL_INTERACTION_STAGES.PROGRESS_UPDATE:
            return message
        elif not is_error_message and interaction_type == self.INTERACTION_TYPE and interaction_stage == MAL_INTERACTION_STAGES.PROGRESS_RESPONSE:
            self.interaction_terminated = True
            return message
        elif is_error_message and interaction_type == self.INTERACTION_TYPE and interaction_stage == MAL_INTERACTION_ERRORS.PROGRESS_UPDATE_ERROR:
            self.interaction_terminated = True
            raise RuntimeError(message)
        elif is_error_message and interaction_type == self.INTERACTION_TYPE and interaction_stage == MAL_INTERACTION_ERRORS.PROGRESS_RESPONSE_ERROR:
            self.interaction_terminated = True
            raise RuntimeError(message)
        else:
            raise InvalidInteractionStageError(classname=self.__class__.__name__, expected_ip=(self.INTERACTION_TYPE, MAL_INTERACTION_STAGES.PROGRESS_UPDATE), ip=(interaction_type, interaction_stage))

#    def receive_response(self):
#        message = self.receive_message()
#        interaction_type = message.header.interaction_type
#        if interaction_stage == MAL_INTERACTION_STAGES.PROGRESS_RESPONSE:
#            self.interaction_terminated = True
#            return message
#        elif interaction_stage == MAL_INTERACTION_STAGES.PROGRESS_RESPONSE_ERROR:
#            self.interaction_terminated = True
#            raise RuntimeError(message)
#        else:
#            raise InvalidInteractionStageError(classname=self.__class__.__name__, expected_ip=(self.INTERACTION_TYPE, MAL_INTERACTION_STAGES.SEND), ip=(interaction_type, interaction_stage))


class PubSubProviderHandler(ProviderHandler):

    INTERACTION_TYPE = InteractionTypeEnum.PUBSUB

    def publish_register(self, body):
        header = self.create_message_header(MAL_INTERACTION_STAGES.PUBSUB_PUBLISH_REGISTER)
        message = MALMessage(header=header, msg_parts=body)
        self.send_message(message)

    def receive_publish_register_ack(self, signature):
        message = self.receive_message(signature)
        interaction_type = message.header.interaction_type
        interaction_stage = message.header.interaction_stage
        is_error_message = message.header.is_error_message
        if not is_error_message and interaction_type == self.INTERACTION_TYPE and interaction_stage == MAL_INTERACTION_STAGES.PUBSUB_PUBLISH_REGISTER_ACK:
            return message
        elif is_error_message and interaction_type == self.INTERACTION_TYPE and interaction_stage == MAL_INTERACTION_ERRORS.PUBSUB_PUBLISH_REGISTER_ERROR:
            raise RuntimeError(message)
        else:
            raise InvalidInteractionStageError(classname=self.__class__.__name__, expected_ip=(self.INTERACTION_TYPE, MAL_INTERACTION_STAGES.PUBSUB_PUBLISH_REGISTER_ACK), ip=(interaction_type, interaction_stage))

    def publish_deregister(self, body):
        header = self.create_message_header(MAL_INTERACTION_STAGES.PUBSUB_PUBLISH_DEREGISTER)
        message = MALMessage(header=header, msg_parts=body)
        self.send_message(message)

    def receive_publish_deregister_ack(self, signature):
        message = self.receive_message(signature)
        interaction_type = message.header.interaction_type
        interaction_stage = message.header.interaction_stage
        is_error_message = message.header.is_error_message
        if not is_error_message and interaction_type == self.INTERACTION_TYPE and interaction_stage == MAL_INTERACTION_STAGES.PUBSUB_PUBLISH_DEREGISTER_ACK:
            return message
        else:
            raise InvalidInteractionStageError(classname=self.__class__.__name__, expected_ip=(self.INTERACTION_TYPE, MAL_INTERACTION_STAGES.PUBSUB_PUBLISH_DEREGISTER_ACK), ip=(interaction_type, interaction_stage))

    def publish(self, body):
        header = self.create_message_header(MAL_INTERACTION_STAGES.PUBSUB_PUBLISH)
        message = MALMessage(header=header, msg_parts=body)
        self.send_message(message)

    # def receive_publish_error(self):
    #     message = self.receive_message()
    #     interaction_type = message.header.interaction_type
    #     is_error_message = message.header.is_error_message
    #     if is_error_message and interaction_type == self.INTERACTION_TYPE and interaction_stage == MAL_INTERACTION_ERRORS.PUBSUB_PUBLISH_ERROR:
    #         return message
    #     else:
    #         raise InvalidInteractionStageError(classname=self.__class__.__name__, expected_ip=(self.INTERACTION_TYPE, MAL_INTERACTION_STAGES.SEND), ip=(interaction_type, interaction_stage))


class PubSubBrokerHandler(ProviderHandler):

    INTERACTION_TYPE = InteractionTypeEnum.PUBSUB

    def receive_registration_message(self, signature):
        message = self.receive_message(signature)
        self.define_header(message.header)
        interaction_type = message.header.interaction_type
        interaction_stage = message.header.interaction_stage
        is_error_message = message.header.is_error_message
        if not is_error_message and interaction_type == self.INTERACTION_TYPE and interaction_stage == MAL_INTERACTION_STAGES.PUBSUB_REGISTER:
            return message
        elif not is_error_message and interaction_type == self.INTERACTION_TYPE and interaction_stage == MAL_INTERACTION_STAGES.PUBSUB_DEREGISTER:
            return message
        else:
            raise InvalidInteractionStageError(classname=self.__class__.__name__, expected_ip=(self.INTERACTION_TYPE, MAL_INTERACTION_STAGES.PUBSUB_REGISTER), ip=(interaction_type, interaction_stage))

    def register_ack(self, body):
        header = self.create_message_header(MAL_INTERACTION_STAGES.PUBSUB_REGISTER_ACK)
        self.define_header(header)
        message = MALMessage(header=header, msg_parts=body)
        self.send_message(message)

    def register_error(self, body):
        header = self.create_message_header(MAL_INTERACTION_STAGES.PUBSUB_REGISTER_ACK_ERROR)
        header.is_error_message = True
        self.define_header(header)
        message = MALMessage(header=header, msg_parts=body)
        self.send_message(message)

    def deregister_ack(self, body):
        header = self.create_message_header(MAL_INTERACTION_STAGES.PUBSUB_DEREGISTER_ACK)
        self.define_header(header)
        message = MALMessage(header=header, msg_parts=body)
        self.send_message(message)

    def deregister_error(self, body):
        header = self.create_message_header(MAL_INTERACTION_STAGES.PUBSUB_DEREGISTER_ACK_ERROR)
        header.is_error_message = True
        self.define_header(header)
        message = MALMessage(header=header, msg_parts=body)
        self.send_message(message)

    def receive_deregister(self, signature):
        message = self.receive_message(signature)
        self.define_header(message.header)
        interaction_type = message.header.interaction_type
        interaction_stage = message.header.interaction_stage
        is_error_message = message.header.is_error_message
        if not is_error_message and interaction_type == self.INTERACTION_TYPE and interaction_stage == MAL_INTERACTION_STAGES.PUBSUB_DEREGISTER:
            return message
        else:
            raise InvalidInteractionStageError(classname=self.__class__.__name__, expected_ip=(self.INTERACTION_TYPE, MAL_INTERACTION_STAGES.PUBSUB_DEREGISTER), ip=(interaction_type, interaction_stage))

    def notify(self, body, to_entity):
        header = self.create_message_header(MAL_INTERACTION_STAGES.PUBSUB_NOTIFY, to_entity=to_entity)
        message = MALMessage(header=header, msg_parts=body)
        self.send_message(message)

    # def notify_error(self, body):
    #     header = self.create_message_header(MAL_INTERACTION_STAGES.PUBSUB_NOTIFY_ERROR)
    #     self.define_header(header)
    #     message = MALMessage(header=header, msg_parts=body)
    #     self.send_message(message)

    def receive_publish_registration_message(self, signature):
        message = self.receive_message(signature)
        self.define_header(message.header)
        interaction_type = message.header.interaction_type
        interaction_stage = message.header.interaction_stage
        is_error_message = message.header.is_error_message
        if not is_error_message and interaction_type == self.INTERACTION_TYPE and interaction_stage == MAL_INTERACTION_STAGES.PUBSUB_PUBLISH_REGISTER:
            return message
        elif not is_error_message and interaction_type == self.INTERACTION_TYPE and interaction_stage == MAL_INTERACTION_STAGES.PUBSUB_PUBLISH_DEREGISTER:
            return message
        else:
            raise InvalidInteractionStageError(classname=self.__class__.__name__, expected_ip=(self.INTERACTION_TYPE, MAL_INTERACTION_STAGES.PUBSUB_PUBLISH_REGISTER), ip=(interaction_type, interaction_stage))

    def publish_register_ack(self, body):
        header = self.create_message_header(MAL_INTERACTION_STAGES.PUBSUB_PUBLISH_REGISTER_ACK)
        self.define_header(header)
        message = MALMessage(header=header, msg_parts=body)
        self.send_message(message)

    def publish_register_error(self, body):
        header = self.create_message_header(MAL_INTERACTION_STAGES.PUBSUB_PUBLISH_REGISTER_ERROR)
        header.is_error_message = True
        self.define_header(header)
        message = MALMessage(header=header, msg_parts=body)
        self.send_message(message)

    def receive_publish_deregister(self, signature):
        message = self.receive_message(signature)
        self.define_header(message.header)
        interaction_type = message.header.interaction_type
        interaction_stage = message.header.interaction_stage
        is_error_message = message.header.is_error_message
        if not is_error_message and interaction_type == self.INTERACTION_TYPE and interaction_stage == MAL_INTERACTION_STAGES.PUBSUB_PUBLISH_DEREGISTER:
            return message
        else:
            raise InvalidInteractionStageError(classname=self.__class__.__name__, expected_ip=(self.INTERACTION_TYPE, MAL_INTERACTION_STAGES.PUBSUB_PUBLISH_DEREGISTER), ip=(interaction_type, interaction_stage))

    def publish_deregister_ack(self, body):
        header = self.create_message_header(MAL_INTERACTION_STAGES.PUBSUB_PUBLISH_DEREGISTER_ACK)
        self.define_header(header)
        message = MALMessage(header=header, msg_parts=body)
        self.send_message(message)

    def receive_publish(self, signature):
        message = self.receive_message(signature)
        self.define_header(message.header)
        interaction_type = message.header.interaction_type
        interaction_stage = message.header.interaction_stage
        is_error_message = message.header.is_error_message
        if not is_error_message and interaction_type == self.INTERACTION_TYPE and interaction_stage == MAL_INTERACTION_STAGES.PUBSUB_PUBLISH:
            return message
        else:
            raise InvalidInteractionStageError(classname=self.__class__.__name__, expected_ip=(self.INTERACTION_TYPE, MAL_INTERACTION_STAGES.PUBSUB_PUBLISH), ip=(interaction_type, interaction_stage))

    # def publish_error(self, body):
    #     header = self.create_message_header(MAL_INTERACTION_STAGES.PUBSUB_PUBLISH_ERROR)
    #     self.define_header(header)
    #     message = MALMessage(header=header, msg_parts=body)
    #     self.send_message(message)


class PubSubConsumerHandler(ConsumerHandler):

    INTERACTION_TYPE = InteractionTypeEnum.PUBSUB

    def register(self, body):
        header = self.create_message_header(MAL_INTERACTION_STAGES.PUBSUB_REGISTER)
        message = MALMessage(header=header, msg_parts=body)
        self.send_message(message)

    def receive_register_ack(self, signature):
        message = self.receive_message(signature)
        interaction_type = message.header.interaction_type
        interaction_stage = message.header.interaction_stage
        is_error_message = message.header.is_error_message
        if not is_error_message and interaction_type == self.INTERACTION_TYPE and interaction_stage == MAL_INTERACTION_STAGES.PUBSUB_REGISTER_ACK:
            return message
        elif is_error_message and interaction_type == self.INTERACTION_TYPE and interaction_stage == MAL_INTERACTION_ERRORS.PUBSUB_REGISTER_ACK_ERROR:
            raise RuntimeError(message)
        else:
            raise InvalidInteractionStageError(classname=self.__class__.__name__, expected_ip=(self.INTERACTION_TYPE, MAL_INTERACTION_STAGES.PUBSUB_REGISTER_ACK), ip=(interaction_type, interaction_stage))

    def deregister(self, body):
        header = self.create_message_header(MAL_INTERACTION_STAGES.PUBSUB_DEREGISTER)
        message = MALMessage(header=header, msg_parts=body)
        self.send_message(message)

    def receive_deregister_ack(self, signature):
        message = self.receive_message(signature)
        interaction_type = message.header.interaction_type
        interaction_stage = message.header.interaction_stage
        is_error_message = message.header.is_error_message
        if not is_error_message and interaction_type == self.INTERACTION_TYPE and interaction_stage == MAL_INTERACTION_STAGES.PUBSUB_DEREGISTER_ACK:
            return message
        elif is_error_message and interaction_type == self.INTERACTION_TYPE and interaction_stage == MAL_INTERACTION_STAGES.PUBSUB_DEREGISTER_ACK_ERROR:
            raise RuntimeError(message)
        else:
            raise InvalidInteractionStageError(classname=self.__class__.__name__, expected_ip=(self.INTERACTION_TYPE, MAL_INTERACTION_STAGES.PUBSUB_DEREGISTER_ACK), ip=(interaction_type, interaction_stage))

    def receive_notify(self, signature):
        message = self.receive_message(signature)
        interaction_type = message.header.interaction_type
        interaction_stage = message.header.interaction_stage
        is_error_message = message.header.is_error_message
        if not is_error_message and  interaction_stage == MAL_INTERACTION_STAGES.PUBSUB_NOTIFY:
            return message
        elif is_error_message and interaction_type == self.INTERACTION_TYPE and interaction_stage == MAL_INTERACTION_ERRORS.PUBSUB_NOTIFY_ERROR:
            raise RuntimeError(message)
        else:
            raise InvalidInteractionStageError(classname=self.__class__.__name__, expected_ip=(self.INTERACTION_TYPE, MAL_INTERACTION_STAGES.PUBSUB_NOTIFY), ip=(interaction_type, interaction_stage))

