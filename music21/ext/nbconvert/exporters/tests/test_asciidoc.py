"""Tests for ASCIIDocExporter`"""

#-----------------------------------------------------------------------------
# Copyright (c) 2016, the IPython Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from .base import ExportersTestsBase
from ..asciidoc import ASCIIDocExporter
from ipython_genutils.testing import decorators as dec

#-----------------------------------------------------------------------------
# Class
#-----------------------------------------------------------------------------

class TestASCIIDocExporter(ExportersTestsBase):
    """Tests for ASCIIDocExporter"""

    exporter_class = ASCIIDocExporter

    def test_constructor(self):
        """
        Can a ASCIIDocExporter be constructed?
        """
        ASCIIDocExporter()


    @dec.onlyif_cmds_exist('pandoc')
    def test_export(self):
        """
        Can a ASCIIDocExporter export something?
        """
        (output, resources) = ASCIIDocExporter().from_filename(self._get_notebook())
        assert len(output) > 0
