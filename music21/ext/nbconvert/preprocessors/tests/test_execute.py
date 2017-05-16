# coding=utf-8

"""
Module with tests for the execute preprocessor.
"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import copy
import glob
import io
import os
import re

import nbformat
import sys

from .base import PreprocessorTestsBase
from ..execute import ExecutePreprocessor, CellExecutionError, executenb

from nbconvert.filters import strip_ansi
from nose.tools import assert_raises, assert_in
from testpath import modified_env

addr_pat = re.compile(r'0x[0-9a-f]{7,9}')
current_dir = os.path.dirname(__file__)

class TestExecute(PreprocessorTestsBase):
    """Contains test functions for execute.py"""

    @staticmethod
    def normalize_output(output):
        """
        Normalizes outputs for comparison.
        """
        output = dict(output)
        if 'metadata' in output:
            del output['metadata']
        if 'text' in output:
            output['text'] = re.sub(addr_pat, '<HEXADDR>', output['text'])
        if 'text/plain' in output.get('data', {}):
            output['data']['text/plain'] = \
                re.sub(addr_pat, '<HEXADDR>', output['data']['text/plain'])
        if 'traceback' in output:
            tb = []
            for line in output['traceback']:
                tb.append(strip_ansi(line))
            output['traceback'] = tb

        return output


    def assert_notebooks_equal(self, expected, actual):
        expected_cells = expected['cells']
        actual_cells = actual['cells']
        self.assertEqual(len(expected_cells), len(actual_cells))

        for expected_cell, actual_cell in zip(expected_cells, actual_cells):
            expected_outputs = expected_cell.get('outputs', [])
            actual_outputs = actual_cell.get('outputs', [])
            normalized_expected_outputs = list(map(self.normalize_output, expected_outputs))
            normalized_actual_outputs = list(map(self.normalize_output, actual_outputs))
            self.assertEqual(normalized_expected_outputs, normalized_actual_outputs)

            expected_execution_count = expected_cell.get('execution_count', None)
            actual_execution_count = actual_cell.get('execution_count', None)
            self.assertEqual(expected_execution_count, actual_execution_count)


    def build_preprocessor(self, opts):
        """Make an instance of a preprocessor"""
        preprocessor = ExecutePreprocessor()
        preprocessor.enabled = True
        for opt in opts:
            setattr(preprocessor, opt, opts[opt])
        return preprocessor


    def test_constructor(self):
        """Can a ExecutePreprocessor be constructed?"""
        self.build_preprocessor({})


    def run_notebook(self, filename, opts, resources):
        """Loads and runs a notebook, returning both the version prior to
        running it and the version after running it.

        """
        with io.open(filename) as f:
            input_nb = nbformat.read(f, 4)

        preprocessor = self.build_preprocessor(opts)
        cleaned_input_nb = copy.deepcopy(input_nb)
        for cell in cleaned_input_nb.cells:
            if 'execution_count' in cell:
                del cell['execution_count']
            cell['outputs'] = []

        # Override terminal size to standardise traceback format
        with modified_env({'COLUMNS': '80', 'LINES': '24'}):
            output_nb, _ = preprocessor(cleaned_input_nb, resources)

        return input_nb, output_nb

    def test_run_notebooks(self):
        """Runs a series of test notebooks and compares them to their actual output"""
        input_files = glob.glob(os.path.join(current_dir, 'files', '*.ipynb'))
        for filename in input_files:
            if os.path.basename(filename) == "Disable Stdin.ipynb":
                continue
            elif os.path.basename(filename) == "Interrupt.ipynb":
                opts = dict(timeout=1, interrupt_on_timeout=True, allow_errors=True)
            elif os.path.basename(filename) == "Skip Exceptions.ipynb":
                opts = dict(allow_errors=True)
            else:
                opts = dict()
            res = self.build_resources()
            res['metadata']['path'] = os.path.dirname(filename)
            input_nb, output_nb = self.run_notebook(filename, opts, res)
            self.assert_notebooks_equal(input_nb, output_nb)

    def test_empty_path(self):
        """Can the kernel be started when the path is empty?"""
        filename = os.path.join(current_dir, 'files', 'HelloWorld.ipynb')
        res = self.build_resources()
        res['metadata']['path'] = ''
        input_nb, output_nb = self.run_notebook(filename, {}, res)
        self.assert_notebooks_equal(input_nb, output_nb)

    def test_disable_stdin(self):
        """Test disabling standard input"""
        filename = os.path.join(current_dir, 'files', 'Disable Stdin.ipynb')
        res = self.build_resources()
        res['metadata']['path'] = os.path.dirname(filename)
        input_nb, output_nb = self.run_notebook(filename, dict(allow_errors=True), res)

        # We need to special-case this particular notebook, because the
        # traceback contains machine-specific stuff like where IPython
        # is installed. It is sufficient here to just check that an error
        # was thrown, and that it was a StdinNotImplementedError
        self.assertEqual(len(output_nb['cells']), 1)
        self.assertEqual(len(output_nb['cells'][0]['outputs']), 1)
        output = output_nb['cells'][0]['outputs'][0]
        self.assertEqual(output['output_type'], 'error')
        self.assertEqual(output['ename'], 'StdinNotImplementedError')
        self.assertEqual(output['evalue'], 'raw_input was called, but this frontend does not support input requests.')

    def test_timeout(self):
        """Check that an error is raised when a computation times out"""
        current_dir = os.path.dirname(__file__)
        filename = os.path.join(current_dir, 'files', 'Interrupt.ipynb')
        res = self.build_resources()
        res['metadata']['path'] = os.path.dirname(filename)
        try:
            exception = TimeoutError
        except NameError:
            exception = RuntimeError

        assert_raises(exception, self.run_notebook, filename, dict(timeout=1), res)

    def test_timeout_func(self):
        """Check that an error is raised when a computation times out"""
        current_dir = os.path.dirname(__file__)
        filename = os.path.join(current_dir, 'files', 'Interrupt.ipynb')
        res = self.build_resources()
        res['metadata']['path'] = os.path.dirname(filename)
        try:
            exception = TimeoutError
        except NameError:
            exception = RuntimeError

        def timeout_func(source):
            return 10

        assert_raises(exception, self.run_notebook, filename, dict(timeout_func=timeout_func), res)

    def test_allow_errors(self):
        """
        Check that conversion continues if ``allow_errors`` is False.
        """
        current_dir = os.path.dirname(__file__)
        filename = os.path.join(current_dir, 'files', 'Skip Exceptions.ipynb')
        res = self.build_resources()
        res['metadata']['path'] = os.path.dirname(filename)
        with assert_raises(CellExecutionError) as exc:
            self.run_notebook(filename, dict(allow_errors=False), res)
        self.assertIsInstance(str(exc.exception), str)
        if sys.version_info >= (3, 0):
            assert_in(u"# üñîçø∂é", str(exc.exception))
        else:
            assert_in(u"# üñîçø∂é".encode('utf8', 'replace'),
                      str(exc.exception))

    def test_custom_kernel_manager(self):
        from .fake_kernelmanager import FakeCustomKernelManager

        current_dir = os.path.dirname(__file__)

        filename = os.path.join(current_dir, 'files', 'HelloWorld.ipynb')

        with io.open(filename) as f:
            input_nb = nbformat.read(f, 4)

        preprocessor = self.build_preprocessor({
            'kernel_manager_class': FakeCustomKernelManager
        })

        cleaned_input_nb = copy.deepcopy(input_nb)
        for cell in cleaned_input_nb.cells:
            if 'execution_count' in cell:
                del cell['execution_count']
            cell['outputs'] = []

        # Override terminal size to standardise traceback format
        with modified_env({'COLUMNS': '80', 'LINES': '24'}):
            output_nb, _ = preprocessor(cleaned_input_nb,
                                        self.build_resources())

        expected = FakeCustomKernelManager.expected_methods.items()

        for method, call_count in expected:
            self.assertNotEqual(call_count, 0, '{} was called'.format(method))

    def test_execute_function(self):
        # Test the executenb() convenience API
        current_dir = os.path.dirname(__file__)
        filename = os.path.join(current_dir, 'files', 'HelloWorld.ipynb')

        with io.open(filename) as f:
            input_nb = nbformat.read(f, 4)

        original = copy.deepcopy(input_nb)
        executed = executenb(original, os.path.dirname(filename))
        self.assert_notebooks_equal(original, executed)
