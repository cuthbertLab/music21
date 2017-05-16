"""Tests for PDF export"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import logging
import os
import shutil

from ipython_genutils.testing import decorators as dec
from testpath import tempdir

from .base import ExportersTestsBase
from ..pdf import PDFExporter


#-----------------------------------------------------------------------------
# Class
#-----------------------------------------------------------------------------

class TestPDF(ExportersTestsBase):
    """Test PDF export"""

    exporter_class = PDFExporter

    def test_constructor(self):
        """Can a PDFExporter be constructed?"""
        self.exporter_class()


    @dec.onlyif_cmds_exist('xelatex')
    @dec.onlyif_cmds_exist('pandoc')
    def test_export(self):
        """Smoke test PDFExporter"""
        with tempdir.TemporaryDirectory() as td:
            newpath = os.path.join(td, os.path.basename(self._get_notebook()))
            shutil.copy(self._get_notebook(), newpath)
            (output, resources) = self.exporter_class(latex_count=1).from_filename(newpath)
            self.assertIsInstance(output, bytes)
            assert len(output) > 0

