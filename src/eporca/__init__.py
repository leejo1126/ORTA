"""eporca: EP-ORCA immunofluorescence analysis pipeline.

Only lightweight modules (config, dax_reader) are imported here so that
`import eporca` works in both the cellpose-gpu and analysis environments.
Heavy modules (segment, foci, analysis.*) are imported on demand.
"""

from .config import Config

__all__ = ["Config"]
__version__ = "0.1.0"
