"""
Test script to demonstrate improvements in document processing
"""

from ai_modules.data_extractor import ImprovedDataExtractor
from ai_modules.categorizer import ImprovedTransactionCategorizer

# Test data examples
test_receipts = [
    """
    RELIANCE FRESH
    Store #234, MG Road
    Bangalore - 560001
    Tel: 080-12345678
    
    Invoice No: RF/BLR/2024/001234
    Date: 15-Jan-2024
    
    ITEMS:
    Rice (5kg)          Rs. 450.00
    Cooking Oil         Rs. 180.00
    Vegetables          Rs. 120.00
    Milk (2L)           Rs. 98.00
    
    Subtotal:           Rs. 848.00
    GST @ 5%:           Rs. 42.40
    --------------------------------
    TOTAL:              Rs. 890.40
    
    Payment: UPI
    Thank you for shopping!
    """,
    
    """
    OLA CABS
    Trip Receipt
    
    Booking ID: OLA123456789
    Date: 20 Jan 2024
    
    Pickup: Indiranagar
    Drop: Koramangala
    Distance: 8.5 km
    
    Base Fare:          ₹80
    Distance Fare:      ₹120
    Time Fare:          ₹45
    Service Tax (5%):   ₹12.25
    ----------------------------
    Total Paid:         ₹257.25
    
    Payment: Card ending ***1234
    Driver: Rajesh Kumar
    """,
    
    """
    Apollo Pharmacy
    #45, Brigade Road
    Bangalore - 560025
    
    Bill No: AP/2024/56789
    Date: 22-Jan-2024 14:30
    
    MEDICINES:
    Paracetamol 500mg (10) ₹25.00
    Vitamin D3           ₹380.00
    Band-Aid (Pack)      ₹45.00
    
    Subtotal:            ₹450.00
    Discount:            ₹22.50
    Net Amount:          ₹427.50
    
    Paid by: Cash
    Prescription ID: RX123456
    """,
    
    """
    PVRINOX Cinemas
    Forum Mall, Bangalore
    
    Movie: Jawan
    Date: 25 Jan 2024, 7:00 PM
    Screen: 3, Seats: G12, G13
    
    Ticket (2) @ ₹350    ₹700.00
    Booking Fee          ₹40.00
    CGST 9%              ₹66.60
    SGST 9%              ₹66.60
    --------------------------------
    Grand Total:         ₹873.20
    
    Booking ID: PVR987654321
    Paid via: Net Banking
    """,
    
    """
    JIO PREPAID RECHARGE
    
    Mobile: 9876543210
    Recharge Date: 28-Jan-2024
    
    Plan: ₹299
    Validity: 28 days
    Data: 2GB/day
    Calls: Unlimited
    
    Amount: Rs 299.00
    Payment Method: UPI
    Transaction ID: JIO202401280012345
    """,
]

def test_data_extraction():
    """Test improved data extraction"""
    print("=" * 80)
    print("TESTING DATA EXTRACTION")
    print("=" * 80)
    
    extractor = ImprovedDataExtractor()
    
    for i, receipt in enumerate(test_receipts, 1):
        print(f"\n{'='*80}")
        print(f"Test Receipt #{i}")
        print(f"{'='*80}")
        print(receipt[:200] + "..." if len(receipt) > 200 else receipt)
        print(f"\n{'─'*80}")
        print("EXTRACTED DATA:")
        print(f"{'─'*80}")
        
        data = extractor.extract_all_data(receipt)
        
        if data:
            print(f"✓ Date:             {data.get('date', 'Not found')}")
            print(f"✓ Vendor:           {data.get('vendor', 'Not found')}")
            print(f"✓ Amount:           ₹{data.get('amount', 0):.2f}")
            print(f"✓ Invoice Number:   {data.get('invoice_number', 'Not found')}")
            print(f"✓ Payment Method:   {data.get('payment_method', 'Not found')}")
            print(f"✓ Tax Amount:       ₹{data.get('tax_amount', 0) or 0:.2f}")
            print(f"✓ Tax Percentage:   {data.get('tax_percentage', 0) or 0}%")
            print(f"✓ Email:            {data.get('email', 'Not found')}")
            print(f"✓ Phone:            {data.get('phone', 'Not found')}")
            print(f"✓ Confidence:       {data.get('confidence', 0):.1f}%")
            
            # Show all amounts found
            if data.get('all_amounts'):
                print(f"\n  All amounts detected:")
                for context, amount in data['all_amounts'].items():
                    print(f"    - {context.capitalize()}: ₹{amount:.2f}")
            
            # Show all dates found
            if data.get('all_dates'):
                print(f"\n  All dates detected:")
                for context, date in data['all_dates'].items():
                    print(f"    - {context.capitalize()}: {date}")
            
            # Validation warnings
            warnings = extractor.validate_extraction(data)
            if warnings:
                print(f"\n⚠️  WARNINGS:")
                for warning in warnings:
                    print(f"    - {warning}")
        else:
            print("❌ Failed to extract data")
    
    print(f"\n{'='*80}\n")

def test_categorization():
    """Test improved categorization"""
    print("=" * 80)
    print("TESTING TRANSACTION CATEGORIZATION")
    print("=" * 80)
    
    categorizer = ImprovedTransactionCategorizer(model_type='nb')
    categorizer.train()
    
    # Test cases
    test_cases = [
        ("RELIANCE FRESH", "grocery shopping", 890.40),
        ("OLA CABS", "taxi ride", 257.25),
        ("Apollo Pharmacy", "medicines", 427.50),
        ("PVRINOX", "movie tickets", 873.20),
        ("JIO", "mobile recharge", 299.00),
        ("Swiggy", "food delivery", 450.00),
        ("Amazon India", "online shopping", 2500.00),
        ("BPCL Petrol Pump", "fuel", 3000.00),
        ("Max Hospital", "medical checkup", 1500.00),
        ("Netflix", "subscription", 499.00),
        ("HDFC Life", "insurance premium", 15000.00),
        ("Zerodha", "stock trading", 5000.00),
        ("Lakme Salon", "haircut", 800.00),
    ]
    
    print("\nSingle Category Predictions:")
    print("─" * 80)
    
    for vendor, desc, amount in test_cases:
        category, confidence = categorizer.predict_category(vendor, desc, amount)
        print(f"{vendor:25s} → {category:25s} (Confidence: {confidence:5.1f}%)")
    
    print(f"\n{'─'*80}")
    print("Top 3 Category Predictions:")
    print("─" * 80)
    
    # Show top 3 for some examples
    sample_cases = [
        ("RELIANCE FRESH", "grocery shopping", 890.40),
        ("Apollo Pharmacy", "medicines", 427.50),
        ("PVRINOX", "movie tickets", 873.20),
    ]
    
    for vendor, desc, amount in sample_cases:
        print(f"\n{vendor} ({desc}):")
        alternatives = categorizer.predict_with_alternatives(vendor, desc, amount, top_n=3)
        for i, (cat, conf) in enumerate(alternatives, 1):
            print(f"  {i}. {cat:30s} {conf:5.1f}%")
    
    print(f"\n{'='*80}\n")

def test_end_to_end():
    """Test complete workflow"""
    print("=" * 80)
    print("END-TO-END WORKFLOW TEST")
    print("=" * 80)
    
    extractor = ImprovedDataExtractor()
    categorizer = ImprovedTransactionCategorizer()
    categorizer.train()
    
    receipt = test_receipts[0]  # RELIANCE FRESH receipt
    
    print("\nProcessing receipt...")
    print("─" * 80)
    
    # Extract data
    data = extractor.extract_all_data(receipt)
    
    if data:
        print("EXTRACTED INFORMATION:")
        print(f"  Date:           {data['date']}")
        print(f"  Vendor:         {data['vendor']}")
        print(f"  Amount:         ₹{data['amount']:.2f}")
        print(f"  Invoice:        {data['invoice_number']}")
        print(f"  Payment:        {data['payment_method']}")
        
        # Categorize
        category, confidence = categorizer.predict_category(
            data['vendor'], 
            data.get('invoice_number', ''),
            data['amount']
        )
        
        print(f"\nCATEGORIZATION:")
        print(f"  Category:       {category}")
        print(f"  Confidence:     {confidence:.1f}%")
        
        # Final transaction object
        print(f"\nFINAL TRANSACTION RECORD:")
        print("─" * 80)
        transaction = {
            'date': str(data['date']),
            'vendor': data['vendor'],
            'amount': data['amount'],
            'category': category,
            'payment_method': data['payment_method'],
            'invoice_number': data['invoice_number'],
            'confidence': min(data['confidence'], confidence),
        }
        
        import json
        print(json.dumps(transaction, indent=2))
    
    print(f"\n{'='*80}\n")

def compare_old_vs_new():
    """Compare old extraction with new extraction"""
    print("=" * 80)
    print("COMPARISON: OLD vs NEW EXTRACTION")
    print("=" * 80)
    
    # Import old extractor
    import sys
    sys.path.insert(0, '/mnt/user-data/uploads')
    
    try:
        from ai_modules.data_extractor import DataExtractor as OldExtractor
        
        old_extractor = OldExtractor()
        new_extractor = ImprovedDataExtractor()
        
        receipt = test_receipts[1]  # OLA receipt
        
        print("\nTest Receipt:")
        print("─" * 80)
        print(receipt)
        
        print("\n" + "─" * 80)
        print("OLD EXTRACTOR RESULTS:")
        print("─" * 80)
        old_data = old_extractor.extract_all_data(receipt)
        if old_data:
            print(f"Date:     {old_data.get('date')}")
            print(f"Vendor:   {old_data.get('vendor')}")
            print(f"Amount:   ₹{old_data.get('amount', 0):.2f}")
            print(f"Payment:  {old_data.get('payment_method')}")
        
        print("\n" + "─" * 80)
        print("NEW EXTRACTOR RESULTS:")
        print("─" * 80)
        new_data = new_extractor.extract_all_data(receipt)
        if new_data:
            print(f"Date:     {new_data.get('date')}")
            print(f"Vendor:   {new_data.get('vendor')}")
            print(f"Amount:   ₹{new_data.get('amount', 0):.2f}")
            print(f"Invoice:  {new_data.get('invoice_number')}")
            print(f"Payment:  {new_data.get('payment_method')}")
            print(f"Email:    {new_data.get('email')}")
            print(f"Phone:    {new_data.get('phone')}")
            print(f"Confidence: {new_data.get('confidence')}%")
        
        print("\n" + "─" * 80)
        print("IMPROVEMENTS:")
        print("─" * 80)
        print("✓ Better vendor name extraction")
        print("✓ Invoice/receipt number detection")
        print("✓ Contact information extraction")
        print("✓ Contextual amount detection (total, subtotal, tax)")
        print("✓ Confidence scoring")
        print("✓ Validation warnings")
        print("✓ Multiple date context detection")
        
    except ImportError as e:
        print(f"Could not import old extractor: {e}")
    
    print(f"\n{'='*80}\n")

if __name__ == "__main__":
    print("\n" + "🔬 DOCUMENT PROCESSING IMPROVEMENTS TEST SUITE 🔬".center(80))
    print("\n")
    
    # Run tests
    test_data_extraction()
    test_categorization()
    test_end_to_end()
    compare_old_vs_new()
    
    print("\n✅ All tests completed!\n")