from setuptools import setup, find_packages
setup(
    name="pyneapple",
    version="0.1",
    packages=find_packages(),
    scripts=['scripts/pyneapple'],

    # Project uses reStructuredText, so ensure that the docutils get
    # installed or upgraded on the target machine
    install_requires=['notebook>=5.1'],

    package_data={
        # If any package contains *.txt or *.rst files, include them:
        'pyneapple': ['*.cfg', '*.ui', 'custom/*', 'custom/*/*'],
    },

    shortcuts=['extras/pyneapple.desktop'],

    # metadata for upload to PyPI
    author="Joel Ong",
    author_email="joel.ong@yale.edu",
    description="GTK Editor for Jupyter Notebooks",
    license="GPLv3",
    keywords="jupyter notebook GTK",
    url="http://github.com/darthoctopus/pyneapple"
)
