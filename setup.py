from setuptools import setup, find_packages
setup(
    name="pyneapple",
    version="0.3",
    packages=find_packages(),
    scripts=['scripts/pyneapple'],

    install_requires=['notebook>=5.1', 'setproctitle'],

    package_data={
        'pyneapple': ['data/*', 'custom/*', 'custom/*/*'],
    },

    data_files=[
        ('share/applications', ['extras/pyneapple.desktop'])],

    # metadata for upload to PyPI
    author="Joel Ong",
    author_email="joel.ong@yale.edu",
    description="GTK3 Editor for Jupyter Notebooks",
    long_description='''Pyneapple is a GTK3-based editor for Jupyter notebooks,
    intended to improve quality of life for GUI use on the desktop
    (as opposed to browser-based use).''',
    license="GPLv3",
    keywords="jupyter notebook GTK",
    url="http://gitlab.com/darthoctopus/pyneapple"
)
