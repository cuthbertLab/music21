"""HTML Exporter class"""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import os

from traitlets import default
from traitlets.config import Config

from nbconvert.filters.highlight import Highlight2HTML

from .templateexporter import TemplateExporter


class HTMLExporter(TemplateExporter):
    """
    Exports a basic HTML document.  This exporter assists with the export of
    HTML.  Inherit from it if you are writing your own HTML template and need
    custom preprocessors/filters.  If you don't need custom preprocessors/
    filters, just change the 'template_file' config option.
    """

    @default('file_extension')
    def _file_extension_default(self):
        return '.html'

    @default('default_template_path')
    def _default_template_path_default(self):
        return os.path.join("..", "templates", "html")

    @default('template_file')
    def _template_file_default(self):
        return 'full'
    
    output_mimetype = 'text/html'
    
    @property
    def default_config(self):
        c = Config({
            'NbConvertBase': {
                'display_data_priority' : ['application/vnd.jupyter.widget-state+json',
                                           'application/vnd.jupyter.widget-view+json',
                                           'application/javascript',
                                           'text/html',
                                           'text/markdown',
                                           'image/svg+xml',
                                           'text/latex',
                                           'image/png',
                                           'image/jpeg',
                                           'text/plain'
                                          ]
                },
            'CSSHTMLHeaderPreprocessor':{
                'enabled':True
                },
            'HighlightMagicsPreprocessor': {
                'enabled':True
                }
            })
        c.merge(super(HTMLExporter,self).default_config)
        return c

    def from_notebook_node(self, nb, resources=None, **kw):
        langinfo = nb.metadata.get('language_info', {})
        lexer = langinfo.get('pygments_lexer', langinfo.get('name', None))
        self.register_filter('highlight_code',
                             Highlight2HTML(pygments_lexer=lexer, parent=self))
        return super(HTMLExporter, self).from_notebook_node(nb, resources, **kw)
