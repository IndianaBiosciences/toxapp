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
