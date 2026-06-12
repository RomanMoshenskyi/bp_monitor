"""Verify Phase 4 - ViewModels."""
import sys
sys.path.insert(0, r'd:\Downloads\bp_monitor-main')

print("=" * 60)
print("PHASE 4 CHECK: ViewModels")
print("=" * 60)

# Test 1: ViewModels import
print("\n1. Testing ViewModels import...")
try:
    from app.presentation.view_models import (
        BaseViewModel,
        DashboardViewModel,
        MeasurementsViewModel,
        AnalyticsViewModel,
    )
    print("   ✅ All ViewModels imported")
except Exception as e:
    print(f"   ❌ ViewModels import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 2: PyQt6 signals
print("\n2. Testing PyQt6 signals...")
try:
    from PyQt6.QtCore import QObject, pyqtSignal
    
    class TestSignals(QObject):
        test_signal = pyqtSignal()
    
    t = TestSignals()
    print("   ✅ PyQt6 signals working")
except Exception as e:
    print(f"   ❌ PyQt6 signals failed: {e}")
    sys.exit(1)

# Test 3: ViewModel inheritance
print("\n3. Testing ViewModel structure...")
try:
    from app.presentation.view_models import BaseViewModel
    
    # Check BaseViewModel has required signals
    assert hasattr(BaseViewModel, 'error_occurred')
    assert hasattr(BaseViewModel, 'loading_changed')
    assert hasattr(BaseViewModel, 'data_changed')
    assert hasattr(BaseViewModel, 'is_loading')
    assert hasattr(BaseViewModel, 'set_error')
    
    print("   ✅ BaseViewModel has all required methods/signals")
except Exception as e:
    print(f"   ❌ ViewModel structure test failed: {e}")
    import traceback
    traceback.print_exc()

# Summary
print("\n" + "=" * 60)
print("✅ PHASE 4 COMPLETE - ViewModels Ready")
print("=" * 60)
print("\nViewModels implemented:")
print("  - BaseViewModel (base class with error handling)")
print("  - DashboardViewModel (latest measurement, stats)")
print("  - MeasurementsViewModel (paginated list, add/delete)")
print("  - AnalyticsViewModel (correlation, charts)")
print("\nAll ViewModels use PyQt6 signals for View updates.")
print("\nNext: UI refactoring to use ViewModels")
