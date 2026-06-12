"""Base ViewModel for MVVM pattern."""
from __future__ import annotations

from PyQt6.QtCore import QObject, pyqtSignal
from typing import Optional, Callable
import logging

_logger = logging.getLogger(__name__)


class BaseViewModel(QObject):
    """
    Base class for all ViewModels.
    
    Implements MVVM pattern: ViewModel mediates between View (UI) and Model (Service).
    """
    
    # Signals for View updates
    error_occurred = pyqtSignal(str)
    loading_changed = pyqtSignal(bool)
    data_changed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self._is_loading = False
        self._error_message: Optional[str] = None
        self._callbacks: list[Callable] = []
    
    @property
    def is_loading(self) -> bool:
        return self._is_loading
    
    @is_loading.setter
    def is_loading(self, value: bool):
        self._is_loading = value
        self.loading_changed.emit(value)
    
    @property
    def error_message(self) -> Optional[str]:
        return self._error_message
    
    def set_error(self, message: str):
        """Set error and notify View."""
        self._error_message = message
        _logger.error(f"ViewModel error: {message}")
        self.error_occurred.emit(message)
    
    def clear_error(self):
        """Clear error state."""
        self._error_message = None
    
    def safe_execute(self, func: Callable, error_message: str = "Operation failed"):
        """Execute function with error handling."""
        self.is_loading = True
        self.clear_error()
        try:
            result = func()
            self.data_changed.emit()
            return result
        except Exception as e:
            _logger.exception(error_message)
            self.set_error(f"{error_message}: {str(e)}")
            return None
        finally:
            self.is_loading = False
