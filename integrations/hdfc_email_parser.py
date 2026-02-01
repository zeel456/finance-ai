"""
HDFC Bank Email Parser - Updated for Real HDFC Email Format
Automatically syncs transactions from HDFC email alerts
"""

import re
import imaplib
import email
from email.header import decode_header
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Optional, Tuple
import hashlib

class HDFCEmailParser:
    """
    Parse HDFC Bank transaction alert emails
    Updated to match actual HDFC email format
    """
    
    # HDFC email senders
    HDFC_SENDERS = [
        'alerts@hdfcbank.net',
        'alertshdfcbank.net',
        'alerts@hdfcbank.com',
        'instaalerts@hdfcbank.net'
    ]
    
    # Updated patterns based on actual HDFC email format
    PATTERNS = {
        'amount': [
            r'Rs\.?\s*(\d+(?:,\d+)*(?:\.\d{2})?)\s+has been (?:debited|credited)',
            r'Rs\s+(\d+(?:,\d+)*(?:\.\d{2})?)',
            r'INR\s+(\d+(?:,\d+)*(?:\.\d{2})?)'
        ],
        'type': [
            r'has been (debited|credited)',
            r'(debit|credit)'
        ],
        'vendor': [
            r'to\s+([A-Z][A-Z0-9\s@\.\-]+?)(?:\s+on\s+\d{2}-\d{2}-\d{2})',
            r'at\s+([A-Z][A-Z0-9\s@\.\-]+?)(?:\s+on\s+\d{2}-\d{2}-\d{2})',
            r'from\s+([A-Z][A-Z0-9\s@\.\-]+?)(?:\s+on\s+\d{2}-\d{2}-\d{2})',
            r'to\s+VPA\s+([a-zA-Z0-9@\.\-]+)',
        ],
        'date': [
            r'on\s+(\d{2}-\d{2}-\d{2})',
            r'on\s+(\d{2}-\w{3}-\d{2,4})',
            r'on\s+(\d{2}/\d{2}/\d{4})'
        ],
        'account': [
            r'from account\s+(\d{4})',
            r'account\s+(\d{4})',
            r'A/c\s+(?:No\.?)?\s*(\d{4})'
        ],
        'reference': [
            r'reference number is\s+(\d+)',
            r'UPI transaction reference number is\s+(\d+)',
            r'Ref[:\s]+(\w+)',
            r'UTR:\s*(\w+)'
        ],
        'payment_mode': [
            r'Your (UPI) transaction',
            r'Info:\s*(UPI|POS|ATM|NEFT|IMPS|Card|Online)',
            r'(Card|Netbanking|ATM)\s+transaction'
        ]
    }
    
    def __init__(self, email_address: str, app_password: str):
        """
        Initialize HDFC email parser
        
        Args:
            email_address: Your Gmail/email address
            app_password: App-specific password (not regular password)
        """
        self.email_address = email_address
        self.app_password = app_password
        self.imap_server = self._detect_imap_server(email_address)
        self.connection = None
        
    def _detect_imap_server(self, email_address: str) -> str:
        """Detect IMAP server from email"""
        if 'gmail' in email_address:
            return 'imap.gmail.com'
        elif 'outlook' in email_address or 'hotmail' in email_address:
            return 'outlook.office365.com'
        elif 'yahoo' in email_address:
            return 'imap.mail.yahoo.com'
        else:
            return 'imap.gmail.com'  # Default
    
    def connect(self) -> bool:
        """Connect to email server"""
        try:
            print(f"🔗 Connecting to {self.imap_server}...")
            self.connection = imaplib.IMAP4_SSL(self.imap_server)
            self.connection.login(self.email_address, self.app_password)
            print("✅ Email connected successfully!")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from email server"""
        if self.connection:
            try:
                self.connection.logout()
                print("✅ Disconnected from email")
            except:
                pass
    
    def fetch_hdfc_emails(self, days_back: int = 30) -> List[Dict]:
        """
        Fetch HDFC transaction emails
        
        Args:
            days_back: How many days to look back
            
        Returns:
            List of parsed transactions
        """
        if not self.connection:
            if not self.connect():
                return []
        
        try:
            # Select inbox
            self.connection.select('INBOX')
            
            # Calculate date range
            since_date = (datetime.now() - timedelta(days=days_back)).strftime("%d-%b-%Y")
            
            # Search for HDFC emails (try multiple sender addresses)
            search_queries = [
                f'(SINCE {since_date} FROM "alerts@hdfcbank.net")',
                f'(SINCE {since_date} FROM "instaalerts@hdfcbank.net")',
                f'(SINCE {since_date} SUBJECT "HDFC Bank")'
            ]
            
            email_ids = []
            
            for query in search_queries:
                try:
                    status, messages = self.connection.search(None, query)
                    if status == 'OK' and messages[0]:
                        email_ids.extend(messages[0].split())
                except:
                    continue
            
            # Remove duplicates
            email_ids = list(set(email_ids))
            
            print(f"📧 Found {len(email_ids)} HDFC emails")
            
            if not email_ids:
                print("⚠️  No HDFC emails found. Check:")
                print("   1. HDFC sends alerts to this email")
                print("   2. Emails aren't in spam")
                print("   3. Date range is correct")
                return []
            
            transactions = []
            
            for email_id in email_ids:
                # Fetch email
                status, msg_data = self.connection.fetch(email_id, '(RFC822)')
                
                if status != 'OK':
                    continue
                
                # Parse email
                email_body = msg_data[0][1]
                email_message = email.message_from_bytes(email_body)
                
                # Extract transaction
                transaction = self._parse_email(email_message)
                
                if transaction:
                    transactions.append(transaction)
            
            print(f"✅ Parsed {len(transactions)} transactions")
            return transactions
            
        except Exception as e:
            print(f"❌ Error fetching emails: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _parse_email(self, email_message) -> Optional[Dict]:
        """Parse individual HDFC email"""
        try:
            # Get subject
            subject = self._decode_header(email_message['Subject'])
            
            # Get email body
            body = self._get_email_body(email_message)
            
            if not body:
                return None
            
            # Combine subject and body for parsing
            full_text = f"{subject} {body}"
            
            # Check if it's a transaction alert
            if not any(keyword in full_text.lower() for keyword in ['debited', 'credited', 'transaction']):
                return None
            
            print(f"\n📄 Parsing: {subject[:60]}...")
            
            # Extract transaction details
            transaction = {
                'source': 'hdfc_email',
                'email_subject': subject,
                'raw_text': body
            }
            
            # Extract amount
            amount = self._extract_amount(full_text)
            if not amount:
                print("   ⚠️  No amount found")
                return None
            transaction['amount'] = amount
            
            # Extract transaction type (debit/credit)
            trans_type = self._extract_type(full_text)
            transaction['type'] = trans_type
            transaction['transaction_type'] = trans_type
            
            # Extract vendor/merchant
            vendor = self._extract_vendor(full_text)
            transaction['vendor_name'] = vendor or 'HDFC Transaction'
            
            # Extract date
            trans_date = self._extract_date(full_text, email_message)
            transaction['transaction_date'] = trans_date
            
            # Extract account number
            account = self._extract_account(full_text)
            transaction['account_number'] = account
            
            # Extract reference number
            reference = self._extract_reference(full_text)
            transaction['reference_number'] = reference
            
            # Extract payment method
            payment_mode = self._extract_payment_mode(full_text)
            transaction['payment_method'] = payment_mode
            
            # Generate unique hash for deduplication
            transaction['transaction_hash'] = self._generate_hash(transaction)
            
            print(f"   ✅ ₹{amount} - {vendor} - {trans_date} - {payment_mode}")
            
            return transaction
            
        except Exception as e:
            print(f"   ❌ Parse error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _decode_header(self, header: str) -> str:
        """Decode email header"""
        if not header:
            return ""
        try:
            decoded = decode_header(header)
            if decoded and decoded[0][0]:
                if isinstance(decoded[0][0], bytes):
                    return decoded[0][0].decode(decoded[0][1] or 'utf-8')
                return str(decoded[0][0])
        except:
            pass
        return str(header) if header else ""
    
    def _get_email_body(self, email_message) -> str:
        """Extract email body text"""
        body = ""
        
        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain" or content_type == "text/html":
                    try:
                        payload = part.get_payload(decode=True)
                        if payload:
                            body = payload.decode('utf-8', errors='ignore')
                            if body:
                                break
                    except:
                        continue
        else:
            try:
                payload = email_message.get_payload(decode=True)
                if payload:
                    body = payload.decode('utf-8', errors='ignore')
            except:
                pass
        
        return body
    
    def _extract_amount(self, text: str) -> Optional[float]:
        """Extract transaction amount"""
        for pattern in self.PATTERNS['amount']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '')
                try:
                    return float(amount_str)
                except:
                    continue
        return None
    
    def _extract_type(self, text: str) -> str:
        """Extract transaction type (debit/credit)"""
        for pattern in self.PATTERNS['type']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                trans_type = match.group(1).lower()
                return 'debit' if 'debit' in trans_type else 'credit'
        
        # Default to debit if unclear
        return 'debit'
    
    def _extract_vendor(self, text: str) -> Optional[str]:
        """Extract vendor/merchant name"""
        for pattern in self.PATTERNS['vendor']:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                vendor = match.group(1).strip()
                # Clean up vendor name
                vendor = re.sub(r'\s+', ' ', vendor)
                vendor = vendor.strip('.,;:-')
                
                # Remove email-like suffixes
                vendor = re.sub(r'@.*', '', vendor)
                
                # Minimum length check
                if len(vendor) > 3:
                    return vendor
        return None
    
    def _extract_date(self, text: str, email_message) -> str:
        """Extract transaction date"""
        for pattern in self.PATTERNS['date']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                try:
                    # Try DD-MM-YY format
                    if '-' in date_str and len(date_str.split('-')[0]) == 2:
                        parts = date_str.split('-')
                        if len(parts) == 3:
                            day, month, year = parts
                            # Convert 2-digit year to 4-digit
                            if len(year) == 2:
                                year = '20' + year
                            dt = datetime(int(year), int(month), int(day))
                            return dt.strftime('%Y-%m-%d')
                except:
                    continue
        
        # Fallback to email date
        try:
            email_date = email.utils.parsedate_to_datetime(email_message['Date'])
            return email_date.strftime('%Y-%m-%d')
        except:
            return datetime.now().strftime('%Y-%m-%d')
    
    def _extract_account(self, text: str) -> Optional[str]:
        """Extract account number"""
        for pattern in self.PATTERNS['account']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def _extract_reference(self, text: str) -> Optional[str]:
        """Extract reference/transaction ID"""
        for pattern in self.PATTERNS['reference']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def _extract_payment_mode(self, text: str) -> str:
        """Extract payment method"""
        for pattern in self.PATTERNS['payment_mode']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                mode = match.group(1).upper()
                mode_map = {
                    'UPI': 'UPI',
                    'POS': 'Card',
                    'ATM': 'ATM',
                    'NEFT': 'Bank Transfer',
                    'IMPS': 'Bank Transfer',
                    'CARD': 'Card',
                    'ONLINE': 'Online Banking',
                    'NETBANKING': 'Online Banking'
                }
                return mode_map.get(mode, mode)
        
        # Check for UPI-specific indicators
        if 'upi' in text.lower() or 'vpa' in text.lower():
            return 'UPI'
        
        return 'Other'
    
    def _generate_hash(self, transaction: Dict) -> str:
        """Generate unique hash for deduplication"""
        hash_string = f"{transaction.get('amount', '')}_{transaction.get('vendor_name', '')}_{transaction.get('transaction_date', '')}_{transaction.get('reference_number', '')}"
        return hashlib.md5(hash_string.encode()).hexdigest()


# ============================================================================
# TRANSACTION SYNC ENGINE
# ============================================================================

class HDFCTransactionSync:
    """Sync HDFC email transactions to database"""
    
    def __init__(self, db_session, category_predictor=None):
        self.db = db_session
        self.category_predictor = category_predictor
        
    def sync_transactions(self, parsed_transactions: List[Dict]) -> Dict:
        """
        Sync parsed transactions to database
        
        Returns:
            Summary of sync operation
        """
        from models.transaction import Transaction
        from models.category import Category
        
        stats = {
            'total': len(parsed_transactions),
            'added': 0,
            'duplicates': 0,
            'errors': 0,
            'error_details': []
        }
        
        print(f"\n🔄 Syncing {stats['total']} transactions...")
        
        for trans_data in parsed_transactions:
            try:
                # Check for duplicates
                if self._is_duplicate(trans_data):
                    stats['duplicates'] += 1
                    print(f"   ⏭️  Skipped duplicate: {trans_data.get('vendor_name')}")
                    continue
                
                # Predict category using AI
                category_id = self._predict_category(trans_data)
                
                # Create transaction
                transaction = Transaction(
                    transaction_date=datetime.strptime(trans_data['transaction_date'], '%Y-%m-%d').date(),
                    amount=trans_data['amount'],
                    currency='INR',
                    vendor_name=trans_data['vendor_name'],
                    description=f"HDFC: {trans_data.get('email_subject', 'Auto-imported')[:100]}",
                    category_id=category_id,
                    payment_method=trans_data.get('payment_method', 'Other'),
                    reference_number=trans_data.get('reference_number'),
                    account_number=trans_data.get('account_number'),
                    transaction_hash=trans_data.get('transaction_hash'),
                    transaction_type=trans_data.get('transaction_type', 'debit'),
                    source='hdfc_email'
                )
                
                self.db.add(transaction)
                stats['added'] += 1
                
                print(f"   ✅ Added: ₹{trans_data['amount']} - {trans_data['vendor_name']}")
                
            except Exception as e:
                stats['errors'] += 1
                error_msg = f"{trans_data.get('vendor_name', 'Unknown')}: {str(e)}"
                stats['error_details'].append(error_msg)
                print(f"   ❌ Error: {error_msg}")
                continue
        
        # Commit all transactions
        try:
            self.db.commit()
            print(f"\n✅ Sync complete!")
            print(f"   Added: {stats['added']}")
            print(f"   Duplicates: {stats['duplicates']}")
            print(f"   Errors: {stats['errors']}")
            
            # Auto-sync budgets
            if stats['added'] > 0:
                try:
                    from utils.budget_utils import BudgetUtils
                    print("\n🔄 Syncing budgets...")
                    updated = BudgetUtils.sync_all_budgets()
                    print(f"✅ Updated {updated} budgets")
                except Exception as e:
                    print(f"⚠️  Budget sync skipped: {e}")
            
        except Exception as e:
            self.db.rollback()
            print(f"❌ Database error: {e}")
            stats['errors'] += stats['added']
            stats['added'] = 0
        
        return stats
    
    def _is_duplicate(self, trans_data: Dict) -> bool:
        """Check if transaction already exists"""
        from models.transaction import Transaction
        
        trans_hash = trans_data.get('transaction_hash')
        
        if trans_hash:
            existing = Transaction.query.filter_by(transaction_hash=trans_hash).first()
            if existing:
                return True
        
        # Fallback: check by amount, vendor, date
        try:
            existing = Transaction.query.filter_by(
                amount=trans_data['amount'],
                vendor_name=trans_data['vendor_name'],
                transaction_date=datetime.strptime(trans_data['transaction_date'], '%Y-%m-%d').date()
            ).first()
            
            return existing is not None
        except:
            return False
    
    def _predict_category(self, trans_data: Dict) -> int:
        """Predict category using enhanced smart categorizer"""
        
        try:
            from utils.smart_categorizer import SmartCategorizer, CategoryMapper
            
            # Enhance transaction data
            enhanced = SmartCategorizer.enhance_transaction(trans_data)
            
            # Get predicted category name
            category_name = enhanced.get('predicted_category', 'Uncategorized')
            confidence = enhanced.get('category_confidence', 0)
            
            # Update vendor name with cleaned version
            trans_data['vendor_name'] = enhanced.get('vendor_name', trans_data['vendor_name'])
            
            print(f"      📊 Category: {category_name} (confidence: {confidence:.0f}%)")
            
            # Get category ID from database
            category_id = CategoryMapper.get_category_id(category_name, self.db)
            
            return category_id
            
        except Exception as e:
            print(f"      ⚠️  Categorization error: {e}")
            # Fallback to simple categorization
            from models.category import Category
            
            vendor_lower = trans_data.get('vendor_name', '').lower()
            
            # Quick fallback rules
            if any(kw in vendor_lower for kw in ['hospital', 'clinic', 'medical', 'doctor']):
                cat = Category.query.filter_by(name='Healthcare').first()
                if cat:
                    return cat.id
            
            if any(kw in vendor_lower for kw in ['swiggy', 'zomato', 'food', 'sweets']):
                cat = Category.query.filter_by(name='Food & Dining').first()
                if cat:
                    return cat.id
            
            # Default: Uncategorized
            cat = Category.query.filter_by(name='Uncategorized').first()
            return cat.id if cat else 1