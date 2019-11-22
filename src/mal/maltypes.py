from enum import IntEnum
from abc import ABC

name = "MAL"
number = 1
version = 1

class MAL_SHORTFORMS(IntEnum):
    BLOB = 1
    BOOLEAN = 2
    DURATION = 3
    FLOAT = 4
    DOUBLE = 5
    IDENTIFIER = 6
    OCTET = 7
    UOCTET = 8
    SHORT = 9
    USHORT = 10
    INTEGER = 11
    UINTEGER = 12
    LONG = 13
    ULONG = 14
    STRING = 15
    TIME = 16
    FINETIME = 17
    URI = 18

class Element(ABC):
    """Element is the base type of all data constructs. All types that make up the MAL data model are derived from it."""

    shortform = None


class Attribute(Element):
    """Attribute is the base type of all attributes of the MAL data model. Attributes are contained within Composites and are used to build complex structures that make the data model."""

    shortform = None

    def __init__(self, value):
        if type(value) == type(self):
            self._value = value.value
        elif type(value) == type(self).value_type:
            self._value = value
        else:
            raise TypeError("Expected {}, got {}.".format(type(self).value_type, type(value)))

    @property
    def value(self):
        return self._value


class Composite(Element):
    """Composite is the base structure for composite structures that contain a set of elements."""

    shortform = None


class Blob(Attribute):
    """The Blob structure is used to store binary object attributes. It is a variable-length, unbounded, octet array. The distinction between this type and a list of Octet attributes is that this type may allow language mappings and encodings to use more efficient or appropriate representations."""

    shortform = MAL_SHORTFORMS.BLOB
    value_type = bytes


class Boolean(Attribute):
    """The Boolean structure is used to store Boolean attributes. Possible values are 'True' or 'False'."""

    shortform = MAL_SHORTFORMS.BOOLEAN
    value_type = bool


class Duration(Attribute):
    """The Duration structure is used to store Duration attributes. It represents a length of time in seconds. It may contain a fractional component."""

    shortform = MAL_SHORTFORMS.DURATION
    value_type = float


class Float(Attribute):
    """The Float structure is used to store floating point attributes using the IEEE 754 32-bit range.
Three special values exist for this type: POSITIVE_INFINITY, NEGATIVE_INFINITY, and NaN (Not A Number)."""

    shortform = MAL_SHORTFORMS.FLOAT
    value_type = float


class Double(Attribute):
    """The Double structure is used to store floating point attributes using the IEEE 754 64-bit range.
Three special values exist for this type: POSITIVE_INFINITY, NEGATIVE_INFINITY, and NaN (Not A Number)."""

    shortform = MAL_SHORTFORMS.DOUBLE
    value_type = float


class Identifier(Attribute):
    """The Identifier structure is used to store an identifier and can be used for indexing. It is a variable-length, unbounded, Unicode string."""

    shortform = MAL_SHORTFORMS.IDENTIFIER
    value_type = str


class Octet(Attribute):
    """The Octet structure is used to store 8-bit signed attributes. The permitted range is -128 to 127."""

    shortform = MAL_SHORTFORMS.OCTET
    value_type = int

    def __init__(self, value):
        super().__init__(value)
        if type(value) == int and ( value < -128 or value > 127 ):
            raise ValueError("Authorized value is between -128 and 127.")


class UOctet(Attribute):
    """The UOctet structure is used to store 8-bit unsigned attributes. The permitted range is 0 to 255."""

    shortform = MAL_SHORTFORMS.UOCTET
    value_type = int

    def __init__(self, value):
        super().__init__(value)
        if type(value) == int and ( value < 0 or value > 255 ):
            raise ValueError("Authorized value is between 0 and 255.")


class Short(Attribute):
    """The Short structure is used to store 16-bit signed attributes. The permitted range is -32768 to 32767."""

    shortform = MAL_SHORTFORMS.SHORT
    value_type = int

    def __init__(self, value):
        super().__init__(value)
        if type(value) == int and ( value < -32768 or value > 32767 ):
            raise ValueError("Authorized value is between -32768 and 32767.")


class UShort(Attribute):
    """The UShort structure is used to store 16-bit unsigned attributes. The permitted range is 0 to 65535."""

    shortform = MAL_SHORTFORMS.USHORT
    value_type = int

    def __init__(self, value):
        super().__init__(value)
        if type(value) == int and ( value < 0 or value > 65535 ):
            raise ValueError("Authorized value is between 0 and 65535.")


class Integer(Attribute):
    """The Integer structure is used to store 32-bit signed attributes. The permitted range is -2147483648 to 2147483647."""

    shortform = MAL_SHORTFORMS.INTEGER
    value_type = int

    def __init__(self, value):
        super().__init__(value)
        if type(value) == int and ( value < -2147483648 or value > 21474836487 ):
            raise ValueError("Authorized value is between -2147483648 and 21474836487.")


class UInteger(Attribute):
    """The UInteger structure is used to store 32-bit unsigned attributes. The permitted range is 0 to 4294967295."""

    shortform = MAL_SHORTFORMS.UINTEGER
    value_type = int

    def __init__(self, value):
        super().__init__(value)
        if type(value) == int and ( value < 0 or value > 4294967295 ):
            raise ValueError("Authorized value is between 0 and 4294967295.")


class Long(Attribute):
    """The Long structure is used to store 64-bit signed attributes. The permitted range is -9223372036854775808 to 9223372036854775807."""

    shortform = MAL_SHORTFORMS.LONG
    value_type = int

    def __init__(self, value):
        super().__init__(value)
        if type(value) == int and ( value < -9223372036854775808 or value > 9223372036854775807 ):
            raise ValueError("Authorized value is between -9223372036854775808 and 9223372036854775807.")


class ULong(Attribute):
    """The ULong structure is used to store 64-bit unsigned attributes. The permitted range is 0 to 18446744073709551615."""

    shortform = MAL_SHORTFORMS.ULONG
    value_type = int

    def __init__(self, value):
        super().__init__(value)
        if type(value) == int and ( value < 0 or value > 18446744073709551615 ):
            raise ValueError("Authorized value is between 0 and 18446744073709551615.")


class String(Attribute):
    """The String structure is used to store String attributes. It is a variable-length, unbounded, Unicode string."""

    shortform = MAL_SHORTFORMS.STRING
    value_type = str


class Time(Attribute):
    """The Time structure is used to store absolute time attributes. It represents an absolute date and time to millisecond resolution."""

    shortform = MAL_SHORTFORMS.TIME
    value_type = float


class FineTime(Attribute):
    """The FineTime structure is used to store high-resolution absolute time attributes. It represents an absolute date and time to picosecond resolution."""

    shortform = MAL_SHORTFORMS.FINETIME
    value_type = float


class URI(Attribute):
    """The URI structure is used to store URI addresses. It is a variable-length, unbounded, Unicode string."""

    shortform = MAL_SHORTFORMS.URI
    value_type = str


