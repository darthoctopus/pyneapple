import os
import configparser

p = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data', 'defaults.cfg')

configp = configparser.ConfigParser()
configp.read([p, 'pyneapplerc', os.path.expanduser('~/.pyneapplerc'),
              os.path.expanduser('~/.config/pyneapple/pyneapplerc')])
config = configp['Pyneapple']
