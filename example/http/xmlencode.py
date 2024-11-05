#! /bin/python3

import sys
sys.path.append('../../src/')
import time

from malpy.mo import mal, mc
from malpy.encoding import xml

e = xml.XMLEncoder()

current_time = time.time()
print("TEST: Time Attribute:", current_time)
em = e.encode_body(mal.Time(current_time))
print(em.decode('utf8'))
print(e.decode_body(em, mal.Time).internal_value)

print("TEST: Null Time Attribute")
em = e.encode_body(mal.Time(None))
print(em.decode('utf8'))
print(e.decode_body(em, mal.Time).internal_value)


print("TEST: TimeList")
em = e.encode_body(mal.TimeList([time.time(), time.time()+5, time.time()+6]))
print(em.decode('utf8'))
emm = e.decode_body(em, mal.TimeList)
print(emm)
print([x.internal_value for x in emm.internal_value])

print("TEST: Enum")
em = e.encode_body([mal.InteractionType(mal.InteractionTypeEnum.SEND)])
print(em.decode('utf8'))
emm = e.decode_body(em, mal.InteractionType)
print(emm.internal_value)


print("TEST: Simple Composite")
em = e.encode_body([mal.IdBooleanPair([mal.Identifier("TOTO"), False])])
print(em.decode('utf8'))
emm = e.decode_body(em, mal.IdBooleanPair)
print(emm)
print(emm.internal_value)

p= mc.ParameterValueData([mc.ValidityState(mc.ValidityStateEnum.VALID), mal.Blob(b'toto'), mal.String("Toto")])

print("mllml", p._internal_value[2]._isNull)

coded  = e.encode_body([p])
print(coded.decode('utf8'))
decoded = e.decode_body(coded, mc.ParameterValueData)
print(decoded)
print([x.internal_value for x in decoded.internal_value])
print(e.encode_body(decoded).decode('utf8'))

m = mal.Subscription([
        "MySubscription",
        ['fr', 'cnes', None],
        None,
        [
            ['key1', [mal.Integer(1),mal.Integer(2),mal.Integer(3)]],
            ['key2', [mal.Boolean(True), mal.Boolean(False)]]
        ]
    ])

u = mal.UpdateHeader(
    [
        "CNES",
        ['fr', 'cnes', 'swot'],
        [
            [mal.Boolean(True)],
            [mal.Boolean(None)],
            [mal.Float(2.3)]
        ]
    ])
em = e.encode_body([m])
print(em.decode('utf-8'))
print(e.decode_body(em, mal.Subscription))
print("{}".format(em.decode('utf-8')))
eu = e.encode_body([u])
print(e.decode_body(eu))
print("{}".format(eu.decode('utf-8')))
eul = e.encode_body([u,u])
deul = e.decode_body(eul)
print(eul.decode('utf8'))
print(deul)