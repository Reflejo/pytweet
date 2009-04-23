# Copyright 2009 Atommica. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
The setup and build script for the pytweet library.
"""

from setuptools import setup

setup(
    name = "pytweet",
    version = "0.1b",
    url = 'http://code.google.com/p/pytweet/',
    license = 'Apache License 2.0',
    description='A python wrapper around the Twitter API',
    author = 'Martin Conte Mac Donell',
    author_email = 'Reflejo@gmail.com',
    packages = ['pytweet'],
    install_requires = ['setuptools', 'simplejson'],
    include_package_data = True,
    classifiers = [
      'Development Status :: 4 - Beta',
      'Intended Audience :: Developers',
      'License :: OSI Approved :: Apache Software License',
      'Topic :: Software Development :: Libraries :: Python Modules',
      'Topic :: Communications :: Chat',
      'Topic :: Internet',
    ],
)
