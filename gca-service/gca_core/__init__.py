"""
GCA Core: Geometric Conscience Architecture
A framework for transparent, ethical AI reasoning through geometric vector manipulation.
"""

from .glassbox import GlassBox
from .moral import MoralKernel, Action, EntropyClass
from .memory import IsotropicMemory
from .optimizer import GCAOptimizer
from .qpt import QuaternionArchitect, NonCommutativeProcessor
from .arena import ArenaProtocol

__version__ = "4.5.0"
__all__ = [
    "GlassBox",
    "MoralKernel",
    "Action",
    "EntropyClass",
    "IsotropicMemory",
    "GCAOptimizer",
    "QuaternionArchitect",
    "NonCommutativeProcessor",
    "ArenaProtocol",
]
