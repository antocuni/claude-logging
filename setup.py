#!/usr/bin/env python3
from setuptools import setup, Extension
import os
import sys

# Force abi3 wheel
if 'bdist_wheel' in sys.argv:
    os.environ['FORCE_ABI3'] = '1'

# Define the extension module with py_limited_api=True
extension = Extension(
    'claude_logging.pytermdump',
    sources=['claude_logging/pytermdump.c'],
    extra_compile_args=['-Wall'],
    py_limited_api=True,
    define_macros=[('Py_LIMITED_API', '0x03080000')],
)

# This file helps with cibuildwheel and the stable ABI
if __name__ == "__main__":
    setup(
        ext_modules=[extension],
    )