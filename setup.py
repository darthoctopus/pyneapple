from setuptools import setup, find_packages
setup(
    name="pyneapple",
    version="0.1",
    packages=find_packages(),
    scripts=['scripts/pyneapple'],

    install_requires=['notebook>=5.1'],

    package_data={
        'pyneapple': ['*.cfg', '*.ui', 'custom/*', 'custom/*/*'],
    },

    data_files = [
        ('share/applications', ['extras/pyneapple.desktop'])],

    # metadata for upload to PyPI
    author="Joel Ong",
    author_email="joel.ong@yale.edu",
    description="GTK Editor for Jupyter Notebooks",
    license="GPLv3",
    keywords="jupyter notebook GTK",
    url="http://github.com/darthoctopus/pyneapple"
)
