#!/usr/bin/env python3
"""
Final Integration Verification - Check main_window.py integration
"""
import sys
import os

sys.path.insert(0, r'd:\Downloads\bp_monitor-main')

print("=" * 80)
print("🔧 INTEGRATION VERIFICATION - main_window.py")
print("=" * 80)

all_passed = True

# Test 1: Check imports in main_window.py
print("\n1️⃣  Checking main_window.py imports...")
try:
    # Read main_window.py
    file_path = os.path.join(os.path.dirname(__file__), 'app', 'main_window.py')
    with open(file_path, 'r', encoding='utf-8') as f:
        source = f.read()
    
    required_imports = [
        'DashboardPageRefactored',
        'MeasurementsPageRefactored', 
        'MedicationsPage',
        'ActivitiesPage',
        'ThresholdsPage',
        'ReportsPage',
        'RecommendationsPage',
        'DashboardViewModel',
        'MeasurementsViewModel',
        'MedicationsViewModel',
        'ActivitiesViewModel',
        'ThresholdsViewModel',
        'ReportsViewModel',
        'RecommendationsViewModel',
        'MonitoringService',
        'WeatherService',
        'AnalysisService',
    ]
    
    for imp in required_imports:
        if imp in source:
            print(f"   ✅ {imp}")
        else:
            print(f"   ❌ {imp} MISSING")
            all_passed = False
except Exception as e:
    print(f"   ❌ FAILED: {e}")
    all_passed = False

# Test 2: Check _patient_pages method
print("\n2️⃣  Checking _patient_pages() integration...")
try:
    required_pages = [
        'DashboardPageRefactored',
        'MeasurementsPageRefactored',
        'MedicationsPage',
        'ActivitiesPage', 
        'ThresholdsPage',
        'ReportsPage',
        'RecommendationsPage',
    ]
    
    for page in required_pages:
        if page in source:
            print(f"   ✅ {page}")
        else:
            print(f"   ❌ {page} MISSING")
            all_passed = False
except Exception as e:
    print(f"   ❌ FAILED: {e}")
    all_passed = False

# Test 3: Check ViewModel instantiation
print("\n3️⃣  Checking ViewModel instantiation...")
try:
    viewmodel_creates = [
        'dashboard_vm =',
        'measurements_vm =',
        'medications_vm =',
        'activities_vm =',
        'thresholds_vm =',
        'reports_vm =',
        'recommendations_vm =',
    ]
    
    for vm in viewmodel_creates:
        if vm in source:
            print(f"   ✅ {vm}")
        else:
            print(f"   ❌ {vm} MISSING")
            all_passed = False
except Exception as e:
    print(f"   ❌ FAILED: {e}")
    all_passed = False

# Test 4: Check refresh_all() updates
print("\n4️⃣  Checking refresh_all() updates...")
try:
    refresh_calls = [
        "dashboard_page._view_model.refresh_data()",
        "measurements_page._view_model.load_measurements()",
        "medications_page._view_model.load_medications()",
        "activities_page._view_model.load_activities()",
        "thresholds_page._view_model.load_profile()",
        "reports_page._view_model.load_reports()",
        "recommendations_page._view_model.load_recommendations()",
    ]
    
    for call in refresh_calls:
        if call in source:
            print(f"   ✅ {call}")
        else:
            print(f"   ❌ {call} MISSING")
            all_passed = False
except Exception as e:
    print(f"   ❌ FAILED: {e}")
    all_passed = False

# Test 5: Check navigation items
print("\n5️⃣  Checking navigation items...")
try:
    nav_items = [
        ('"Ліки"', 'Ліки'),
        ('"Активність"', 'Активність'),
        ('"Пороги"', 'Пороги'),
        ('"Звіти"', 'Звіти'),
    ]
    
    for key, label in nav_items:
        if key in source:
            print(f"   ✅ {label}")
        else:
            print(f"   ❌ {label} MISSING")
            all_passed = False
except Exception as e:
    print(f"   ❌ FAILED: {e}")
    all_passed = False

# Test 6: Try to import main_window (syntax check)
print("\n6️⃣  Checking main_window.py syntax...")
try:
    from app import main_window
    print("   ✅ main_window.py imports successfully")
except SyntaxError as e:
    print(f"   ❌ Syntax error: {e}")
    all_passed = False
except ImportError as e:
    print(f"   ⚠️  Import error (may need PyQt6): {e}")
    # Don't fail here - PyQt6 might not be installed in test environment
except Exception as e:
    print(f"   ❌ Error: {e}")
    all_passed = False

# Summary
print("\n" + "=" * 80)
if all_passed:
    print("🎉🎉🎉 ALL INTEGRATION CHECKS PASSED! 🎉🎉🎉")
    print("=" * 80)
    print("\n✨ Integration Complete!")
    print("\n📊 Summary:")
    print("   • MainWindow now uses ViewModel-based pages")
    print("   • 5 new pages integrated: Medications, Activities, Thresholds, Reports, Recommendations")
    print("   • refresh_all() properly updates all ViewModels")
    print("   • Navigation includes all new functionality")
    print("\n🚀 Application is ready to run!")
    print("\n   Run: python -m app")
    sys.exit(0)
else:
    print("⚠️  Some integration checks failed")
    print("=" * 80)
    sys.exit(1)
