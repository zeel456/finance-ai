"""
Verify Report Data Accuracy
Save as: verify_reports.py

Run with: python verify_reports.py
"""

import json
from datetime import datetime
from ai_modules.report_generator import ReportGenerator
from models.transaction import Transaction
from models.category import Category
from models.database import db

class ReportDataVerifier:
    """Verify that reports generate correct data"""
    
    @staticmethod
    def verify_monthly_report(year, month):
        """Verify monthly report data accuracy"""
        
        print(f"\n{'='*60}")
        print(f"VERIFYING MONTHLY REPORT: {month}/{year}")
        print(f"{'='*60}\n")
        
        # Generate report
        report = ReportGenerator.generate_monthly_report(year, month)
        
        # Verify structure
        print("1. STRUCTURE CHECK")
        print("-" * 40)
        required_keys = ['period', 'summary', 'categories']
        for key in required_keys:
            status = "✓" if key in report else "✗"
            print(f"  {status} {key}: {key in report}")
        
        # Verify summary data
        print("\n2. SUMMARY DATA CHECK")
        print("-" * 40)
        summary = report.get('summary', {})
        
        # Manually count from database
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
        
        db_total = db.session.query(
            db.func.sum(Transaction.amount)
        ).filter(
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date < end_date
        ).scalar() or 0
        
        db_count = db.session.query(
            db.func.count(Transaction.id)
        ).filter(
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date < end_date
        ).scalar() or 0
        
        report_total = summary.get('total_expenses', 0)
        report_count = summary.get('transaction_count', 0)
        
        print(f"  Total Expenses:")
        print(f"    Report: ₹{report_total:,.2f}")
        print(f"    Database: ₹{db_total:,.2f}")
        print(f"    Match: {'✓ YES' if abs(report_total - db_total) < 0.01 else '✗ NO'}")
        
        print(f"\n  Transaction Count:")
        print(f"    Report: {report_count}")
        print(f"    Database: {db_count}")
        print(f"    Match: {'✓ YES' if report_count == db_count else '✗ NO'}")
        
        # Verify categories sum
        print("\n3. CATEGORIES CHECK")
        print("-" * 40)
        categories = report.get('categories', [])
        categories_sum = sum(cat.get('total', 0) for cat in categories)
        
        print(f"  Total from categories: ₹{categories_sum:,.2f}")
        print(f"  Summary total: ₹{report_total:,.2f}")
        print(f"  Match: {'✓ YES' if abs(categories_sum - report_total) < 0.01 else '✗ NO'}")
        
        print(f"\n  Top 5 Categories:")
        for cat in categories[:5]:
            print(f"    • {cat['name']}: ₹{cat['total']:,.2f} ({cat['percentage']:.1f}%)")
        
        # Verify calculations
        print("\n4. CALCULATION CHECK")
        print("-" * 40)
        
        if report_count > 0:
            expected_avg = report_total / report_count
            actual_avg = summary.get('average_transaction', 0)
            print(f"  Average Transaction:")
            print(f"    Expected: ₹{expected_avg:,.2f}")
            print(f"    Actual: ₹{actual_avg:,.2f}")
            print(f"    Match: {'✓ YES' if abs(expected_avg - actual_avg) < 0.01 else '✗ NO'}")
        
        days_in_period = summary.get('days_in_period', 0)
        if days_in_period > 0:
            expected_daily_avg = report_total / days_in_period
            actual_daily_avg = summary.get('average_daily', 0)
            print(f"\n  Daily Average:")
            print(f"    Expected: ₹{expected_daily_avg:,.2f}")
            print(f"    Actual: ₹{actual_daily_avg:,.2f}")
            print(f"    Match: {'✓ YES' if abs(expected_daily_avg - actual_daily_avg) < 0.01 else '✗ NO'}")
        
        # Verify percentages
        print("\n5. PERCENTAGE CHECK")
        print("-" * 40)
        percentage_sum = sum(cat.get('percentage', 0) for cat in categories)
        print(f"  Sum of percentages: {percentage_sum:.1f}%")
        print(f"  Valid: {'✓ YES (100%)' if abs(percentage_sum - 100) < 0.1 else '✗ NO'}")
        
        # Verify dates
        print("\n6. DATE CHECK")
        print("-" * 40)
        period = report.get('period', {})
        print(f"  Start Date: {period.get('start_date')}")
        print(f"  End Date: {period.get('end_date')}")
        print(f"  Days in Period: {days_in_period}")
        
        expected_days = (end_date - start_date).days
        print(f"  Expected Days: {expected_days}")
        print(f"  Match: {'✓ YES' if days_in_period == expected_days else '✗ NO'}")
        
        return {
            'total_match': abs(report_total - db_total) < 0.01,
            'count_match': report_count == db_count,
            'categories_match': abs(categories_sum - report_total) < 0.01,
            'percentage_valid': abs(percentage_sum - 100) < 0.1
        }
    
    @staticmethod
    def verify_quarterly_report(year, quarter):
        """Verify quarterly report data accuracy"""
        
        print(f"\n{'='*60}")
        print(f"VERIFYING QUARTERLY REPORT: Q{quarter}/{year}")
        print(f"{'='*60}\n")
        
        # Generate report
        report = ReportGenerator.generate_quarterly_report(year, quarter)
        
        # Get monthly reports for verification
        quarter_months = {
            1: (1, 2, 3),
            2: (4, 5, 6),
            3: (7, 8, 9),
            4: (10, 11, 12)
        }
        
        months = quarter_months.get(quarter, (1, 2, 3))
        
        print("1. MONTHLY BREAKDOWN CHECK")
        print("-" * 40)
        
        total_from_months = 0
        for month in months:
            monthly = ReportGenerator.generate_monthly_report(year, month)
            month_total = monthly['summary']['total_expenses']
            total_from_months += month_total
            print(f"  {monthly['period']['month_name']}: ₹{month_total:,.2f}")
        
        report_total = report['summary']['total_expenses']
        print(f"\n  Sum from months: ₹{total_from_months:,.2f}")
        print(f"  Quarterly total: ₹{report_total:,.2f}")
        print(f"  Match: {'✓ YES' if abs(total_from_months - report_total) < 0.01 else '✗ NO'}")
        
        # Verify average monthly
        print("\n2. AVERAGE CALCULATION CHECK")
        print("-" * 40)
        expected_avg = total_from_months / 3
        actual_avg = report['summary'].get('average_monthly', 0)
        print(f"  Expected Average: ₹{expected_avg:,.2f}")
        print(f"  Actual Average: ₹{actual_avg:,.2f}")
        print(f"  Match: {'✓ YES' if abs(expected_avg - actual_avg) < 0.01 else '✗ NO'}")
        
        return {
            'months_match': abs(total_from_months - report_total) < 0.01,
            'average_match': abs(expected_avg - actual_avg) < 0.01
        }
    
    @staticmethod
    def generate_verification_report():
        """Generate comprehensive verification report"""
        
        print("\n" + "="*60)
        print("COMPREHENSIVE REPORT VERIFICATION")
        print("="*60)
        
        current_year = datetime.now().year
        current_month = datetime.now().month
        
        # Test current month
        monthly_results = ReportDataVerifier.verify_monthly_report(current_year, current_month)
        
        # Test current quarter
        current_quarter = (current_month - 1) // 3 + 1
        quarterly_results = ReportDataVerifier.verify_quarterly_report(current_year, current_quarter)
        
        # Summary
        print("\n" + "="*60)
        print("VERIFICATION SUMMARY")
        print("="*60)
        
        all_passed = all(monthly_results.values()) and all(quarterly_results.values())
        
        print("\nMonthly Report:")
        for check, passed in monthly_results.items():
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"  {status}: {check}")
        
        print("\nQuarterly Report:")
        for check, passed in quarterly_results.items():
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"  {status}: {check}")
        
        print("\n" + "="*60)
        if all_passed:
            print("✓ ALL CHECKS PASSED - Reports are accurate!")
        else:
            print("✗ SOME CHECKS FAILED - Review errors above")
        print("="*60 + "\n")
        
        return all_passed


if __name__ == '__main__':
    # Run verification
    try:
        verifier = ReportDataVerifier()
        success = verifier.generate_verification_report()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)