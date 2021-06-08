from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()

setup(
    name='struc',  # Required

    version='0.0.1',  # Required

    author='cnvox',  # Optional

    packages=find_packages(where='.'),

    python_requires='>=3.8, <4',

    install_requires=[
        "atomicwrites==1.4.0",
        "attrs==21.2.0",
        "colorama==0.4.4",
        "iniconfig==1.1.1",
        "packaging==20.9",
        "pluggy==0.13.1",
        "py==1.10.0",
        "pyparsing==2.4.7",
        "pytest==6.2.4",
        "toml==0.10.2",
        "typed-ast==1.4.3",
        "typing-extensions==3.10.0.0",

    ]
)