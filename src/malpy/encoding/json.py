
from malpy.mo import mal
from malpy.malpydefinitions import MALPY_ENCODING

from .abstract_encoding import Encoder

class JSONEncoder(Encoder):
    encoding = MALPY_ENCODING.JSON

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