#!/usr/bin/env python3

import sys
from pyneapple import Pyneapple

if __name__ == '__main__':
	__spec__ = None #strange Windows workaround
    p = Pyneapple()
    p.run(sys.argv)