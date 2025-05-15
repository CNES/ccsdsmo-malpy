# SPDX-FileCopyrightText: 2025 Olivier Churlaud <olivier@churlaud.com>
# SPDX-FileCopyrightText: 2025 CNES
#
# SPDX-License-Identifier: MIT

import copy
import time
from enum import IntEnum

from .maltypes import InteractionTypeEnum, Errors

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

    # PubSub
    PUBSUB_REGISTER_ERROR = 2
    PUBSUB_PUBLISH_REGISTER_ERROR = 4
    PUBSUB_DEREGISTER_ERROR = 8
    PUBSUB_PUBLISH_DEREGISTER_ERROR = 10
    PUBSUB_NOTIFY_ERROR = 17
#    PUBSUB_PUBLISH_ERROR =



class MALError(Exception):
    def __init__(self, messageHeader, error, extraInformation=None):
        self.messageHeader = messageHeader
        self.error = error
        self.extraInformation = extraInformation
        super().__init__("MAL Error: [{}]{} {}".format(error.value, error.name, extraInformation))


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

    AREA = None
    AREA_VERSION = None
    SERVICE = None
    OPERATION = None
    INTERACTION_TYPE = None

    def __init__(self, transport, encoding):
        self.transport = transport
        self.encoding = encoding
        self.transport.parent = self
        self.encoding.parent = self
        self.interaction_terminated = False

    def send_message(self, message):
        raw_message = self.encoding.encode(message)
        self.transport.send(raw_message)

    def receive_message(self):
        raw_message = self.transport.recv()
        return self.encoding.decode(raw_message)

    def check_message(self, message, expected_interaction_stage, expected_interaction_error=None):
        is_error_message = message.header.is_error_message
        interaction_type = message.header.interaction_type
        interaction_stage = message.header.interaction_stage

        is_expected_interaction = (interaction_type == self.INTERACTION_TYPE and interaction_stage == expected_interaction_stage)
        is_expected_error = (interaction_type == self.INTERACTION_TYPE and interaction_stage == expected_interaction_error)

        if not is_error_message and is_expected_interaction:
            # If expected intearction, we check for the operation correctness
            if message.header.service_area != self.AREA:
                raise MALError(messageHeader=message.header, error=Errors.Unsupported_Area)
            if message.header.service != self.SERVICE:
                raise MALError(messageHeader=message.header, error=Errors.Unsupported_Service)
            if message.header.operation != self.OPERATION:
                raise MALError(messageHeader=message.header, error=Errors.Unsupported_Operation)
            if  message.header.area_version != self.AREA_VERSION:
                raise MALError(messageHeader=message.header, error=Errors.Unsupported_Area_Version)
        elif is_error_message and is_expected_error:
            self.interaction_terminated = True
            raise MALError(message.header, Errors(message.msg_parts[0].internal_value))
        else:
            raise InvalidInteractionStageError(classname=self.__class__.__name__, expected_ip=(self.INTERACTION_TYPE, expected_interaction_stage), ip=(interaction_type, interaction_stage))


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

    def receive_send(self):
        message = self.receive_message()
        self.check_message(message, MAL_INTERACTION_STAGES.SEND)
        self.interaction_terminated = True
        return message


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

    def receive_submit(self):
        message = self.receive_message()
        self.define_header(message.header)
        self.check_message(message, MAL_INTERACTION_STAGES.SUBMIT)
        return message

    def ack(self, body, async_send=False):
        header = self.create_message_header(MAL_INTERACTION_STAGES.SUBMIT_ACK)
        message = MALMessage(header=header, msg_parts=body)
        self.send_message(message)
        self.interaction_terminated = True

    def error(self, body):
        header = self.create_message_header(MAL_INTERACTION_ERRORS.SUBMIT_ERROR)
        header.is_error_message = True
        message = MALMessage(header=header, msg_parts=body)
        self.send_message(message)
        self.interaction_terminated = True


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

    def receive_ack(self):
        message = self.receive_message()
        self.check_message(message, MAL_INTERACTION_STAGES.SUBMIT_ACK, MAL_INTERACTION_ERRORS.SUBMIT_ERROR)
        self.interaction_terminated = True
        return message


class RequestProviderHandler(ProviderHandler):
    """
    A provider handler for operations belonging to the SEND
    interaction pattern
    """

    INTERACTION_TYPE = InteractionTypeEnum.REQUEST

    def receive_request(self):
        message = self.receive_message()
        self.define_header(message.header)
        self.check_message(message, MAL_INTERACTION_STAGES.REQUEST)
        return message

    def response(self, body, async_send=False):
        header = self.create_message_header(MAL_INTERACTION_STAGES.REQUEST_RESPONSE)
        message = MALMessage(header=header, msg_parts=body)
        self.send_message(message)
        self.interaction_terminated = True

    def error(self, body):
        header = self.create_message_header(MAL_INTERACTION_ERRORS.REQUEST_ERROR)
        header.is_error_message = True
        message = MALMessage(header=header, msg_parts=body)
        self.send_message(message)
        self.interaction_terminated = True


class RequestConsumerHandler(ConsumerHandler):
    """
    A consumer handler for operations belonging to the SEND
    interaction pattern
    """

    INTERACTION_TYPE = InteractionTypeEnum.REQUEST

    def request(self, body):
        header = self.create_message_header(MAL_INTERACTION_STAGES.REQUEST)
        message = MALMessage(header=header, msg_parts=body)
        self.send_message(message)

    def receive_response(self):
        message = self.receive_message()
        self.check_message(message, MAL_INTERACTION_STAGES.REQUEST_RESPONSE, MAL_INTERACTION_ERRORS.REQUEST_ERROR)
        self.interaction_terminated = True
        return message


class InvokeProviderHandler(ProviderHandler):
    """
    A provider handler for operations belonging to the SEND
    interaction pattern
    """

    INTERACTION_TYPE = InteractionTypeEnum.INVOKE

    def receive_invoke(self):
        message = self.receive_message()
        self.define_header(message.header)
        self.check_message(message, MAL_INTERACTION_STAGES.INVOKE)
        return message

    def ack(self, body, async_send=False):
        header = self.create_message_header(MAL_INTERACTION_STAGES.INVOKE_ACK)
        message = MALMessage(header=header, msg_parts=body)
        self.send_message(message)

    def ack_error(self, body):
        header = self.create_message_header(MAL_INTERACTION_ERRORS.INVOKE_ACK_ERROR)
        header.is_error_message = True
        message = MALMessage(header=header, msg_parts=body)
        self.send_message(message)
        self.interaction_terminated = True

    def response(self, body, async_send=False):
        header = self.create_message_header(MAL_INTERACTION_STAGES.INVOKE_RESPONSE)
        message = MALMessage(header=header, msg_parts=body)
        self.send_message(message)
        self.interaction_terminated = True

    def response_error(self, body):
        header = self.create_message_header(MAL_INTERACTION_ERRORS.INVOKE_RESPONSE_ERROR)
        header.is_error_message = True
        message = MALMessage(header=header, msg_parts=body)
        self.send_message(message)
        self.interaction_terminated = True


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

    def receive_ack(self):
        message = self.receive_message()
        self.check_message(message, MAL_INTERACTION_STAGES.INVOKE_ACK, MAL_INTERACTION_ERRORS.INVOKE_ACK_ERROR)
        return message

    def receive_response(self):
        message = self.receive_message()
        self.check_message(message, MAL_INTERACTION_STAGES.INVOKE_RESPONSE, MAL_INTERACTION_ERRORS.INVOKE_RESPONSE_ERROR)
        self.interaction_terminated = True
        return message


class ProgressProviderHandler(ProviderHandler):
    """
    A provider handler for operations belonging to the SEND
    interaction pattern
    """

    INTERACTION_TYPE = InteractionTypeEnum.PROGRESS

    def receive_progress(self):
        message = self.receive_message()
        self.define_header(message.header)
        self.check_message(message, MAL_INTERACTION_STAGES.PROGRESS)
        return message

    def ack(self, body, async_send=False):
        header = self.create_message_header(MAL_INTERACTION_STAGES.PROGRESS_ACK)
        message = MALMessage(header=header, msg_parts=body)
        self.send_message(message)

    def ack_error(self, body):
        header = self.create_message_header(MAL_INTERACTION_ERRORS.PROGRESS_ACK_ERROR)
        header.is_error_message = True
        message = MALMessage(header=header, msg_parts=body)
        self.send_message(message)

    def update(self, body):
        header = self.create_message_header(MAL_INTERACTION_STAGES.PROGRESS_UPDATE)
        message = MALMessage(header=header, msg_parts=body)
        self.send_message(message)

    def update_error(self, body):
        header = self.create_message_header(MAL_INTERACTION_ERRORS.PROGRESS_UPDATE_ERROR)
        header.is_error_message = True
        message = MALMessage(header=header, msg_parts=body)
        self.send_message(message)
        self.interaction_terminated = True

    def response(self, body, async_send=False):
        header = self.create_message_header(MAL_INTERACTION_STAGES.PROGRESS_RESPONSE)
        message = MALMessage(header=header, msg_parts=body)
        self.send_message(message)
        self.interaction_terminated = True

    def response_error(self, body):
        header = self.create_message_header(MAL_INTERACTION_ERRORS.PROGRESS_RESPONSE_ERROR)
        header.is_error_message = True
        message = MALMessage(header=header, msg_parts=body)
        self.send_message(message)
        self.interaction_terminated = True


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

    def receive_ack(self):
        message = self.receive_message()
        self.check_message(message, MAL_INTERACTION_STAGES.PROGRESS_ACK, MAL_INTERACTION_ERRORS.PROGRESS_ACK_ERROR)
        return message

    def receive_update_or_response(self):
        """ As it is not possible to know beforehand if the received message is
        an update or the final response, we only do receive_update. The content of
        the header message will let us know te corresponding state.
        """
        message = self.receive_message()
        if message.header.interaction_stage in (MAL_INTERACTION_STAGES.PROGRESS_UPDATE, MAL_INTERACTION_ERRORS.PROGRESS_UPDATE_ERROR):
            self.check_message(message, MAL_INTERACTION_STAGES.PROGRESS_UPDATE, MAL_INTERACTION_ERRORS.PROGRESS_UPDATE_ERROR)
        elif message.header.interaction_stage in (MAL_INTERACTION_STAGES.PROGRESS_RESPONSE, MAL_INTERACTION_ERRORS.PROGRESS_RESPONSE_ERROR):
            self.check_message(message, MAL_INTERACTION_STAGES.PROGRESS_RESPONSE, MAL_INTERACTION_ERRORS.PROGRESS_RESPONSE_ERROR)
            self.interaction_terminated = True
        else:
            self.check_message(message, None)
        return message

    def receive_update(self):
        return self.receive_update_or_response()

    def receive_response(self):
        return self.receive_update_or_response()


class PubSubProviderHandler(ProviderHandler):

    INTERACTION_TYPE = InteractionTypeEnum.PUBSUB

    def publish_register(self, body):
        header = self.create_message_header(MAL_INTERACTION_STAGES.PUBSUB_PUBLISH_REGISTER)
        message = MALMessage(header=header, msg_parts=body)
        self.send_message(message)

    def receive_publish_register_ack(self):
        message = self.receive_message()
        self.check_message(message, MAL_INTERACTION_STAGES.PUBSUB_PUBLISH_REGISTER_ACK, MAL_INTERACTION_ERRORS.PUBSUB_PUBLISH_REGISTER_ERROR)
        return message

    def publish_deregister(self, body):
        header = self.create_message_header(MAL_INTERACTION_STAGES.PUBSUB_PUBLISH_DEREGISTER)
        message = MALMessage(header=header, msg_parts=body)
        self.send_message(message)

    def receive_publish_deregister_ack(self):
        message = self.receive_message()
        self.check_message(message, MAL_INTERACTION_STAGES.PUBSUB_PUBLISH_DEREGISTER_ACK, MAL_INTERACTION_ERRORS.PUBSUB_PUBLISH_DEREGISTER_ERROR)
        self.interaction_terminated = True
        return message

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

    def receive_registration_message(self):
        message = self.receive_message()
        self.define_header(message.header)
        if message.header.interaction_stage == MAL_INTERACTION_STAGES.PUBSUB_REGISTER:
            self.check_message(message, MAL_INTERACTION_STAGES.PUBSUB_REGISTER)
        elif message.header.interaction_stage == MAL_INTERACTION_STAGES.PUBSUB_DEREGISTER:
            self.check_message(message, MAL_INTERACTION_STAGES.PUBSUB_DEREGISTER)
        else:
            self.check_message(message, None)
        return message

    def register_ack(self, body):
        header = self.create_message_header(MAL_INTERACTION_STAGES.PUBSUB_REGISTER_ACK)
        self.define_header(header)
        message = MALMessage(header=header, msg_parts=body)
        self.send_message(message)

    def register_error(self, body):
        header = self.create_message_header(MAL_INTERACTION_ERRORS.PUBSUB_REGISTER_ERROR)
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
        header = self.create_message_header(MAL_INTERACTION_ERRORS.PUBSUB_DEREGISTER_ERROR)
        header.is_error_message = True
        self.define_header(header)
        message = MALMessage(header=header, msg_parts=body)
        self.send_message(message)

    def notify(self, body, uri_to):
        header = self.create_message_header(MAL_INTERACTION_STAGES.PUBSUB_NOTIFY, uri_to=uri_to)
        message = MALMessage(header=header, msg_parts=body)
        self.send_message(message)

    def notify_error(self, body):
        header = self.create_message_header(MAL_INTERACTION_ERRORS.PUBSUB_NOTIFY_ERROR)
        self.define_header(header)
        message = MALMessage(header=header, msg_parts=body)
        self.send_message(message)
        self.interaction_terminated = True

    def receive_publish_registration_message(self):
        message = self.receive_message()
        self.define_header(message.header)
        if message.header.interaction_stage == MAL_INTERACTION_STAGES.PUBSUB_PUBLISH_REGISTER:
            self.check_message(message, MAL_INTERACTION_STAGES.PUBSUB_PUBLISH_REGISTER)
        elif message.header.interaction_stage == MAL_INTERACTION_STAGES.PUBSUB_PUBLISH_DEREGISTER:
            self.check_message(message, MAL_INTERACTION_STAGES.PUBSUB_PUBLISH_DEREGISTER)
        else:
            self.check_message(message, None)
        return message

    def publish_register_ack(self, body):
        header = self.create_message_header(MAL_INTERACTION_STAGES.PUBSUB_PUBLISH_REGISTER_ACK)
        self.define_header(header)
        message = MALMessage(header=header, msg_parts=body)
        self.send_message(message)

    def publish_register_error(self, body):
        header = self.create_message_header(MAL_INTERACTION_ERRORS.PUBSUB_PUBLISH_REGISTER_ERROR)
        header.is_error_message = True
        self.define_header(header)
        message = MALMessage(header=header, msg_parts=body)
        self.send_message(message)
        self.interaction_terminated = True

    def publish_deregister_ack(self, body):
        header = self.create_message_header(MAL_INTERACTION_STAGES.PUBSUB_PUBLISH_DEREGISTER_ACK)
        self.define_header(header)
        message = MALMessage(header=header, msg_parts=body)
        self.send_message(message)
        self.interaction_terminated = True

    def receive_publish(self):
        message = self.receive_message()
        self.define_header(message.header)
        self.check_message(message, MAL_INTERACTION_STAGES.PUBSUB_PUBLISH)
        return message

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

    def receive_register_ack(self):
        message = self.receive_message()
        self.check_message(message, MAL_INTERACTION_STAGES.PUBSUB_REGISTER_ACK, MAL_INTERACTION_ERRORS.PUBSUB_REGISTER_ERROR)
        return message

    def deregister(self, body):
        header = self.create_message_header(MAL_INTERACTION_STAGES.PUBSUB_DEREGISTER)
        message = MALMessage(header=header, msg_parts=body)
        self.send_message(message)

    def receive_deregister_ack(self):
        message = self.receive_message()
        self.check_message(message, MAL_INTERACTION_STAGES.PUBSUB_DEREGISTER_ACK, MAL_INTERACTION_ERRORS.PUBSUB_DEREGISTER_ERROR)
        self.interaction_terminated = True
        return message

    def receive_notify(self):
        message = self.receive_message()
        self.check_message(message, MAL_INTERACTION_STAGES.PUBSUB_NOTIFY, MAL_INTERACTION_ERRORS.PUBSUB_NOTIFY_ERROR)
        self.interaction_terminated = True
        return message
