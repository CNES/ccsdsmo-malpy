#! /bin/python

import sys
sys.path.append('../../src')

from mo import mal
import encoding

m = mal.Subscription(
    ["MySubscription",
        [
            [
                ['Id1', 'Id2', None],
                True,
                True,
                True,
                True,
                [
                    ["IDK1", 9, None, None],
                    None
                ]
            ]
        ]
    ]
    )

print("copy*********************")
#print(len(m))
a = m.copy()
b = mal.Subscription(a)
e = encoding.XMLEncoder()

em = e.encode_body([m])
print(em.decode('utf-8'))

decodedValue = e.decode_body(em)
print(decodedValue)
m2 = mal.Subscription(decodedValue[0])

print(e.encode_body([m2]).decode('utf-8'))
