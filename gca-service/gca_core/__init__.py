"""
GCA Core: Geometric Conscience Architecture
A framework for transparent, ethical AI reasoning through geometric vector manipulation.
"""

from .glassbox import GlassBox
from .moral import MoralKernel, Action, EntropyClass
from .memory import IsotropicMemory
from .optimizer import GCAOptimizer
from .qpt import QuaternionArchitect
from .arena import ArenaProtocol

__version__ = "4.5.1"
__all__ = [
    "GlassBox",
    "MoralKernel",
    "Action",
    "EntropyClass",
    "IsotropicMemory",
    "GCAOptimizer",
    "QuaternionArchitect",
    "ArenaProtocol",
]
