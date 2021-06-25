import pickle
import xml.dom.minidom
import re
import sys
import logging

from malpydefinitions import MALPY_ENCODING
from mo import mal, com, mc
from mo.com.services import *
from mo.mc.services import *

MAL_MODULES = [
    'mo.mal', 'mo.com', 'mo.mc',
    'mo.com.services.archive',
    'mo.com.services.activitytracking',
    'mo.com.services.event',
    'mo.mc.services.action',
    'mo.mc.services.aggregation',
    'mo.mc.services.alert',
    'mo.mc.services.check',
    'mo.mc.services.conversion',
    'mo.mc.services.group',
    'mo.mc.services.parameter',
    'mo.mc.services.statistic'
    ]


class Encoder(object):
    encoding = None
    parent = None

    def encode(self, message):
        raise NotImplementedError("This is to be implemented.")
        return message

    def decode(self, message):
        raise NotImplementedError("This is to be implemented.")
        return message


class PickleEncoder(Encoder):
    encoding = MALPY_ENCODING.PICKLE

    def encode(self, message):
        return pickle.dumps(message)

    def decode(self, message):
        return pickle.loads(message)


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

    def decode(self, message):
        decoded_body = self.decode_body(message.msg_parts)
        decoded_message = mal.MALMessage(header=message.header,
                                         msg_parts=decoded_body)
        return decoded_message

    def encode_body(self, body):

        def _encode_internal(element, parent):
            domdoc = parent.ownerDocument

            # The node name is attribName if it exists, otherwise its type
            # ex: <longElement> ?? </longElement> or <Identifier> ?? </Identifier>
            nodename = element.attribName or type(element).__name__
            subnode = parent.appendChild(domdoc.createElement(nodename))

            # Deal with the Null type:
            if element.value is None:
                # ex: <longElement xsi:nul="True" /> or <Identifier xsi:nul="True" />
                # It's a leaf, we don't recurse deeper.
                subnode.setAttribute('xsi:nil', 'true')
            # if it's a list, it means this is a composite or a list of thing
            elif type(element.value) is list:
                # so we recurse over each item and append them below the objects
                # ex: the ?? is defined with se same algorithm
                for subelement in element.value:
                    _encode_internal(subelement, subnode)
            # else it's an attribute we add a subnode
            else:
                # ex: <longElement><Long>9</Long><longElement> or <Identifier><Identifier>LIVE</Identifier></Identifier>
                # It's a leaf, we don't recurse deeper.
                attributenode = subnode.appendChild(domdoc.createElement(type(element).__name__))
                attributenode.appendChild(domdoc.createTextNode(str(element.value)))


        dom = xml.dom.getDOMImplementation()

        # Create the document header and its namespaces
        d = dom.createDocument(MAL_XML_NAMESPACE_URL, MAL_XML_BODY, None)
        rootElement = d.firstChild

        rootElement.setAttributeNS(XML_NAMESPACE, XMLNS_XSI, XML_XSI_NAMESPACE_URL);
        rootElement.setAttributeNS(XML_NAMESPACE, MAL_XML, MAL_XML_NAMESPACE_URL);

        # Recursively go through the object to encode it (a composite is a list of list)
        if type(body) is not list:
            body = [body]

        for element in body:
            _encode_internal(element, rootElement)
        encoded_body = d.toprettyxml(encoding="UTF-8")
        return encoded_body

    def decode_body(self, body):

        # If the XML document was indented, there will be text node made of tabs
        # and newline characters. Those are not relevant for decoding.
        emptyNodePattern = re.compile(r"^[\n\t]*$")
        maltypes = []
        for module in MAL_MODULES:
            maltypes.extend(dir(sys.modules[module]))

        def _cleanupEmptyChildNodes(node):

            clean_childNodes = []
            for element in node.childNodes:
                # We only keep nodes that do not match the pattern
                if not(element.nodeType is element.TEXT_NODE and re.match(emptyNodePattern, element.nodeValue)):
                    clean_childNodes.append(element)
                    _cleanupEmptyChildNodes(element)
            node.childNodes = clean_childNodes

        def str_to_class(classname):
            for module in MAL_MODULES:
                try:
                    return getattr(sys.modules[module], classname)
                except AttributeError:
                    pass
            raise RuntimeError("I don't know this object")

        def _decode_internal(node, elementName=None):
            logger = logging.getLogger(__name__)
            logger.debug("IN {} {}".format(node, elementName))

            internal = []

            # Either the node name is a MAL class or the name of the attribute
            # If it's a MAL class we recurse in its children and build the MALElement
            if node.nodeName in maltypes:
                objectClass = str_to_class(node.nodeName)

                # First case: it's Null and we reached a leaf
                if node.hasAttribute('xsi:nil') and node.getAttribute('xsi:nil'):
                    return objectClass(None, attribName=elementName)

                # Otherwise it's a MALElement to parse
                else:

                    for element in node.childNodes:
                        # If it's text node, we reached a leaf
                        if element.nodeType is element.TEXT_NODE:
                            castedValue = objectClass.value_type(element.nodeValue)
                            internal.append(castedValue)
                        elif element.nodeType is element.ELEMENT_NODE:
                            # If it's a NULL element, we reached a leave
                            if element.hasAttribute('xsi:nil') and element.getAttribute('xsi:nil') == "true":
                                internal.append(None)
                            # In all other cases, we recurse
                            else:
                                logger.debug('all other cases {}'.format(objectClass))
                                internal.append(_decode_internal(element))
                        else:
                            raise RuntimeError(element)
                if len(internal) == 1:
                    logger.debug("OUT {} {}".format(node, elementName))
                    return objectClass(internal[0])
                elif len(internal) == 0:
                    raise RuntimeError("len(internal) == 0", node)
                else:
                    logger.debug("more than one")
                    logger.debug("OUT {} {}".format( node, elementName))
                    return objectClass(internal, attribName=elementName)
            # If it's the name of the attribute, it either has MAL Element children
            # or is Null
            else:
                if node.nodeType is node.ELEMENT_NODE:
                    # Except for the first node, there should never be two consecutive name nodes
                    if elementName and elementName != MAL_XML_BODY:
                        raise RuntimeError("Below a name-tag should be a MAL Element")

                    # TODO: A sortir de la méthode
                    if node.nodeName == MAL_XML_BODY:
                        for element in node.childNodes:
                            internal.append(_decode_internal(element))
                        logger.debug("OUT {} {}".format(node, elementName))
                        return internal

                    elementName = node.nodeName

                    # First case: it's Null and we reached a leaf
                    if node.hasAttribute('xsi:nil') and node.getAttribute('xsi:nil'):
                        logger.debug("OUT {} {}".format( node, elementName))
                        return None
                    # Otherwise it's a MALElement to parse
                    else:
                        if len(node.childNodes) == 1:
                            logger.debug("OUT {} {}".format( node, elementName))
                            return _decode_internal(node.childNodes[0], elementName)
                        else:
                            # it's a list
                            internal = []
                            maltype = node.childNodes[0].nodeName + "List"
                            malobject = str_to_class(maltype)
                            for element in node.childNodes:
                                internal.append(_decode_internal(element))
                            logger.debug("OUT {} {}".format( node, elementName))
                            return malobject(internal)

        if body == b"":
            return None
        d = xml.dom.minidom.parseString(body)
        rootElement = d.firstChild
        _cleanupEmptyChildNodes(rootElement)
        return _decode_internal(rootElement)
