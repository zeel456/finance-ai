"""
Finance AI Chatbot Testing Suite
Save as: tests/test_chatbot.py
Run: python tests/test_chatbot.py
"""

import requests
import time
import json
from datetime import datetime
from collections import defaultdict

# Configuration
BASE_URL = 'http://localhost:5000'
TIMEOUT = 30
DELAY_BETWEEN_REQUESTS = 0.3  # seconds

# Test Queries organized by intent
TEST_QUERIES = {
    'total_expense': [
        "What's my total expense?",
        "How much did I spend?",
        "Total spending",
        "Show me all expenses",
        "How much money have I spent?",
        "What's my overall spending?",
        "Calculate all my expenses",
        "Total",
        "All spending",
        "Everything I spent",
        "What's my total expense this month?",
        "Total spending last month",
    ],
    
    'category_expense': [
        "How much did I spend on food?",
        "Food expenses",
        "Show me transportation spending",
        "What did I spend on shopping?",
        "Entertainment costs",
        "Groceries spending",
        "How much on healthcare?",
        "Travel expenses",
        "What about utilities?",
        "Education spending",
        "Dining expenses",
        "Restaurant spending",
        "How much on groceries last month?",
        "This month's food spending",
    ],
    
    'top_spending': [
        "What are my biggest expenses?",
        "Top 5 spending areas",
        "Where do I spend the most?",
        "Show me top spending",
        "Highest expenses",
        "Top categories",
        "Major spending areas",
        "Largest expenses",
        "What costs me the most?",
        "Top 3 expenses",
        "Show top 5",
        "Biggest spending",
    ],
    
    'comparison': [
        "Compare this month vs last month",
        "How does this month compare to last month?",
        "Is my spending increasing?",
        "Show month over month change",
        "Compare this year with last year",
        "Spending difference between months",
        "Am I spending more or less?",
        "Growth in expenses",
        "Compare spending patterns",
        "This month versus last month",
    ],
    
    'average_expense': [
        "What's my average spending?",
        "Average transaction amount",
        "Mean expense",
        "Typical spending",
        "Average daily expense",
        "What do I spend on average?",
        "Average per transaction",
        "Average monthly spending",
    ],
    
    'trend': [
        "What's my spending trend?",
        "Show spending pattern",
        "How is my spending changing?",
        "Display expense trends",
        "Track my spending behavior",
        "Spending over time",
        "Monthly progression",
        "Expense patterns",
    ],
    
    'vendor_analysis': [
        "Which vendors do I use most?",
        "Show me all merchants",
        "Where do I shop frequently?",
        "Top stores I buy from",
        "Favorite vendors",
        "Most used merchants",
        "Vendor breakdown",
    ],
    
    'payment_method': [
        "How much did I pay by card?",
        "Show payment method breakdown",
        "UPI payments",
        "Cash spending",
        "Credit card expenses",
        "How did I pay?",
        "Payment methods used",
    ],
    
    'budget_check': [
        "Am I over budget?",
        "Budget status",
        "How much budget left?",
        "Check my budget",
        "Within budget?",
    ],
    
    'tax_query': [
        "How much tax did I pay?",
        "What's my GST amount?",
        "Show tax deductions",
        "Total taxes paid",
        "Tax breakdown",
    ],
}

# Edge cases and challenging queries
EDGE_CASES = [
    # Ambiguous
    ("Show me everything", None),
    ("What's the total?", 'total_expense'),
    ("Last month", None),
    ("Food", 'category_expense'),
    
    # Typos
    ("totl expence", 'total_expense'),
    ("how much i spended on food?", 'category_expense'),
    ("transporatation cost", 'category_expense'),
    ("top spening", 'top_spending'),
    
    # Natural language
    ("I want to see how much I spent on food", 'category_expense'),
    ("Could you tell me my total expenses?", 'total_expense'),
    ("Can you show me where my money goes?", 'top_spending'),
    ("What did dining out cost me?", 'category_expense'),
]

# Follow-up context tests (must be run in sequence)
CONTEXT_TESTS = [
    {
        'name': 'Category Follow-up',
        'queries': [
            ("How much did I spend on food this month?", 'category_expense'),
            ("What about last month?", 'category_expense'),
            ("And transportation?", 'category_expense'),
        ]
    },
    {
        'name': 'Top Spending Context',
        'queries': [
            ("Show me top 5 spending areas", 'top_spending'),
            ("What about this month only?", 'top_spending'),
            ("Compare with last month", 'comparison'),
        ]
    },
]

class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

class ChatbotTester:
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url
        self.results = defaultdict(list)
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.start_time = None
        
    def test_query(self, query, expected_intent=None, show_response=False):
        """Test a single query"""
        start = time.time()
        
        try:
            response = requests.post(
                f'{self.base_url}/api/query',
                json={'query': query},
                timeout=TIMEOUT
            )
            elapsed = time.time() - start
            
            if response.status_code != 200:
                return self._create_result(False, query, expected_intent, 
                                          error=f"HTTP {response.status_code}")
            
            data = response.json()
            
            if not data.get('success'):
                return self._create_result(False, query, expected_intent,
                                          error=data.get('error', 'Unknown error'))
            
            result = data['result']
            intent = result.get('intent', 'unknown')
            confidence = result.get('confidence', 0)
            response_text = result.get('response', '')
            
            # Check if intent matches expected
            is_correct = (expected_intent is None or 
                         intent == expected_intent or
                         confidence < 40)  # Low confidence is acceptable for ambiguous
            
            # Print result
            status = f"{Colors.GREEN}✅{Colors.END}" if is_correct else f"{Colors.RED}❌{Colors.END}"
            query_short = query[:50] + '...' if len(query) > 50 else query
            
            print(f"{status} '{query_short}'")
            print(f"   → Intent: {Colors.CYAN}{intent}{Colors.END} "
                  f"(Confidence: {confidence:.1f}%) "
                  f"[{elapsed:.2f}s]")
            
            if expected_intent and intent != expected_intent and confidence >= 40:
                print(f"   {Colors.RED}Expected: {expected_intent}{Colors.END}")
            
            if show_response:
                response_short = response_text[:100] + '...' if len(response_text) > 100 else response_text
                print(f"   Response: {response_short}")
            
            return self._create_result(is_correct, query, expected_intent,
                                      intent, confidence, elapsed, response_text)
            
        except requests.exceptions.Timeout:
            return self._create_result(False, query, expected_intent,
                                      error='Request timeout')
        except requests.exceptions.ConnectionError:
            return self._create_result(False, query, expected_intent,
                                      error='Connection failed - Is server running?')
        except Exception as e:
            return self._create_result(False, query, expected_intent,
                                      error=str(e))
    
    def _create_result(self, is_correct, query, expected_intent, 
                      intent=None, confidence=0, elapsed=0, response='', error=None):
        """Create a standardized result dictionary"""
        return {
            'correct': is_correct,
            'query': query,
            'expected_intent': expected_intent,
            'detected_intent': intent,
            'confidence': confidence,
            'response_time': elapsed,
            'response': response,
            'error': error
        }
    
    def test_intent_group(self, intent_name, queries):
        """Test all queries for a specific intent"""
        print(f"\n{Colors.BOLD}{'='*70}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}Testing Intent: {intent_name.upper()}{Colors.END}")
        print(f"{Colors.BOLD}{'='*70}{Colors.END}\n")
        
        results = []
        for query in queries:
            result = self.test_query(query, intent_name)
            results.append(result)
            self.results[intent_name].append(result)
            
            self.total_tests += 1
            if result['correct']:
                self.passed_tests += 1
            else:
                self.failed_tests += 1
            
            time.sleep(DELAY_BETWEEN_REQUESTS)
        
        # Print statistics for this intent
        self._print_intent_stats(intent_name, results)
        
        return results
    
    def test_edge_cases(self):
        """Test edge cases and ambiguous queries"""
        print(f"\n{Colors.BOLD}{'='*70}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.YELLOW}Testing Edge Cases & Ambiguous Queries{Colors.END}")
        print(f"{Colors.BOLD}{'='*70}{Colors.END}\n")
        
        results = []
        for query, expected_intent in EDGE_CASES:
            result = self.test_query(query, expected_intent)
            results.append(result)
            self.results['edge_cases'].append(result)
            
            self.total_tests += 1
            if result['correct']:
                self.passed_tests += 1
            else:
                self.failed_tests += 1
            
            time.sleep(DELAY_BETWEEN_REQUESTS)
        
        self._print_intent_stats('Edge Cases', results)
        return results
    
    def test_context_sequences(self):
        """Test context-aware follow-up queries"""
        print(f"\n{Colors.BOLD}{'='*70}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.YELLOW}Testing Context & Follow-ups{Colors.END}")
        print(f"{Colors.BOLD}{'='*70}{Colors.END}\n")
        
        for test_group in CONTEXT_TESTS:
            print(f"\n{Colors.CYAN}Sequence: {test_group['name']}{Colors.END}")
            print(f"{'-'*50}")
            
            for i, (query, expected_intent) in enumerate(test_group['queries'], 1):
                print(f"\n{Colors.BOLD}Step {i}:{Colors.END}")
                result = self.test_query(query, expected_intent, show_response=True)
                self.results['context_tests'].append(result)
                
                self.total_tests += 1
                if result['correct']:
                    self.passed_tests += 1
                else:
                    self.failed_tests += 1
                
                time.sleep(DELAY_BETWEEN_REQUESTS * 2)  # Longer delay for context
    
    def _print_intent_stats(self, intent_name, results):
        """Print statistics for an intent group"""
        correct = sum(1 for r in results if r['correct'])
        total = len(results)
        accuracy = (correct / total * 100) if total > 0 else 0
        
        avg_confidence = sum(r['confidence'] for r in results if r['confidence']) / total if total > 0 else 0
        avg_time = sum(r['response_time'] for r in results if r['response_time']) / total if total > 0 else 0
        
        print(f"\n{Colors.BOLD}Statistics:{Colors.END}")
        print(f"  Accuracy: {correct}/{total} ({accuracy:.1f}%)")
        print(f"  Avg Confidence: {avg_confidence:.1f}%")
        print(f"  Avg Response Time: {avg_time:.2f}s")
        
        # Show failed queries
        failed = [r for r in results if not r['correct']]
        if failed:
            print(f"\n  {Colors.RED}Failed Queries:{Colors.END}")
            for r in failed[:5]:  # Show first 5 failures
                print(f"    • '{r['query'][:50]}...'")
                if r['error']:
                    print(f"      Error: {r['error']}")
                elif r['detected_intent']:
                    print(f"      Got: {r['detected_intent']} (Expected: {r['expected_intent']})")
    
    def generate_report(self):
        """Generate final test report"""
        elapsed = time.time() - self.start_time
        
        print(f"\n{Colors.BOLD}{'='*70}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.GREEN}FINAL TEST REPORT{Colors.END}")
        print(f"{Colors.BOLD}{'='*70}{Colors.END}\n")
        
        print(f"{Colors.BOLD}Overall Results:{Colors.END}")
        print(f"  Total Tests: {self.total_tests}")
        print(f"  {Colors.GREEN}Passed: {self.passed_tests}{Colors.END}")
        print(f"  {Colors.RED}Failed: {self.failed_tests}{Colors.END}")
        
        overall_accuracy = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        print(f"  {Colors.BOLD}Overall Accuracy: {overall_accuracy:.1f}%{Colors.END}")
        print(f"  Total Time: {elapsed:.1f}s")
        
        # Intent-wise breakdown
        print(f"\n{Colors.BOLD}Intent-wise Breakdown:{Colors.END}")
        for intent, results in self.results.items():
            if results:
                correct = sum(1 for r in results if r['correct'])
                total = len(results)
                accuracy = (correct / total * 100) if total > 0 else 0
                avg_conf = sum(r['confidence'] for r in results if r['confidence']) / total if total > 0 else 0
                
                status = f"{Colors.GREEN}✓{Colors.END}" if accuracy >= 70 else f"{Colors.RED}✗{Colors.END}"
                print(f"  {status} {intent:20s} → {correct:2d}/{total:2d} ({accuracy:5.1f}%) | Avg Conf: {avg_conf:5.1f}%")
        
        # Save results to file
        self._save_results()
        
        print(f"\n{Colors.CYAN}📄 Detailed results saved to: test_results.json{Colors.END}")
        print(f"{Colors.GREEN}✅ Testing Complete!{Colors.END}\n")
    
    def _save_results(self):
        """Save detailed results to JSON file"""
        output = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_tests': self.total_tests,
                'passed': self.passed_tests,
                'failed': self.failed_tests,
                'accuracy': (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
            },
            'results_by_intent': {}
        }
        
        for intent, results in self.results.items():
            output['results_by_intent'][intent] = {
                'total': len(results),
                'correct': sum(1 for r in results if r['correct']),
                'accuracy': (sum(1 for r in results if r['correct']) / len(results) * 100) if results else 0,
                'queries': [
                    {
                        'query': r['query'],
                        'expected': r['expected_intent'],
                        'detected': r['detected_intent'],
                        'confidence': r['confidence'],
                        'correct': r['correct'],
                        'error': r['error']
                    }
                    for r in results
                ]
            }
        
        with open('test_results.json', 'w') as f:
            json.dump(output, f, indent=2)
    
    def run_all_tests(self):
        """Run all tests"""
        self.start_time = time.time()
        
        print(f"\n{Colors.BOLD}{Colors.BLUE}🧪 Starting Chatbot Testing Suite{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}\n")
        print(f"Base URL: {self.base_url}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Test each intent group
        for intent_name, queries in TEST_QUERIES.items():
            self.test_intent_group(intent_name, queries)
        
        # Test edge cases
        self.test_edge_cases()
        
        # Test context sequences
        self.test_context_sequences()
        
        # Generate final report
        self.generate_report()

def main():
    """Main function"""
    print(f"\n{Colors.BOLD}Finance AI Chatbot - Testing Suite{Colors.END}")
    print(f"{'='*70}\n")
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print(f"{Colors.GREEN}✓ Server is running{Colors.END}\n")
        else:
            print(f"{Colors.RED}✗ Server returned status {response.status_code}{Colors.END}")
            return
    except requests.exceptions.ConnectionError:
        print(f"{Colors.RED}✗ Cannot connect to server at {BASE_URL}{Colors.END}")
        print(f"{Colors.YELLOW}⚠ Make sure Flask server is running: python app.py{Colors.END}\n")
        return
    except Exception as e:
        print(f"{Colors.RED}✗ Error: {str(e)}{Colors.END}\n")
        return
    
    # Run tests
    tester = ChatbotTester(BASE_URL)
    tester.run_all_tests()

if __name__ == '__main__':
    main()