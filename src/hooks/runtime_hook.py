import os
import sys

# Application resources are immutable. User state paths are selected by the
# application (FILE_MANAGER_HOME/CONFIGPATH), never forced into _MEIPASS.
if hasattr(sys, "_MEIPASS"):
    os.environ.setdefault("RESOURCEPATH", sys._MEIPASS)
