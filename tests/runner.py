# Copyright 2019 Indiana Biosciences Research Institute (IBRI)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# unit test suite for toxapp
import unittest
from tests import test_computation, test_email, test_celery, test_treemap, test_r

loader = unittest.TestLoader()
suite = unittest.TestSuite()

suite.addTests(loader.loadTestsFromModule(test_computation))
suite.addTests(loader.loadTestsFromModule(test_email))
# run celery tests after test_computation, since it strings together several of the components tested there
suite.addTests(loader.loadTestsFromModule(test_celery))
suite.addTests(loader.loadTestsFromModule(test_treemap))
suite.addTests(loader.loadTestsFromModule(test_r))
runner = unittest.TextTestRunner(verbosity=3)
result = runner.run(suite)
