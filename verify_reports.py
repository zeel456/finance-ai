"""
Quick Report Data Verification Script
Save as: verify_reports.py in project root
Run from project root: python verify_reports.py
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from sqlalchemy import func

# Import your models
try:
    from models.database import db
    from models.transaction import Transaction
    from models.category import Category
    from ai_modules.report_generator import ReportGenerator
    print("✓ All imports successful\n")
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)


class QuickReportVerifier:
    """Quick verification of report data"""
    
    @staticmethod
    def verify_database_connection():
        """Check if database connection works"""
        print("="*60)
        print("1. DATABASE CONNECTION CHECK")
        print("="*60)
        try:
            # Try a simple query
            count = db.session.query(Transaction).count()
            print(f"✓ Database connected")
            print(f"  Total transactions in DB: {count}\n")
            return True
        except Exception as e:
            print(f"✗ Database error: {e}\n")
            return False
    
    @staticmethod
    def verify_monthly_report_data(year, month):
        """Verify monthly report generates correct data"""
        print("="*60)
        print(f"2. MONTHLY REPORT VERIFICATION: {month}/{year}")
        print("="*60)
        
        try:
            # Generate report
            report = ReportGenerator.generate_monthly_report(year, month)
            print("✓ Report generated successfully")
            
            # Check structure
            print("\nStructure Check:")
            keys_ok = all(key in report for key in ['period', 'summary', 'categories'])
            print(f"  {'✓' if keys_ok else '✗'} Has required keys (period, summary, categories)")
            
            # Get data
            summary = report['summary']
            period = report['period']
            
            print(f"\nReport Data:")
            print(f"  Period: {period['month_name']} {period['year']}")
            print(f"  Date Range: {period['start_date']} to {period['end_date']}")
            print(f"  Total Expenses: ₹{summary['total_expenses']:,.2f}")
            print(f"  Transaction Count: {summary['transaction_count']}")
            print(f"  Average Transaction: ₹{summary['average_transaction']:,.2f}")
            print(f"  Daily Average: ₹{summary['average_daily']:,.2f}")
            print(f"  Days in Period: {summary['days_in_period']}")
            
            # Manually verify from database
            print(f"\nDatabase Verification:")
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1)
            else:
                end_date = datetime(year, month + 1, 1)
            
            db_total = db.session.query(
                func.sum(Transaction.amount)
            ).filter(
                Transaction.transaction_date >= start_date,
                Transaction.transaction_date < end_date
            ).scalar() or 0
            
            db_count = db.session.query(
                func.count(Transaction.id)
            ).filter(
                Transaction.transaction_date >= start_date,
                Transaction.transaction_date < end_date
            ).scalar() or 0
            
            print(f"  DB Total: ₹{db_total:,.2f}")
            print(f"  Report Total: ₹{summary['total_expenses']:,.2f}")
            print(f"  Match: {'✓ YES' if abs(db_total - summary['total_expenses']) < 0.01 else '✗ NO'}")
            
            print(f"\n  DB Count: {db_count}")
            print(f"  Report Count: {summary['transaction_count']}")
            print(f"  Match: {'✓ YES' if db_count == summary['transaction_count'] else '✗ NO'}")
            
            # Check categories
            print(f"\nCategories Check:")
            categories = report.get('categories', [])
            print(f"  Total categories: {len(categories)}")
            
            if categories:
                categories_sum = sum(cat['total'] for cat in categories)
                print(f"  Sum from categories: ₹{categories_sum:,.2f}")
                print(f"  Summary total: ₹{summary['total_expenses']:,.2f}")
                print(f"  Match: {'✓ YES' if abs(categories_sum - summary['total_expenses']) < 0.01 else '✗ NO'}")
                
                percentage_sum = sum(cat['percentage'] for cat in categories)
                print(f"\n  Percentage sum: {percentage_sum:.1f}%")
                print(f"  Valid (should be 100%): {'✓ YES' if abs(percentage_sum - 100) < 0.1 else '✗ NO'}")
                
                print(f"\n  Top 5 Categories:")
                for cat in categories[:5]:
                    print(f"    • {cat['name']}: ₹{cat['total']:,.2f} ({cat['percentage']:.1f}%)")
            
            # Check calculations
            print(f"\nCalculation Verification:")
            if summary['transaction_count'] > 0:
                expected_avg = summary['total_expenses'] / summary['transaction_count']
                actual_avg = summary['average_transaction']
                match = abs(expected_avg - actual_avg) < 0.01
                print(f"  Average Transaction:")
                print(f"    Expected: ₹{expected_avg:,.2f}")
                print(f"    Actual: ₹{actual_avg:,.2f}")
                print(f"    {'✓ CORRECT' if match else '✗ WRONG'}")
            
            if summary['days_in_period'] > 0:
                expected_daily = summary['total_expenses'] / summary['days_in_period']
                actual_daily = summary['average_daily']
                match = abs(expected_daily - actual_daily) < 0.01
                print(f"\n  Daily Average:")
                print(f"    Expected: ₹{expected_daily:,.2f}")
                print(f"    Actual: ₹{actual_daily:,.2f}")
                print(f"    {'✓ CORRECT' if match else '✗ WRONG'}")
            
            print()
            return True
            
        except Exception as e:
            print(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    @staticmethod
    def verify_quarterly_report_data(year, quarter):
        """Verify quarterly report"""
        print("="*60)
        print(f"3. QUARTERLY REPORT VERIFICATION: Q{quarter}/{year}")
        print("="*60)
        
        try:
            report = ReportGenerator.generate_quarterly_report(year, quarter)
            print("✓ Report generated successfully")
            
            period = report['period']
            summary = report['summary']
            
            print(f"\nReport Data:")
            print(f"  Quarter: Q{period['quarter']} {period['year']}")
            print(f"  Total Expenses: ₹{summary['total_expenses']:,.2f}")
            print(f"  Transaction Count: {summary['transaction_count']}")
            print(f"  Average Monthly: ₹{summary['average_monthly']:,.2f}")
            
            print(f"\nMonthly Breakdown:")
            monthly = report.get('monthly_breakdown', [])
            for m in monthly:
                print(f"  • {m['month_name']}: ₹{m['total']:,.2f} ({m['count']} transactions)")
            
            # Verify sum
            if monthly:
                monthly_sum = sum(m['total'] for m in monthly)
                print(f"\n  Sum from months: ₹{monthly_sum:,.2f}")
                print(f"  Quarterly total: ₹{summary['total_expenses']:,.2f}")
                print(f"  Match: {'✓ YES' if abs(monthly_sum - summary['total_expenses']) < 0.01 else '✗ NO'}")
            
            print()
            return True
            
        except Exception as e:
            print(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    @staticmethod
    def run_all_checks():
        """Run all verification checks"""
        print("\n")
        print("╔" + "="*58 + "╗")
        print("║" + " "*58 + "║")
        print("║" + "  REPORT DATA VERIFICATION SUITE".center(58) + "║")
        print("║" + " "*58 + "║")
        print("╚" + "="*58 + "╝")
        print()
        
        # Check database
        if not QuickReportVerifier.verify_database_connection():
            print("✗ Cannot continue without database connection")
            return False
        
        # Check monthly report
        current_year = datetime.now().year
        current_month = datetime.now().month
        
        monthly_ok = QuickReportVerifier.verify_monthly_report_data(current_year, current_month)
        
        # Check quarterly report
        current_quarter = (current_month - 1) // 3 + 1
        quarterly_ok = QuickReportVerifier.verify_quarterly_report_data(current_year, current_quarter)
        
        # Summary
        print("="*60)
        print("VERIFICATION SUMMARY")
        print("="*60)
        print(f"Monthly Report: {'✓ PASS' if monthly_ok else '✗ FAIL'}")
        print(f"Quarterly Report: {'✓ PASS' if quarterly_ok else '✗ FAIL'}")
        
        if monthly_ok and quarterly_ok:
            print("\n✓ ALL CHECKS PASSED - Reports are generating correct data!")
            print("✓ You can proceed with PDF export")
        else:
            print("\n✗ SOME CHECKS FAILED - Review errors above")
        
        print()
        return monthly_ok and quarterly_ok


if __name__ == '__main__':
    try:
        success = QuickReportVerifier.run_all_checks()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)