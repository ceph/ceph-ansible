# Copyright 2015, Rackspace US, Inc.
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

import os
import sys

from distutils.version import LooseVersion
from ansible import __version__ as __ansible_version__

# This appends the sys path with the file path which is used for the
#  import of the specific verion of the config_template action plugin
#  needed based on the ansible version calling the plugin.
sys.path.append(os.path.dirname(__file__))

if LooseVersion(__ansible_version__) < LooseVersion("2.0"):
    from _v1_config_template import *
else:
    from _v2_config_template import *
