import datetime
import pickle
import xml.dom.minidom
import re
import sys
from enum import IntEnum

from malpy.malpydefinitions import MALPY_ENCODING
from malpy.mo import mal, com, mc
from malpy.mo.com.services import *
from malpy.mo.mc.services import *

LOG_LEVEL = "INFO"

class Debug():
    depth = 0
    def IN(self, *args):
        self.DEBUG('>', *args)
        self.depth += 1

    def OUT(self, *args):
        self.depth -= 1
        self.DEBUG('<', *args)
        
    def DEBUG(self, *args):
        if LOG_LEVEL == "DEBUG":
            print(self.depth*'-', *args)
debug = Debug()
def DEBUG(*args):
    debug.DEBUG(*args)
def DEBUG_IN(*args):
    debug.IN(*args)
def DEBUG_OUT(*args):
    debug.OUT(*args)


MAL_MODULES = [
    'malpy.mo.mal', 'malpy.mo.com', 'malpy.mo.mc',
    'malpy.mo.com.services.archive',
    'malpy.mo.com.services.activitytracking',
    'malpy.mo.com.services.event',
    'malpy.mo.mc.services.action',
    'malpy.mo.mc.services.aggregation',
    'malpy.mo.mc.services.alert',
    'malpy.mo.mc.services.check',
    'malpy.mo.mc.services.conversion',
    'malpy.mo.mc.services.group',
    'malpy.mo.mc.services.parameter',
    'malpy.mo.mc.services.statistic'
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
            DEBUG_IN("IN", node, elementName)

            internal = []

            # Either the node name is a MAL class or the name of the attribute
            # If it's a MAL class we recurse in its children and build the MALElement
            if node.nodeName in maltypes:
                objectClass = str_to_class(node.nodeName)
                
                # First case: it's Null and we reached a leaf
                if node.hasAttribute('xsi:nil') and node.getAttribute('xsi:nil'):
                    DEBUG_OUT('Leaf > xsi:nil', 'value=None')
                    return objectClass(None, attribName=elementName)

                # Otherwise it's a MALElement to parse
                else:
                    for element in node.childNodes:
                        # If it's text node, we reached a leaf
                        if element.nodeType is element.TEXT_NODE:
                            DEBUG('* Leaf > TextNode', 'value={}'.format(element.nodeValue))
                            # Special case for IntEnum (the encoding message is a string that we convert to enums)
                            if issubclass(objectClass.value_type, IntEnum):
                                for v in list(objectClass.value_type):
                                    if v.name == element.nodeValue:
                                        castedValue = v
                                        break
                            # normal cases
                            else:
                                # Handle 'blob' special case
                                if objectClass.value_type == bytes and type(element.nodeValue) == str:
                                    value = bytes.fromhex(element.nodeValue)
                                # Special case for Time (value is a timestamp and we want YYYY-MM-DDThh:mm:ss.sss)
                                elif objectClass.value_type == float and type(element.nodeValue) == str and len(element.nodeValue) == len('YYYY-MM-DDThh:mm:ss.sss'):
                                    value = datetime.datetime.strptime(element.nodeValue, '%Y-%m-%dT%H:%M:%S.%f').timestamp()
                                # Special case for FineTime (value is a timestamp and we want YYYY-MM-DDThh:mm:ss.sssssssss)
                                elif objectClass.value_type == float and type(element.nodeValue) == str and len(element.nodeValue) == len('YYYY-MM-DDThh:mm:ss.sssssssss'):
                                    value = datetime.datetime.strptime(element.nodeValue[:-3], '%Y-%m-%dT%H:%M:%S.%f').timestamp()
                                    value += int(element.nodeValue[-3:]) * 1e-9
                                else:
                                    value = element.nodeValue
                                castedValue = objectClass.value_type(value)
                            internal.append(castedValue)
                        elif element.nodeType is element.ELEMENT_NODE:
                            # If it's a NULL element, we reached a leaf again
                            if element.hasAttribute('xsi:nil') and element.getAttribute('xsi:nil') == "true":
                                DEBUG('* Leaf > xsi:nil', 'value=None')
                                internal.append(None)
                            # In all other cases, we recurse
                            else:
                                DEBUG('* Recurse on', element.nodeName)
                                internal.append(_decode_internal(element))
                        else:
                            raise RuntimeError(element)
                if len(internal) == 1:
                    parsed_object = objectClass(internal[0])
                    DEBUG_OUT('return single Object', node, elementName, parsed_object)
                    return parsed_object
                elif len(internal) == 0:
                    raise RuntimeError("len(internal) == 0", node)
                else:
                    parsed_object = objectClass(internal, attribName=elementName)
                    DEBUG_OUT('return list or composite', parsed_object, elementName)
                    return parsed_object
            # If it's the name of the attribute, it either has MAL Element children
            # or is Null
            else:
                if node.nodeType is node.ELEMENT_NODE:
                    # Except for the first node, there should never be two consecutive name nodes
                    if elementName and elementName != MAL_XML_BODY:
                        raise RuntimeError("Below a name-tag should be a MAL Element")

                    # TODO: A sortir de la méthode
                    # Recursion starts here
                    if node.nodeName == MAL_XML_BODY:
                        for element in node.childNodes:
                            internal.append(_decode_internal(element))
                        DEBUG_OUT("The message is completely decoded.")
                        return internal

                    elementName = node.nodeName

                    # It's Null and we reached a leaf
                    if node.hasAttribute('xsi:nil') and node.getAttribute('xsi:nil'):
                        DEBUG_OUT('Return Leaf > xsi:nil', 'value=None')
                        return None
                    # Otherwise it's a MALElement to parse
                    else:
                        if len(node.childNodes) == 1:
                            DEBUG("Recurse on {}".format(elementName))
                            decoded_object = _decode_internal(node.childNodes[0], elementName)
                            DEBUG_OUT("Return content", decoded_object)
                            return decoded_object
                        else:
                            # it's a list or a composite, we don't know their type before the end of the recursion
                            internal = []
                            for element in node.childNodes:
                                internal.append(_decode_internal(element))
                            DEBUG_OUT("Return composite or list", "value={}".format(elementName))
                            return internal

        if body == b"":
            return None
        d = xml.dom.minidom.parseString(body)
        rootElement = d.firstChild
        _cleanupEmptyChildNodes(rootElement)
	
        return _decode_internal(rootElement)



class JSONEncoder(Encoder):
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

        def _encode_internal(element,isInList):
            doc=''
            # The node name is attribName if it exists, otherwise its type
            nodename = element.attribName or type(element).__name__

            # Deal with the Null type:
            if element.internal_value is None:
                # It's a leaf, we don't recurse deeper.
               doc = doc +  "\"{}\" : ".format(nodename) + "null,"
               if isInList:
                  doc = '{' + doc[0:-1] + '},' # Remove last caractere (comma) of doc String befor add }

            # if it's a list, it means this is a composite or a list of thing
            elif type(element.internal_value) is list:
                # so we recurse over each item and append them below the objects
                # ex: the ?? is defined with se same algorithm
                if nodename.find('List') > 0:
                    doc = doc + "\"{}\" : [".format(nodename) 
                    for subelement in element.internal_value:
                        doc = doc + _encode_internal(subelement, True)
                    doc = doc[0:-1] + '],' # Remove last caractere (comma) of doc String befor add }
                else:
                    if isInList:
                        doc = doc + ' {'
                    else:
                        doc = doc + "\"{}\" : ".format(nodename) +' {'
                    for subelement in element.internal_value:
                        doc = doc + _encode_internal(subelement, False)
                    doc = doc[0:-1] + '},' # Remove last caractere (comma) of doc String befor add }

            # else it's an attribute we add a subnode
            else:
                # It's a leaf, we don't recurse deeper.
                # Special case for IntEnum (the encoding message is a string that we convert to enums)
                if issubclass(type(element.internal_value), IntEnum):
                    value = element.internal_value.name
                # Normal case
                else:
                    value = str(element.internal_value)
                doc = doc +  "\"{}\" : ".format(nodename) + "\"{}\",".format(value)

                if isInList:
                    doc = '{' + doc[0:-1] + '}' # Remove last caractere (comma) of doc String befor add }

            return doc

        rootElement=''

        # Recursively go through the object to encode it (a composite is a list of list)
        if type(body) is not list:
            body = [body]

        rootElement = rootElement + '{'
        for element in body:
            rootElement = rootElement + _encode_internal(element, False)
        rootElement = rootElement[0:-1] + '}' # Remove last caractere (comma) of doc String befor add }

        return rootElement
