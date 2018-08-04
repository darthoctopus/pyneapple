#!/usr/bin/env python3

import sys
import setproctitle
from pyneapple import Pyneapple

if __name__ == '__main__':
    if '__spec__' not in locals():
        __spec__ = None #strange Windows workaround
    setproctitle.setproctitle('pyneapple')
    p = Pyneapple()
    p.run(sys.argv)
