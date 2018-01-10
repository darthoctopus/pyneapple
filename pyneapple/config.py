import configparser, os

p = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'defaults.cfg')

defaultp = configparser.ConfigParser()
configp = configparser.ConfigParser()
defaultp.read_file(open(p))
default = defaultp['Pyneapple']
try:
	configp.read(['pyneapplerc', os.path.expanduser('~/.pyneapplerc'), os.path.expanduser('~/.config/pyneapple/pyneapplerc')])
	config2 = configp['Pyneapple']

	def config(key, fallback=None):
		return config2.get(key, default.get(key, fallback))

except:
	def config(key, fallback=None):
		return default.get(key, fallback)