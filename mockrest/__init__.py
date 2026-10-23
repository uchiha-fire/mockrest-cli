"""
mockrest-cli
Instant Zero-Config Mock REST API Server
"""

__version__ = "0.1.0"
__author__ = "Zephyrus Labs"
__maintainer__ = "Shubham Sharma"
__email__ = "zephyrus.labs@gmail.com"
__developer_email__ = "sharmashubham25962@gmail.com"

from .core import MockServer, generate_synthetic_data

__all__ = [
    "MockServer",
    "generate_synthetic_data",
    "__version__",
    "__author__",
    "__maintainer__",
    "__email__",
    "__developer_email__",
]
