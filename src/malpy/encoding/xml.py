import datetime
import xml.dom.minidom
import logging
import re
import sys
from enum import IntEnum

from malpy.malpydefinitions import MALPY_ENCODING
from malpy.mo import mal

from .abstract_encoding import Encoder

MAL_XML_NAMESPACE_URL = "http://www.ccsds.org/schema/malxml/MAL"
MAL_XML = "xmlns:malxml"
MAL_XML_BODY = 'malxml:Body'
XML_XSI_NAMESPACE_URL = "http://www.w3.org/2001/XMLSchema-instance"
XML_NAMESPACE = "http://www.w3.org/2000/xmlns/"
XMLNS_XSI = "xmlns:xsi"
XMLNS = "xmlns"


class XMLEncoder(Encoder):
    encoding = MALPY_ENCODING.XML

    def encode(self, message):
        encoded_body = self.encode_body(message.msg_parts)
        encoded_message = mal.MALMessage(header=message.header,
                                         msg_parts=encoded_body)
        return encoded_message

    def decode(self, message, signature):
        decoded_body = self.decode_body(message.msg_parts, signature)
        decoded_message = mal.MALMessage(header=message.header,
                                         msg_parts=decoded_body)
        return decoded_message

    def encode_body(self, body):

        def _encode_internal(element, parent):
            domdoc = parent.ownerDocument

            if element is None:
                return

            # The node name is attribName if it exists, otherwise its type
            # ex: <longElement> ?? </longElement> or <Identifier> ?? </Identifier>
            nodename = element.attribName or type(element).__name__
            subnode = parent.appendChild(domdoc.createElement(nodename))

            # Deal with the Null type:
            if element.internal_value is None:
                # ex: <longElement xsi:nul="True" /> or <Identifier xsi:nul="True" />
                # It's a leaf, we don't recurse deeper.
                subnode.setAttribute('xsi:nil', 'true')
            # if it's a list, it means this is a composite or a list of thing
            elif type(element.internal_value) is list:
                # so we recurse over each item and append them below the objects
                # ex: the ?? is defined with the same algorithm
                for subelement in element.internal_value:
                    _encode_internal(subelement, subnode)
            # else it's an attribute we add a subnode
            else:
                if issubclass(type(element), mal.Composite):
                    # it's a composite, so we recurse
                    _encode_internal(element.internal_value, subnode)
                else:
                    # ex: <longElement><Long>9</Long><longElement> or <Identifier><Identifier>LIVE</Identifier></Identifier>
                    # It's a leaf, we don't recurse deeper.
                    attributenode = subnode.appendChild(domdoc.createElement(type(element).__name__))
                    # Special case for IntEnum (the encoded message is a string that we convert to enums)
                    if issubclass(type(element.internal_value), IntEnum):
                        value = element.internal_value.name
                    # Special case for Blob (the value is b'toto' and we want 'toto')
                    elif type(element) is mal.maltypes.Blob:
                        value = element.internal_value.hex()
                    # Special case for Time (value is a timestamp and we want YYYY-MM-DDThh:mm:ss.sss)
                    elif type(element) is mal.maltypes.Time:
                        value = datetime.datetime.fromtimestamp(element.internal_value).isoformat()
                        if '.' in value:  # it means we have microsecond
                            value = value[:-3]  # we reduce to millisecond
                        else:
                            value += ".000"
                    # Special case for FineTime (value is a timestamp and we want YYYY-MM-DDThh:mm:ss.sssssssss)
                    elif type(element) is mal.maltypes.FineTime:
                        # get YYYY-MM-DDThh:mm:ss.ssssss
                        value = datetime.datetime.fromtimestamp(element.internal_value).isoformat()
                        if '.' in value:  # it means we have microsecond
                            value += 000   # we add zeroes to nanoseconds
                        else:
                            value += ".000000000"
                    # Normal case
                    else:
                        value = str(element.internal_value)
                    attributenode.appendChild(domdoc.createTextNode(value))

        dom = xml.dom.getDOMImplementation()

        # Create the document header and its namespaces
        d = dom.createDocument(MAL_XML_NAMESPACE_URL, MAL_XML_BODY, None)
        rootElement = d.firstChild

        rootElement.setAttributeNS(XML_NAMESPACE, XMLNS_XSI, XML_XSI_NAMESPACE_URL)
        rootElement.setAttributeNS(XML_NAMESPACE, MAL_XML, MAL_XML_NAMESPACE_URL)

        # Recursively go through the object to encode it (a composite is a list of list)
        if type(body) is not list:
            body = [body]

        for element in body:
            _encode_internal(element, rootElement)
        encoded_body = d.toprettyxml(encoding="UTF-8")
        return encoded_body

    def decode_body(self, body, signature):

        # If the XML document was indented, there will be text node made of tabs
        # and newline characters. Those are not relevant for decoding.
        emptyNodePattern = re.compile(r"^[\n\t]*$")

        def _cleanupEmptyChildNodes(node):
            clean_childNodes = []
            for element in node.childNodes:
                # We only keep nodes that do not match the pattern
                if not(element.nodeType is element.TEXT_NODE and re.match(emptyNodePattern, element.nodeValue)):
                    clean_childNodes.append(element)
                    _cleanupEmptyChildNodes(element)
            node.childNodes = clean_childNodes


        def _decode_composite(element, objectClass):
            """
            <IdBooleanPair>
                <id>
                        <Identifier>TOTO</Identifier>
                </id>
                <value>
                        <Boolean>False</Boolean>
                </value>
            </IdBooleanPair>
            """
            logging.debug("_decode_composite")
            subelements = element.childNodes
            resultList = []
            for k in range(len(subelements)):
                resultList.append(
                    _decode_internal2(subelements[k], objectClass._fieldTypes[k].type)
                    )
            return objectClass(resultList)

        def _decode_list(element, objectClass, name=None):
            """
            <TimeList>
                <Time>
                        <Time>2024-10-19T17:21:26.929</Time>
                </Time>
                <Time>
                        <Time>2024-10-19T17:21:26.929</Time>
                </Time>
                <Time>
                        <Time>2024-10-19T17:21:26.929</Time>
                </Time>
            </TimeList>
            """
            logging.debug("_decode_list")
            subelements = element.childNodes
            resultList = []
            for subelement in subelements:
                resultList.append(
                    _decode_internal2(subelement, objectClass._fieldTypes.type)
                )
            return objectClass(resultList)

        def _decode_enum(element, objectClass):
            """
            <InteractionType>
                <InteractionType>SEND</InteractionType>
            </InteractionType>
            """

            if len(element.childNodes) == 0:  # It's certainly a NULL
                if element.hasAttribute('xsi:nil') and element.getAttribute('xsi:nil') == "true":
                    return objectClass(None)
                else:
                    raise RuntimeError("elementNode, but not None")

            # For all the other cases
            if len(element.childNodes) != 1:
                raise RuntimeError("This is an attribute: it shall have exactly one child, got {}".format(len(element.childNodes)))

            subelement = element.childNodes[0]

            if len(subelement.childNodes) != 1:
                raise RuntimeError("This is an attribute: it shall have exactly one child, got {}".format(len(element.childNodes)))

            if objectClass.__name__ not in ('Attribute', subelement.nodeName):
                raise RuntimeError("ElementName shall be the name of the attribute: got {} instead of {}"
                                    .format(subelement.nodeName, objectClass.__name__))
            subelement = subelement.childNodes[0]

            if subelement.nodeType is subelement.TEXT_NODE:
                # Special case for IntEnum (the encoding message is a string that we convert to enums)
                for v in list(objectClass.value_type):
                    if v.name == subelement.nodeValue:
                        return objectClass(v)
            else:
                raise RuntimeError("node should have been of type TEXT", subelement)

        def _decode_attribute(element, objectClass, name=None):
            """
            <Time>
                <Time>2024-10-20T12:22:00.999</Time>
            </Time>
            or
            <timeName>
                <Time>2024-10-20T12:22:00.999</Time>
            </timeName>
            or
            <Time xsi:nil="true"/>
            """
            logging.debug("_decode_attribute")
            
            if len(element.childNodes) == 0:  # It's certainly a NULL
                if element.hasAttribute('xsi:nil') and element.getAttribute('xsi:nil') == "true":
                    return objectClass(None)
                else:
                    raise RuntimeError("elementNode, but not None")

            # For all the other cases
            if len(element.childNodes) != 1:
                raise RuntimeError("This is an attribute: it shall have exactly one child, got {}".format(len(element.childNodes)))

            subelement = element.childNodes[0]

            if len(subelement.childNodes) != 1:
                raise RuntimeError("This is an attribute: it shall have exactly one child, got {}".format(len(element.childNodes)))

            if objectClass.__name__ not in ('Attribute', subelement.nodeName):
                raise RuntimeError("ElementName shall be the name of the attribute: got {} instead of {}"
                                    .format(subelement.nodeName, objectClass.__name__))
            
            if objectClass.__name__ == "Attribute":
                # The nodeName is supposed to be the concrete attribute type
                attributeType = getattr(sys.modules["malpy.mo.mal"], subelement.nodeName)
            else:
                attributeType = objectClass
            subelement = subelement.childNodes[0]

            if subelement.nodeType is subelement.TEXT_NODE:
                # Handle 'blob' special case
                if attributeType.__name__ == "Blob":
                    value = bytes.fromhex(subelement.nodeValue)
                # Special case for Time (value is a timestamp and we want YYYY-MM-DDThh:mm:ss.sss)
                elif attributeType.__name__ == "Time":
                    value = datetime.datetime.strptime(subelement.nodeValue, '%Y-%m-%dT%H:%M:%S.%f').timestamp()
                # Special case for FineTime (value is a timestamp and we want YYYY-MM-DDThh:mm:ss.sssssssss)
                elif attributeType.__name__ == "FineTime":
                    value = datetime.datetime.strptime(subelement.nodeValue[:-3], '%Y-%m-%dT%H:%M:%S.%f').timestamp()
                    value += int(subelement.nodeValue[-3:]) * 1e-9
                elif attributeType.__name__ == "Boolean":
                    booleanTable = {
                        'True': True,
                        'False': False
                    }
                    try:
                        value = booleanTable[subelement.nodeValue]
                    except KeyError:
                        raise RuntimeError("Boolean expects values 'True/False', got: {}".format(subelement.nodeValue))
                else:
                    value = subelement.nodeValue

                return attributeType(value)
            else:
                raise RuntimeError("node should have been of type TEXT", subelement)

        def _decode_internal2(body, signature):
            if mal.ElementList in signature.mro():
                return _decode_list(body, signature)
            elif mal.Composite in signature.mro():
                return _decode_composite(body, signature)
            elif mal.AbstractEnum in signature.mro():
                return _decode_enum(body, signature)
            elif mal.Attribute in signature.mro():
                return _decode_attribute(body, signature)
            else:
                raise RuntimeError("I cannot decode this type: {}".format(signature))



        if body == b"":
            return None
        d = xml.dom.minidom.parseString(body)
        rootElement = d.firstChild
        _cleanupEmptyChildNodes(rootElement)
        messageElements = rootElement.childNodes

        if type(signature) == type(list):
            decodedBody = []
            for i in range(len(signature)):
                decodedBody.append(_decode_internal2(messageElements[i], signature[i]))
        else:
            subelement = messageElements[0]
            decoded_body = _decode_internal2(subelement, signature)

        return decoded_body
