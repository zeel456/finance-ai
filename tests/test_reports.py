"""
Test Suite for Report Generator and PDF Export
Save as: tests/test_reports.py

Run with: pytest tests/test_reports.py -v
"""

import pytest
import json
from datetime import datetime, timedelta
from io import BytesIO
from ai_modules.report_generator import ReportGenerator
from ai_modules.pdf_generator import PDFGenerator

class TestReportGenerator:
    """Test report data generation"""
    
    def test_monthly_report_structure(self):
        """Verify monthly report has correct structure"""
        report = ReportGenerator.generate_monthly_report(2025, 1)
        
        # Check required keys exist
        assert 'period' in report, "Missing 'period' key"
        assert 'summary' in report, "Missing 'summary' key"
        assert 'categories' in report, "Missing 'categories' key"
        
        # Check period structure
        period = report['period']
        assert period['type'] == 'monthly', "Period type should be 'monthly'"
        assert period['year'] == 2025, "Year mismatch"
        assert period['month'] == 1, "Month mismatch"
        assert 'start_date' in period, "Missing start_date"
        assert 'end_date' in period, "Missing end_date"
        
        print(f"✓ Monthly report structure valid")
        print(f"  Period: {period['month_name']} {period['year']}")
        print(f"  Range: {period['start_date']} to {period['end_date']}")
    
    def test_summary_data_types(self):
        """Verify summary contains correct data types"""
        report = ReportGenerator.generate_monthly_report(2025, 1)
        summary = report['summary']
        
        # Check data types
        assert isinstance(summary['total_expenses'], (int, float)), "total_expenses should be numeric"
        assert isinstance(summary['transaction_count'], int), "transaction_count should be int"
        assert isinstance(summary['average_transaction'], (int, float)), "average_transaction should be numeric"
        assert isinstance(summary['days_in_period'], int), "days_in_period should be int"
        
        # Check no negative values
        assert summary['total_expenses'] >= 0, "total_expenses cannot be negative"
        assert summary['transaction_count'] >= 0, "transaction_count cannot be negative"
        
        print(f"✓ Summary data types valid")
        print(f"  Total: ₹{summary['total_expenses']:,.2f}")
        print(f"  Count: {summary['transaction_count']}")
        print(f"  Average: ₹{summary['average_transaction']:,.2f}")
    
    def test_categories_data_consistency(self):
        """Verify categories data is consistent"""
        report = ReportGenerator.generate_monthly_report(2025, 1)
        categories = report['categories']
        
        if len(categories) == 0:
            print("⚠ Warning: No categories in report (empty database?)")
            return
        
        total_from_categories = 0
        total_from_summary = report['summary']['total_expenses']
        
        for cat in categories:
            assert 'name' in cat, "Category missing 'name'"
            assert 'total' in cat, "Category missing 'total'"
            assert 'count' in cat, "Category missing 'count'"
            assert 'percentage' in cat, "Category missing 'percentage'"
            
            assert isinstance(cat['total'], (int, float)), f"Category total should be numeric"
            assert isinstance(cat['count'], int), f"Category count should be int"
            assert 0 <= cat['percentage'] <= 100, f"Percentage should be 0-100, got {cat['percentage']}"
            
            total_from_categories += cat['total']
        
        # Verify total matches
        if total_from_summary > 0:
            assert abs(total_from_categories - total_from_summary) < 1, \
                f"Category total {total_from_categories} doesn't match summary {total_from_summary}"
        
        print(f"✓ Categories data consistent")
        print(f"  Categories: {len(categories)}")
        print(f"  Sum from categories: ₹{total_from_categories:,.2f}")
        print(f"  Summary total: ₹{total_from_summary:,.2f}")
    
    def test_quarterly_report_structure(self):
        """Verify quarterly report has correct structure"""
        report = ReportGenerator.generate_quarterly_report(2025, 1)
        
        assert 'period' in report, "Missing 'period' key"
        assert 'summary' in report, "Missing 'summary' key"
        assert 'monthly_breakdown' in report, "Missing 'monthly_breakdown' key"
        
        period = report['period']
        assert period['type'] == 'quarterly', "Period type should be 'quarterly'"
        assert period['quarter'] == 1, "Quarter mismatch"
        assert len(report['monthly_breakdown']) == 3, "Should have 3 months"
        
        print(f"✓ Quarterly report structure valid")
        print(f"  Quarter: Q{period['quarter']} {period['year']}")
        print(f"  Months: {[m['month_name'] for m in report['monthly_breakdown']]}")
    
    def test_comparison_report_structure(self):
        """Verify comparison report structure"""
        report = ReportGenerator.generate_comparison_report('monthly', 3)
        
        assert 'period_type' in report, "Missing 'period_type'"
        assert 'data' in report, "Missing 'data'"
        assert 'trend' in report, "Missing 'trend'"
        
        assert report['period_type'] == 'monthly', "Period type should match"
        assert len(report['data']) <= 3, f"Should have max 3 periods, got {len(report['data'])}"
        
        trend = report['trend']
        assert 'change_percentage' in trend, "Missing change_percentage"
        assert 'direction' in trend, "Missing direction"
        assert trend['direction'] in ['up', 'down', 'stable'], "Invalid direction"
        
        print(f"✓ Comparison report structure valid")
        print(f"  Periods: {len(report['data'])}")
        print(f"  Trend: {trend['direction']} ({trend['change_percentage']:.1f}%)")
    
    def test_custom_report_structure(self):
        """Verify custom range report"""
        start = '2025-01-01'
        end = '2025-01-31'
        report = ReportGenerator.generate_custom_report(start, end)
        
        assert 'period' in report, "Missing 'period' key"
        assert report['period']['type'] == 'custom', "Period type should be 'custom'"
        assert report['period']['start_date'] == start, "Start date mismatch"
        assert report['period']['end_date'] == end, "End date mismatch"
        
        print(f"✓ Custom report structure valid")
        print(f"  Range: {start} to {end}")
        print(f"  Days: {report['period']['days']}")


class TestPDFGenerator:
    """Test PDF generation"""
    
    def create_sample_report(self):
        """Create a sample report for testing"""
        return {
            'period': {
                'type': 'monthly',
                'year': 2025,
                'month': 1,
                'month_name': 'January',
                'start_date': '2025-01-01',
                'end_date': '2025-01-31'
            },
            'summary': {
                'total_expenses': 15000.50,
                'transaction_count': 45,
                'average_transaction': 333.34,
                'average_daily': 484.53,
                'total_tax': 2250.00,
                'days_in_period': 31
            },
            'categories': [
                {
                    'name': 'Food & Dining',
                    'total': 3500.00,
                    'count': 15,
                    'percentage': 23.33
                },
                {
                    'name': 'Transportation',
                    'total': 2800.00,
                    'count': 8,
                    'percentage': 18.67
                },
                {
                    'name': 'Shopping',
                    'total': 4200.00,
                    'count': 12,
                    'percentage': 28.00
                },
                {
                    'name': 'Utilities',
                    'total': 1500.00,
                    'count': 5,
                    'percentage': 10.00
                },
                {
                    'name': 'Entertainment',
                    'total': 3000.00,
                    'count': 5,
                    'percentage': 20.00
                }
            ],
            'vendors': [
                {'name': 'Amazon', 'total': 2500.00, 'count': 5},
                {'name': 'Uber', 'total': 1200.00, 'count': 8},
                {'name': 'Zomato', 'total': 1800.00, 'count': 12},
                {'name': 'Flipkart', 'total': 900.00, 'count': 3}
            ]
        }
    
    def test_pdf_generation_monthly(self):
        """Test PDF generation for monthly report"""
        report = self.create_sample_report()
        
        try:
            pdf_buffer = PDFGenerator.generate_report_pdf(
                report, 
                'monthly'
            )
            
            assert pdf_buffer is not None, "PDF buffer is None"
            assert isinstance(pdf_buffer, BytesIO), "Should return BytesIO object"
            
            pdf_size = pdf_buffer.getbuffer().nbytes
            assert pdf_size > 1000, f"PDF too small ({pdf_size} bytes), likely empty"
            
            print(f"✓ PDF generated successfully")
            print(f"  Size: {pdf_size / 1024:.2f} KB")
            
        except Exception as e:
            pytest.fail(f"PDF generation failed: {str(e)}")
    
    def test_pdf_with_charts(self):
        """Test PDF generation with chart images"""
        report = self.create_sample_report()
        
        # Create a minimal valid base64 PNG (1x1 pixel transparent PNG)
        sample_chart_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        
        charts = {
            'category_chart': f"data:image/png;base64,{sample_chart_base64}",
            'daily_chart': f"data:image/png;base64,{sample_chart_base64}"
        }
        
        try:
            pdf_buffer = PDFGenerator.generate_report_pdf(
                report,
                'monthly',
                charts
            )
            
            assert pdf_buffer is not None, "PDF buffer is None"
            pdf_size = pdf_buffer.getbuffer().nbytes
            assert pdf_size > 2000, f"PDF with charts too small ({pdf_size} bytes)"
            
            print(f"✓ PDF with charts generated successfully")
            print(f"  Size: {pdf_size / 1024:.2f} KB")
            print(f"  Charts included: {len(charts)}")
            
        except Exception as e:
            pytest.fail(f"PDF with charts generation failed: {str(e)}")
    
    def test_pdf_data_integrity(self):
        """Verify PDF contains correct data"""
        report = self.create_sample_report()
        
        pdf_buffer = PDFGenerator.generate_report_pdf(report, 'monthly')
        pdf_bytes = pdf_buffer.getvalue()
        pdf_text = pdf_bytes.decode('latin-1', errors='ignore')
        
        # Check for key data points in PDF
        checks = [
            ('January', 'Month name'),
            ('2025', 'Year'),
            ('15000', 'Total amount'),
            ('45', 'Transaction count'),
            ('Food & Dining', 'Category'),
            ('Amazon', 'Vendor'),
        ]
        
        found_count = 0
        for check_text, description in checks:
            if check_text in pdf_text:
                found_count += 1
                print(f"  ✓ Found: {description} ({check_text})")
            else:
                print(f"  ✗ Missing: {description} ({check_text})")
        
        assert found_count >= 4, f"PDF missing critical data (found {found_count}/6)"
        print(f"✓ PDF data integrity check passed ({found_count}/6 items found)")
    
    def test_quarterly_pdf(self):
        """Test quarterly report PDF"""
        report = {
            'period': {
                'type': 'quarterly',
                'year': 2025,
                'quarter': 1,
                'start_date': '2025-01-01',
                'end_date': '2025-03-31'
            },
            'summary': {
                'total_expenses': 45000.00,
                'transaction_count': 120,
                'average_monthly': 15000.00,
                'days_in_period': 90
            },
            'monthly_breakdown': [
                {'month': 1, 'month_name': 'January', 'total': 15000.00, 'count': 40},
                {'month': 2, 'month_name': 'February', 'total': 14500.00, 'count': 38},
                {'month': 3, 'month_name': 'March', 'total': 15500.00, 'count': 42}
            ],
            'categories': [
                {'name': 'Food', 'total': 10500.00, 'count': 45, 'percentage': 23.33},
                {'name': 'Transport', 'total': 8400.00, 'count': 24, 'percentage': 18.67}
            ]
        }
        
        pdf_buffer = PDFGenerator.generate_report_pdf(report, 'quarterly')
        pdf_size = pdf_buffer.getbuffer().nbytes
        
        assert pdf_size > 1000, "Quarterly PDF too small"
        print(f"✓ Quarterly PDF generated ({pdf_size / 1024:.2f} KB)")


class TestDataValidation:
    """Test data validation and edge cases"""
    
    def test_empty_report(self):
        """Test handling of empty report"""
        report = {
            'period': {'type': 'monthly', 'year': 2025, 'month': 1},
            'summary': {'total_expenses': 0, 'transaction_count': 0},
            'categories': []
        }
        
        pdf_buffer = PDFGenerator.generate_report_pdf(report, 'monthly')
        assert pdf_buffer is not None, "Should handle empty reports"
        print(f"✓ Empty report handled correctly")
    
    def test_missing_optional_fields(self):
        """Test report with missing optional fields"""
        report = {
            'period': {'type': 'monthly', 'year': 2025, 'month': 1},
            'summary': {'total_expenses': 1000.00, 'transaction_count': 5},
            'categories': []
            # Missing vendors, payment_methods, etc.
        }
        
        pdf_buffer = PDFGenerator.generate_report_pdf(report, 'monthly')
        assert pdf_buffer is not None, "Should handle missing optional fields"
        print(f"✓ Missing optional fields handled correctly")
    
    def test_invalid_base64_image(self):
        """Test handling of invalid base64 images"""
        report = {
            'period': {'type': 'monthly', 'year': 2025, 'month': 1},
            'summary': {'total_expenses': 1000.00, 'transaction_count': 5},
            'categories': []
        }
        
        charts = {
            'bad_chart': 'not-valid-base64-data!!!',
            'empty_chart': ''
        }
        
        # Should not crash, just skip invalid charts
        pdf_buffer = PDFGenerator.generate_report_pdf(report, 'monthly', charts)
        assert pdf_buffer is not None, "Should handle invalid base64 gracefully"
        print(f"✓ Invalid base64 images handled gracefully")


if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v', '--tb=short'])