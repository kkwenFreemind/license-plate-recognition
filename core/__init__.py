"""核心模組"""

from .base_detector import BaseDetector
from .recognizer_base import DetailRecognizer
from .system import MultiModalRecognitionSystem

__all__ = ['BaseDetector', 'DetailRecognizer', 'MultiModalRecognitionSystem']
