# SPDX-FileCopyrightText: 2025 Olivier Churlaud <olivier@churlaud.com>
# SPDX-FileCopyrightText: 2025 CNES
#
# SPDX-License-Identifier: MIT

#####################################################
# Generated by generators/generator.py              #
# This file is generated. Do NOT edit it by hand.   #
#####################################################

"""The parameter service allows the user to subscribe to parameter value report and optionally be able to set new values. A single PUBSUB operation is provided for monitoring and publishing of parameter values.
A parameter value also contains a calculation of the validity of the parameter, the flow chart for this calculation is provided in Figure 3-3:
 validity calculation flow chart 

This standard supports the concept of non-standard invalidity states but the meaning and calculation of these is outside the scope of this standard.
The generation of value reports can be controlled using the enableGeneration operation, which supports the use of groups. Groups must reference parameter identities or groups of parameter identities only.
The parameter service does not include any value checking, this is delegated to the check service.
Parameter definitions are maintained using the operations defined in this service but storage of definitions is delegated to the COM archive."""

from enum import IntEnum
from malpy.mo import mal
from malpy.mo import com
from malpy.mo import mc

number = 2

# CapabilitySet 1
class MonitorValue(mal.PubSubProviderHandler):
    AREA = 4
    VERSION = 1
    SERVICE = 2
    OPERATION = 1



# CapabilitySet 2
class GetValue(mal.RequestProviderHandler):
    AREA = 4
    VERSION = 1
    SERVICE = 2
    OPERATION = 2



# CapabilitySet 3
class SetValue(mal.SubmitProviderHandler):
    AREA = 4
    VERSION = 1
    SERVICE = 2
    OPERATION = 3



# CapabilitySet 4
class EnableGeneration(mal.RequestProviderHandler):
    AREA = 4
    VERSION = 1
    SERVICE = 2
    OPERATION = 4



# CapabilitySet 5
class ListDefinition(mal.RequestProviderHandler):
    AREA = 4
    VERSION = 1
    SERVICE = 2
    OPERATION = 5



# CapabilitySet 6
class AddParameter(mal.RequestProviderHandler):
    AREA = 4
    VERSION = 1
    SERVICE = 2
    OPERATION = 6


class UpdateDefinition(mal.RequestProviderHandler):
    AREA = 4
    VERSION = 1
    SERVICE = 2
    OPERATION = 7


class RemoveParameter(mal.SubmitProviderHandler):
    AREA = 4
    VERSION = 1
    SERVICE = 2
    OPERATION = 8


class MALShortForm(IntEnum):
    VALIDITYSTATE = 4
    PARAMETERDEFINITIONDETAILS = 1
    PARAMETERVALUE = 2
    PARAMETERCONVERSION = 3
    PARAMETERCREATIONREQUEST = 5
    PARAMETERRAWVALUE = 6
    PARAMETERVALUEDETAILS = 7


class ValidityStateEnum(IntEnum):
    """Convenience enumeration that holds the validity states and their numeric values."""

    VALID = 0  # Valid.
    EXPIRED = 1  # The parameter has a timeout associated which has expired
    INVALID_RAW = 2  # The parameter raw value cannot be obtained, or calculated for synthetic parameters
    INVALID_CONVERSION = 3  # The validity expression either has evaluated to TRUE or there is no validity defined, but the conversion of the parameter value has failed (for example an unexpected value for a discrete conversion)
    UNVERIFIED = 4  # The validity of the validity expression has been evaluated to FALSE and therefore cannot be used to verify the current value
    INVALID = 5  # The validity expression has been evaluated to FALSE


class ValidityState(mal.AbstractEnum):
    """Convenience enumeration that holds the validity states and their numeric values."""

    shortForm = MALShortForm.VALIDITYSTATE
    value_type = ValidityStateEnum


class ValidityStateList(mal.ElementList):
    shortForm = -MALShortForm.VALIDITYSTATE

    def __init__(self, value=None, canBeNull=True, attribName=None):
        super().__init__(value, canBeNull, attribName)
        self._internal_value = []
        if type(value) == type(self):
            if value.internal_value is None:
                if self._canBeNull:
                    self._isNull = True
                else:
                    raise ValueError("This {} cannot be Null".format(type(self)))
            else:
                self._internal_value = value.copy().internal_value
        else:
            listvalue = value if type(value) == list else [value]
            for v in listvalue:
                 self._internal_value.append(ValidityState(v))


class ParameterDefinitionDetails(mal.Composite):
    """The ParameterDefinitionDetails structure holds a parameter definition. The conversion field defines the conditions where the relevant conversion is applied. For onboard parameters, the report interval should be a multiple of the minimum sampling interval of that parameter."""

    shortForm = MALShortForm.PARAMETERDEFINITIONDETAILS
    _fieldNumber = mal.Composite._fieldNumber + 7

    def __init__(self, value=None, canBeNull=True, attribName=None):
        super().__init__(value, canBeNull, attribName)
        self._internal_value += [None]*7
        if value is None and self._canBeNull:
            self._isNull = True
        elif type(value) == type(self):
            if value.internal_value is None:
                if self._canBeNull:
                    self._isNull = True
                else:
                    raise ValueError("This {} cannot be Null".format(type(self)))
            else:
                self._internal_value = value.copy().internal_value
        else:
            self.description = value[mal.Composite._fieldNumber + 0]
            self.rawType = value[mal.Composite._fieldNumber + 1]
            self.rawUnit = value[mal.Composite._fieldNumber + 2]
            self.generationEnabled = value[mal.Composite._fieldNumber + 3]
            self.reportInterval = value[mal.Composite._fieldNumber + 4]
            self.validityExpression = value[mal.Composite._fieldNumber + 5]
            self.conversion = value[mal.Composite._fieldNumber + 6]

    @property
    def description(self):
        return self._internal_value[mal.Composite._fieldNumber + 0]

    @description.setter
    def description(self, description):
        self._internal_value[mal.Composite._fieldNumber + 0] = mal.String(description, canBeNull=False, attribName='description')
        self._isNull = False

    @property
    def rawType(self):
        return self._internal_value[mal.Composite._fieldNumber + 1]

    @rawType.setter
    def rawType(self, rawType):
        self._internal_value[mal.Composite._fieldNumber + 1] = mal.Octet(rawType, canBeNull=False, attribName='rawType')
        self._isNull = False

    @property
    def rawUnit(self):
        return self._internal_value[mal.Composite._fieldNumber + 2]

    @rawUnit.setter
    def rawUnit(self, rawUnit):
        self._internal_value[mal.Composite._fieldNumber + 2] = mal.String(rawUnit, canBeNull=True, attribName='rawUnit')
        self._isNull = False

    @property
    def generationEnabled(self):
        return self._internal_value[mal.Composite._fieldNumber + 3]

    @generationEnabled.setter
    def generationEnabled(self, generationEnabled):
        self._internal_value[mal.Composite._fieldNumber + 3] = mal.Boolean(generationEnabled, canBeNull=False, attribName='generationEnabled')
        self._isNull = False

    @property
    def reportInterval(self):
        return self._internal_value[mal.Composite._fieldNumber + 4]

    @reportInterval.setter
    def reportInterval(self, reportInterval):
        self._internal_value[mal.Composite._fieldNumber + 4] = mal.Duration(reportInterval, canBeNull=False, attribName='reportInterval')
        self._isNull = False

    @property
    def validityExpression(self):
        return self._internal_value[mal.Composite._fieldNumber + 5]

    @validityExpression.setter
    def validityExpression(self, validityExpression):
        self._internal_value[mal.Composite._fieldNumber + 5] = mc.ParameterExpression(validityExpression, canBeNull=True, attribName='validityExpression')
        self._isNull = False

    @property
    def conversion(self):
        return self._internal_value[mal.Composite._fieldNumber + 6]

    @conversion.setter
    def conversion(self, conversion):
        self._internal_value[mal.Composite._fieldNumber + 6] = ParameterConversion(conversion, canBeNull=True, attribName='conversion')
        self._isNull = False


class ParameterDefinitionDetailsList(mal.ElementList):
    shortForm = -MALShortForm.PARAMETERDEFINITIONDETAILS

    def __init__(self, value=None, canBeNull=True, attribName=None):
        super().__init__(value, canBeNull, attribName)
        self._internal_value = []
        if type(value) == type(self):
            if value.internal_value is None:
                if self._canBeNull:
                    self._isNull = True
                else:
                    raise ValueError("This {} cannot be Null".format(type(self)))
            else:
                self._internal_value = value.copy().internal_value
        else:
            listvalue = value if type(value) == list else [value]
            for v in listvalue:
                 self._internal_value.append(ParameterDefinitionDetails(v))


class ParameterValue(mal.Composite):
    """This structure holds a specific value of the parameter. The type of the value shall match that specified in the parameter definition."""

    shortForm = MALShortForm.PARAMETERVALUE
    _fieldNumber = mal.Composite._fieldNumber + 3

    def __init__(self, value=None, canBeNull=True, attribName=None):
        super().__init__(value, canBeNull, attribName)
        self._internal_value += [None]*3
        if value is None and self._canBeNull:
            self._isNull = True
        elif type(value) == type(self):
            if value.internal_value is None:
                if self._canBeNull:
                    self._isNull = True
                else:
                    raise ValueError("This {} cannot be Null".format(type(self)))
            else:
                self._internal_value = value.copy().internal_value
        else:
            self.validityState = value[mal.Composite._fieldNumber + 0]
            self.rawValue = value[mal.Composite._fieldNumber + 1]
            self.convertedValue = value[mal.Composite._fieldNumber + 2]

    @property
    def validityState(self):
        return self._internal_value[mal.Composite._fieldNumber + 0]

    @validityState.setter
    def validityState(self, validityState):
        self._internal_value[mal.Composite._fieldNumber + 0] = mal.UOctet(validityState, canBeNull=False, attribName='validityState')
        self._isNull = False

    @property
    def rawValue(self):
        return self._internal_value[mal.Composite._fieldNumber + 1]

    @rawValue.setter
    def rawValue(self, rawValue):
        if rawValue is None:
            self._internal_value[mal.Composite._fieldNumber + 1] = mal.Attribute(rawValue, canBeNull=True, attribName='rawValue')
        else:
            self._internal_value[mal.Composite._fieldNumber + 1] = type(rawValue)(rawValue, canBeNull=True, attribName='rawValue')
        self._isNull = False

    @property
    def convertedValue(self):
        return self._internal_value[mal.Composite._fieldNumber + 2]

    @convertedValue.setter
    def convertedValue(self, convertedValue):
        if convertedValue is None:
            self._internal_value[mal.Composite._fieldNumber + 2] = mal.Attribute(convertedValue, canBeNull=True, attribName='convertedValue')
        else:
            self._internal_value[mal.Composite._fieldNumber + 2] = type(convertedValue)(convertedValue, canBeNull=True, attribName='convertedValue')
        self._isNull = False


class ParameterValueList(mal.ElementList):
    shortForm = -MALShortForm.PARAMETERVALUE

    def __init__(self, value=None, canBeNull=True, attribName=None):
        super().__init__(value, canBeNull, attribName)
        self._internal_value = []
        if type(value) == type(self):
            if value.internal_value is None:
                if self._canBeNull:
                    self._isNull = True
                else:
                    raise ValueError("This {} cannot be Null".format(type(self)))
            else:
                self._internal_value = value.copy().internal_value
        else:
            listvalue = value if type(value) == list else [value]
            for v in listvalue:
                 self._internal_value.append(ParameterValue(v))


class ParameterConversion(mal.Composite):
    """The ParameterConversion structure holds information about the conversions to be applied to a parameter."""

    shortForm = MALShortForm.PARAMETERCONVERSION
    _fieldNumber = mal.Composite._fieldNumber + 3

    def __init__(self, value=None, canBeNull=True, attribName=None):
        super().__init__(value, canBeNull, attribName)
        self._internal_value += [None]*3
        if value is None and self._canBeNull:
            self._isNull = True
        elif type(value) == type(self):
            if value.internal_value is None:
                if self._canBeNull:
                    self._isNull = True
                else:
                    raise ValueError("This {} cannot be Null".format(type(self)))
            else:
                self._internal_value = value.copy().internal_value
        else:
            self.convertedType = value[mal.Composite._fieldNumber + 0]
            self.convertedUnit = value[mal.Composite._fieldNumber + 1]
            self.conditionalConversions = value[mal.Composite._fieldNumber + 2]

    @property
    def convertedType(self):
        return self._internal_value[mal.Composite._fieldNumber + 0]

    @convertedType.setter
    def convertedType(self, convertedType):
        self._internal_value[mal.Composite._fieldNumber + 0] = mal.Octet(convertedType, canBeNull=False, attribName='convertedType')
        self._isNull = False

    @property
    def convertedUnit(self):
        return self._internal_value[mal.Composite._fieldNumber + 1]

    @convertedUnit.setter
    def convertedUnit(self, convertedUnit):
        self._internal_value[mal.Composite._fieldNumber + 1] = mal.String(convertedUnit, canBeNull=True, attribName='convertedUnit')
        self._isNull = False

    @property
    def conditionalConversions(self):
        return self._internal_value[mal.Composite._fieldNumber + 2]

    @conditionalConversions.setter
    def conditionalConversions(self, conditionalConversions):
        self._internal_value[mal.Composite._fieldNumber + 2] = mc.ConditionalConversionList(conditionalConversions, canBeNull=False, attribName='conditionalConversions')
        self._isNull = False


class ParameterConversionList(mal.ElementList):
    shortForm = -MALShortForm.PARAMETERCONVERSION

    def __init__(self, value=None, canBeNull=True, attribName=None):
        super().__init__(value, canBeNull, attribName)
        self._internal_value = []
        if type(value) == type(self):
            if value.internal_value is None:
                if self._canBeNull:
                    self._isNull = True
                else:
                    raise ValueError("This {} cannot be Null".format(type(self)))
            else:
                self._internal_value = value.copy().internal_value
        else:
            listvalue = value if type(value) == list else [value]
            for v in listvalue:
                 self._internal_value.append(ParameterConversion(v))


class ParameterCreationRequest(mal.Composite):
    """The ParameterCreationRequest contains all the fields required when creating a new parameter in a provider."""

    shortForm = MALShortForm.PARAMETERCREATIONREQUEST
    _fieldNumber = mal.Composite._fieldNumber + 2

    def __init__(self, value=None, canBeNull=True, attribName=None):
        super().__init__(value, canBeNull, attribName)
        self._internal_value += [None]*2
        if value is None and self._canBeNull:
            self._isNull = True
        elif type(value) == type(self):
            if value.internal_value is None:
                if self._canBeNull:
                    self._isNull = True
                else:
                    raise ValueError("This {} cannot be Null".format(type(self)))
            else:
                self._internal_value = value.copy().internal_value
        else:
            self.name = value[mal.Composite._fieldNumber + 0]
            self.paramDefDetails = value[mal.Composite._fieldNumber + 1]

    @property
    def name(self):
        return self._internal_value[mal.Composite._fieldNumber + 0]

    @name.setter
    def name(self, name):
        self._internal_value[mal.Composite._fieldNumber + 0] = mal.Identifier(name, canBeNull=False, attribName='name')
        self._isNull = False

    @property
    def paramDefDetails(self):
        return self._internal_value[mal.Composite._fieldNumber + 1]

    @paramDefDetails.setter
    def paramDefDetails(self, paramDefDetails):
        self._internal_value[mal.Composite._fieldNumber + 1] = ParameterDefinitionDetails(paramDefDetails, canBeNull=False, attribName='paramDefDetails')
        self._isNull = False


class ParameterCreationRequestList(mal.ElementList):
    shortForm = -MALShortForm.PARAMETERCREATIONREQUEST

    def __init__(self, value=None, canBeNull=True, attribName=None):
        super().__init__(value, canBeNull, attribName)
        self._internal_value = []
        if type(value) == type(self):
            if value.internal_value is None:
                if self._canBeNull:
                    self._isNull = True
                else:
                    raise ValueError("This {} cannot be Null".format(type(self)))
            else:
                self._internal_value = value.copy().internal_value
        else:
            listvalue = value if type(value) == list else [value]
            for v in listvalue:
                 self._internal_value.append(ParameterCreationRequest(v))


class ParameterRawValue(mal.Composite):
    """The ParameterRawValue structure holds a new raw value for a specific parameter."""

    shortForm = MALShortForm.PARAMETERRAWVALUE
    _fieldNumber = mal.Composite._fieldNumber + 2

    def __init__(self, value=None, canBeNull=True, attribName=None):
        super().__init__(value, canBeNull, attribName)
        self._internal_value += [None]*2
        if value is None and self._canBeNull:
            self._isNull = True
        elif type(value) == type(self):
            if value.internal_value is None:
                if self._canBeNull:
                    self._isNull = True
                else:
                    raise ValueError("This {} cannot be Null".format(type(self)))
            else:
                self._internal_value = value.copy().internal_value
        else:
            self.paramInstId = value[mal.Composite._fieldNumber + 0]
            self.rawValue = value[mal.Composite._fieldNumber + 1]

    @property
    def paramInstId(self):
        return self._internal_value[mal.Composite._fieldNumber + 0]

    @paramInstId.setter
    def paramInstId(self, paramInstId):
        self._internal_value[mal.Composite._fieldNumber + 0] = mal.Long(paramInstId, canBeNull=False, attribName='paramInstId')
        self._isNull = False

    @property
    def rawValue(self):
        return self._internal_value[mal.Composite._fieldNumber + 1]

    @rawValue.setter
    def rawValue(self, rawValue):
        if rawValue is None:
            self._internal_value[mal.Composite._fieldNumber + 1] = mal.Attribute(rawValue, canBeNull=True, attribName='rawValue')
        else:
            self._internal_value[mal.Composite._fieldNumber + 1] = type(rawValue)(rawValue, canBeNull=True, attribName='rawValue')
        self._isNull = False


class ParameterRawValueList(mal.ElementList):
    shortForm = -MALShortForm.PARAMETERRAWVALUE

    def __init__(self, value=None, canBeNull=True, attribName=None):
        super().__init__(value, canBeNull, attribName)
        self._internal_value = []
        if type(value) == type(self):
            if value.internal_value is None:
                if self._canBeNull:
                    self._isNull = True
                else:
                    raise ValueError("This {} cannot be Null".format(type(self)))
            else:
                self._internal_value = value.copy().internal_value
        else:
            listvalue = value if type(value) == list else [value]
            for v in listvalue:
                 self._internal_value.append(ParameterRawValue(v))


class ParameterValueDetails(mal.Composite):
    """This structure holds a specific time stamped value of the parameter. The type of the value shall match that specified in the parameter definition."""

    shortForm = MALShortForm.PARAMETERVALUEDETAILS
    _fieldNumber = mal.Composite._fieldNumber + 4

    def __init__(self, value=None, canBeNull=True, attribName=None):
        super().__init__(value, canBeNull, attribName)
        self._internal_value += [None]*4
        if value is None and self._canBeNull:
            self._isNull = True
        elif type(value) == type(self):
            if value.internal_value is None:
                if self._canBeNull:
                    self._isNull = True
                else:
                    raise ValueError("This {} cannot be Null".format(type(self)))
            else:
                self._internal_value = value.copy().internal_value
        else:
            self.paramId = value[mal.Composite._fieldNumber + 0]
            self.defId = value[mal.Composite._fieldNumber + 1]
            self.timestamp = value[mal.Composite._fieldNumber + 2]
            self.value = value[mal.Composite._fieldNumber + 3]

    @property
    def paramId(self):
        return self._internal_value[mal.Composite._fieldNumber + 0]

    @paramId.setter
    def paramId(self, paramId):
        self._internal_value[mal.Composite._fieldNumber + 0] = mal.Long(paramId, canBeNull=False, attribName='paramId')
        self._isNull = False

    @property
    def defId(self):
        return self._internal_value[mal.Composite._fieldNumber + 1]

    @defId.setter
    def defId(self, defId):
        self._internal_value[mal.Composite._fieldNumber + 1] = mal.Long(defId, canBeNull=False, attribName='defId')
        self._isNull = False

    @property
    def timestamp(self):
        return self._internal_value[mal.Composite._fieldNumber + 2]

    @timestamp.setter
    def timestamp(self, timestamp):
        self._internal_value[mal.Composite._fieldNumber + 2] = mal.Time(timestamp, canBeNull=False, attribName='timestamp')
        self._isNull = False

    @property
    def value(self):
        return self._internal_value[mal.Composite._fieldNumber + 3]

    @value.setter
    def value(self, value):
        self._internal_value[mal.Composite._fieldNumber + 3] = ParameterValue(value, canBeNull=False, attribName='value')
        self._isNull = False


class ParameterValueDetailsList(mal.ElementList):
    shortForm = -MALShortForm.PARAMETERVALUEDETAILS

    def __init__(self, value=None, canBeNull=True, attribName=None):
        super().__init__(value, canBeNull, attribName)
        self._internal_value = []
        if type(value) == type(self):
            if value.internal_value is None:
                if self._canBeNull:
                    self._isNull = True
                else:
                    raise ValueError("This {} cannot be Null".format(type(self)))
            else:
                self._internal_value = value.copy().internal_value
        else:
            listvalue = value if type(value) == list else [value]
            for v in listvalue:
                 self._internal_value.append(ParameterValueDetails(v))


