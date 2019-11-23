#! /bin/python

import sys
sys.path.append('../../src')

import mal
import encoding

m = mal.Subscription(["MySubscription", [[['Id1','Id2', None],True, True, True, True, [["IDK1",9,None,None]]]]])

a = m.copy()
b = mal.Subscription(a)
e = encoding.XMLEncoder()

em = e.encode(m)
print(em.decode('utf-8'))
print(e.decode(em))
