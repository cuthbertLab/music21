"""
Module with tests for the serve post-processor
"""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from nose import SkipTest
from ...tests.base import TestsBase


class TestServe(TestsBase):
    """Contains test functions for serve.py"""


    def test_constructor(self):
        """Can a ServePostProcessor be constructed?"""
        try:
            from ..serve import ServePostProcessor
        except ImportError:
            raise SkipTest("Serve post-processor test requires tornado")
        ServePostProcessor()
