import re
from datetime import datetime
from dateutil import parser as date_parser
import traceback
from typing import Dict, List, Optional, Tuple
from collections import Counter

class ImprovedDataExtractor:
    """Extract structured data from raw text with improved accuracy"""
    
    def __init__(self):
        # Enhanced date patterns with context
        self.date_patterns = [
            # ISO format
            (r'\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b', 10),
            # DD/MM/YYYY or MM/DD/YYYY
            (r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b', 8),
            # DD Month YYYY
            (r'\b\d{1,2}[\s-]+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)[\s-]+\d{2,4}\b', 9),
            # Month DD, YYYY
            (r'\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)[\s-]+\d{1,2},?\s+\d{4}\b', 9),
        ]
        
        # Date context keywords
        self.date_contexts = {
            'invoice': ['invoice date', 'date of invoice', 'dated', 'bill date'],
            'transaction': ['transaction date', 'purchase date', 'date of purchase', 'paid on'],
            'due': ['due date', 'payment due', 'due by'],
        }
        
        # Amount patterns with context
        self.amount_contexts = {
            'total': ['total', 'grand total', 'net total', 'amount payable', 'total amount', 'total due', 'balance due'],
            'subtotal': ['subtotal', 'sub total', 'sub-total'],
            'tax': ['tax', 'gst', 'vat', 'cgst', 'sgst', 'igst'],
            'discount': ['discount', 'off', 'savings'],
        }
        
        # Enhanced currency patterns
        self.currency_patterns = [
            # Indian Rupee - various formats
            (r'(?:total|amount|paid|balance|sum)[\s:]*(?:rs\.?|inr|₹)\s*(\d+(?:,\d{2,3})*(?:\.\d{2})?)', 10),
            (r'(?:rs\.?|inr|₹)\s*(\d+(?:,\d{2,3})*(?:\.\d{2})?)', 8),
            (r'(\d+(?:,\d{2,3})*(?:\.\d{2})?)\s*(?:rs\.?|inr|₹)', 7),
            # Dollar
            (r'\$\s*(\d+(?:,\d{3})*(?:\.\d{2})?)', 6),
            # Plain numbers near context words
            (r'(?:total|amount|paid|balance)[\s:]*(\d+(?:,\d{2,3})*(?:\.\d{2})?)', 5),
            # Plain numbers
            (r'\b(\d+(?:,\d{2,3})*(?:\.\d{2})?)\b', 1),
        ]
    
    def extract_dates_with_context(self, text: str) -> Tuple[Optional[datetime], Dict[str, datetime]]:
        """Extract dates with contextual understanding"""
        dates_by_context = {
            'invoice': [],
            'transaction': [],
            'due': [],
            'other': []
        }
        
        # Split text into lines for context analysis
        lines = text.split('\n')
        
        for line_idx, line in enumerate(lines):
            line_lower = line.lower()
            
            # Try each date pattern
            for pattern, priority in self.date_patterns:
                matches = re.finditer(pattern, line, re.IGNORECASE)
                for match in matches:
                    try:
                        date_str = match.group(0)
                        parsed_date = date_parser.parse(date_str, fuzzy=True, dayfirst=True)
                        
                        # Skip unrealistic dates
                        if parsed_date.year < 2000 or parsed_date.year > 2030:
                            continue
                        
                        # Determine context
                        context_type = 'other'
                        for ctx_type, keywords in self.date_contexts.items():
                            if any(kw in line_lower for kw in keywords):
                                context_type = ctx_type
                                break
                        
                        dates_by_context[context_type].append({
                            'date': parsed_date,
                            'priority': priority,
                            'context': context_type,
                            'line': line.strip()
                        })
                    except Exception:
                        continue
        
        # Select primary date (prefer invoice/transaction dates)
        primary_date = None
        for context in ['invoice', 'transaction', 'other', 'due']:
            if dates_by_context[context]:
                # Sort by priority and recency
                dates_by_context[context].sort(key=lambda x: (-x['priority'], -x['date'].timestamp()))
                primary_date = dates_by_context[context][0]['date']
                break
        
        # Convert to simple dict for return
        simplified_dates = {}
        for context, date_list in dates_by_context.items():
            if date_list:
                simplified_dates[context] = date_list[0]['date']
        
        return primary_date, simplified_dates
    
    def extract_amounts_with_context(self, text: str) -> Dict[str, float]:
        """Extract monetary amounts with contextual understanding"""
        amounts_by_context = {
            'total': [],
            'subtotal': [],
            'tax': [],
            'discount': [],
            'other': []
        }
        
        lines = text.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            
            # Determine line context
            line_context = 'other'
            for ctx_type, keywords in self.amount_contexts.items():
                if any(kw in line_lower for kw in keywords):
                    line_context = ctx_type
                    break
            
            # Try each currency pattern
            for pattern, priority in self.currency_patterns:
                matches = re.finditer(pattern, line, re.IGNORECASE)
                for match in matches:
                    try:
                        # Extract numeric value
                        amount_str = match.group(1)
                        amount_str = re.sub(r'[^\d.]', '', amount_str)
                        amount = float(amount_str)
                        
                        # Filter reasonable amounts
                        if 0.01 <= amount <= 10000000:
                            amounts_by_context[line_context].append({
                                'amount': amount,
                                'priority': priority,
                                'line': line.strip()
                            })
                    except (ValueError, IndexError):
                        continue
        
        # Select best amounts for each context
        result = {}
        for context, amount_list in amounts_by_context.items():
            if amount_list:
                # Sort by priority
                amount_list.sort(key=lambda x: -x['priority'])
                result[context] = amount_list[0]['amount']
        
        # If we have both total and subtotal, validate
        if 'total' in result and 'subtotal' in result:
            if result['subtotal'] > result['total']:
                # Swap them - likely mislabeled
                result['total'], result['subtotal'] = result['subtotal'], result['total']
        
        return result
    
    def extract_vendor_name(self, text: str) -> str:
        """Extract vendor/merchant name with improved logic"""
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        
        # Score each line for likelihood of being vendor name
        candidates = []
        
        for i, line in enumerate(lines[:10]):  # Check first 10 lines
            score = 0
            line_clean = re.sub(r'[^\w\s&.-]', '', line)
            
            # Skip if too short or too long
            if len(line_clean) < 3 or len(line_clean) > 80:
                continue
            
            # Skip if mostly numbers
            if sum(c.isdigit() for c in line) / len(line) > 0.5:
                continue
            
            # Skip common headers
            skip_terms = ['invoice', 'receipt', 'bill', 'tax invoice', 'order', 
                         'purchase order', 'quotation', 'estimate', 'statement']
            if any(term in line.lower() for term in skip_terms):
                continue
            
            # Scoring logic
            # Prefer lines near the top
            score += (10 - i) * 2
            
            # Prefer lines with title case
            if line_clean.istitle():
                score += 10
            
            # Prefer lines with all caps (common for business names)
            if line_clean.isupper() and len(line_clean) > 5:
                score += 8
            
            # Prefer lines with business suffixes
            if any(suffix in line_clean for suffix in ['Ltd', 'LLC', 'Inc', 'Pvt', 'Corp', 'Co.']):
                score += 15
            
            # Prefer lines with moderate length
            if 10 <= len(line_clean) <= 40:
                score += 5
            
            # Penalize if contains common non-name words
            penalty_words = ['page', 'date', 'time', 'number', 'original', 'copy', 'duplicate']
            if any(word in line.lower() for word in penalty_words):
                score -= 10
            
            if score > 0:
                candidates.append({
                    'name': line_clean.strip(),
                    'score': score,
                    'position': i
                })
        
        # Return highest scoring candidate
        if candidates:
            candidates.sort(key=lambda x: (-x['score'], x['position']))
            return candidates[0]['name']
        
        return "Unknown Vendor"
    
    def extract_tax_info(self, text: str) -> Tuple[Optional[float], Optional[float]]:
        """Extract tax amount and percentage with better accuracy"""
        tax_amount = None
        tax_percentage = None
        
        # Tax-specific patterns
        patterns = [
            # GST/Tax with amount
            (r'(?:gst|tax|vat|cgst|sgst|igst)[\s:@]*(?:rs\.?|₹|inr)?\s*(\d+(?:,\d{2,3})*(?:\.\d{2})?)', 'amount'),
            # Percentage format
            (r'(?:gst|tax|vat)[\s:@]*(\d+(?:\.\d{1,2})?)\s*%', 'percentage'),
            # @ percentage format
            (r'@\s*(\d+(?:\.\d{1,2})?)\s*%', 'percentage'),
        ]
        
        for pattern, tax_type in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    value_str = re.sub(r'[^\d.]', '', match.group(1))
                    value = float(value_str)
                    
                    if tax_type == 'percentage':
                        if 0 < value <= 100:
                            tax_percentage = value
                    else:  # amount
                        if value < 1:  # Likely percentage written as decimal
                            tax_percentage = value * 100
                        elif value <= 100:  # Could be percentage
                            tax_percentage = value
                        else:  # Definitely amount
                            tax_amount = value
                except (ValueError, IndexError):
                    continue
        
        return tax_amount, tax_percentage
    
    def extract_payment_method(self, text: str) -> str:
        """Extract payment method with better detection"""
        text_lower = text.lower()
        
        # Score each payment method
        scores = {}
        
        payment_keywords = {
            'Card': ['card', 'credit card', 'debit card', 'visa', 'mastercard', 'amex', 'rupay'],
            'UPI': ['upi', 'paytm', 'gpay', 'google pay', 'phonepe', 'bhim', 'upi id', 'upi transaction'],
            'Cash': ['cash', 'paid in cash', 'cash payment'],
            'Net Banking': ['net banking', 'netbanking', 'online banking', 'bank transfer', 'neft', 'rtgs', 'imps'],
            'Wallet': ['wallet', 'mobikwik', 'freecharge', 'paytm wallet', 'amazon pay'],
            'Cheque': ['cheque', 'check', 'cheque no', 'check number'],
        }
        
        for method, keywords in payment_keywords.items():
            score = sum(text_lower.count(kw) for kw in keywords)
            if score > 0:
                scores[method] = score
        
        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]
        
        return 'Other'
    
    def extract_invoice_number(self, text: str) -> Optional[str]:
        """Extract invoice/bill/receipt number"""
        patterns = [
            r'(?:invoice|bill|receipt)\s*(?:no\.?|number|#)[\s:]*([A-Z0-9/-]+)',
            r'(?:inv|rcpt|bill)\s*#[\s:]*([A-Z0-9/-]+)',
            r'(?:invoice|bill|receipt)[\s:]*([A-Z]{2,}\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def extract_contact_info(self, text: str) -> Dict[str, Optional[str]]:
        """Extract contact information"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        phone_pattern = r'(?:\+91|91)?[\s-]?[6-9]\d{9}'
        
        email = None
        phone = None
        
        email_match = re.search(email_pattern, text)
        if email_match:
            email = email_match.group(0)
        
        phone_matches = re.findall(phone_pattern, text)
        if phone_matches:
            # Clean up phone number
            phone = re.sub(r'[^\d+]', '', phone_matches[0])
        
        return {'email': email, 'phone': phone}
    
    def get_extraction_confidence(self, extracted_data: Dict) -> float:
        """Calculate confidence score for extraction"""
        score = 0
        max_score = 100
        
        # Check each field
        if extracted_data.get('date'):
            score += 20
        
        if extracted_data.get('amount'):
            score += 25
        
        if extracted_data.get('vendor') and extracted_data['vendor'] != 'Unknown Vendor':
            score += 20
        
        if extracted_data.get('invoice_number'):
            score += 15
        
        if extracted_data.get('tax_amount') or extracted_data.get('tax_percentage'):
            score += 10
        
        if extracted_data.get('payment_method') and extracted_data['payment_method'] != 'Other':
            score += 10
        
        return min(score, max_score)
    
    def extract_all_data(self, text: str) -> Optional[Dict]:
        """Extract all relevant data from text with improved accuracy"""
        if not text or len(text.strip()) < 10:
            return None
        
        try:
            # Extract dates
            primary_date, all_dates = self.extract_dates_with_context(text)
            
            # Extract amounts
            amounts = self.extract_amounts_with_context(text)
            primary_amount = amounts.get('total') or amounts.get('other')
            
            # Extract other information
            vendor = self.extract_vendor_name(text)
            tax_amount, tax_percentage = self.extract_tax_info(text)
            payment_method = self.extract_payment_method(text)
            invoice_number = self.extract_invoice_number(text)
            contact_info = self.extract_contact_info(text)
            
            extracted_data = {
                'date': primary_date.date() if primary_date else None,
                'all_dates': {k: v.date() for k, v in all_dates.items()},
                'amount': primary_amount,
                'all_amounts': amounts,
                'vendor': vendor,
                'payment_method': payment_method,
                'invoice_number': invoice_number,
                'tax_amount': tax_amount,
                'tax_percentage': tax_percentage,
                'email': contact_info['email'],
                'phone': contact_info['phone'],
                'raw_text': text[:2000],  # Store first 2000 chars
            }
            
            # Calculate confidence
            extracted_data['confidence'] = self.get_extraction_confidence(extracted_data)
            
            return extracted_data
            
        except Exception as e:
            print(f"Error extracting data: {e}")
            traceback.print_exc()
            return None
    
    def validate_extraction(self, extracted_data: Dict) -> List[str]:
        """Validate extracted data and return warnings"""
        warnings = []
        
        if not extracted_data:
            return ['No data extracted']
        
        # Check for missing critical fields
        if not extracted_data.get('date'):
            warnings.append('No date found in document')
        
        if not extracted_data.get('amount'):
            warnings.append('No amount found in document')
        
        if extracted_data.get('vendor') == 'Unknown Vendor':
            warnings.append('Could not identify vendor name')
        
        # Validate logical consistency
        amounts = extracted_data.get('all_amounts', {})
        if 'total' in amounts and 'subtotal' in amounts:
            if amounts['subtotal'] > amounts['total']:
                warnings.append('Subtotal appears greater than total - please verify')
        
        if 'total' in amounts and 'tax' in amounts:
            if amounts['tax'] > amounts['total']:
                warnings.append('Tax amount appears greater than total - please verify')
        
        # Check date validity
        if extracted_data.get('date'):
            date_obj = extracted_data['date']
            if isinstance(date_obj, datetime):
                date_obj = date_obj.date()
            
            current_date = datetime.now().date()
            if date_obj > current_date:
                warnings.append('Document date is in the future')
            
            # Check if date is too old (more than 5 years)
            years_ago = (current_date - date_obj).days / 365
            if years_ago > 5:
                warnings.append(f'Document date is {years_ago:.1f} years old')
        
        # Confidence check
        confidence = extracted_data.get('confidence', 0)
        if confidence < 50:
            warnings.append(f'Low extraction confidence ({confidence}%) - manual review recommended')
        
        return warnings
    
DataExtractor = ImprovedDataExtractor
