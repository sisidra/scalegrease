import json
from unittest import TestCase
from scalegrease.error import Error

import scalegrease.runner


class TestInvalidRunner(TestCase):

    def test_runner_not_found(self):
        conf = json.loads("{\"runners\":[]}")
        self.assertRaises(Error, scalegrease.runner.run, "not_found", "mock:artifact", [], conf)
