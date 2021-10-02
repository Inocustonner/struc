from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()

setup(
    name='struc',  # Required

    version='0.1.1',  # Required

    author='cnvox',  # Optional

    packages=find_packages(where='.'),

    python_requires='>=3.8, <4',

    install_requires=[]
)