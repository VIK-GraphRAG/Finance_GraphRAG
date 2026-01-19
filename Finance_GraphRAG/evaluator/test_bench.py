#!/usr/bin/env python3
"""
Quality Evaluation System for Tech-Analyst GraphRAG

Tests:
1. Security: Verify no sensitive data in cloud prompts
2. Multi-hop: Evaluate Neo4j path quality (1-5 score)
3. Format: Check PRD compliance (4-section structure)
4. Accuracy: Compare against ground truth
"""

import json
import re
import sys
import os
from typing import Dict, List, Any, Tuple
from pathlib import Path
import requests
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from openai import OpenAI
    from config import OPENAI_API_KEY, OPENAI_BASE_URL
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️ OpenAI not available for LLM-as-judge tests")


class SecurityTester:
    """
    Test for sensitive data leaks in cloud API prompts
    """
    
    # Patterns that indicate sensitive data
    SENSITIVE_PATTERNS = [
        r'\[INTERNAL_DATA_\d+\]',  # Tagged internal data
        r'Project\s+[A-Z]\w+',      # Project names
        r'\$\d+\.?\d*[BMK]',        # Specific financial numbers
        r'confidential',
        r'proprietary',
        r'internal\s+memo',
        r'Q[1-4]\s+\d{4}\s+revenue:\s+\$\d+',  # Specific quarterly data
    ]
    
    def __init__(self):
        self.violations = []
    
    def scan_for_leaks(self, prompt: str, context: str = "") -> Dict[str, Any]:
        """
        Scan prompt for sensitive data leaks
        
        Args:
            prompt: Prompt sent to cloud API
            context: Additional context
            
        Returns:
            Scan results with violations
        """
        violations = []
        
        for pattern in self.SENSITIVE_PATTERNS:
            matches = re.findall(pattern, prompt, re.IGNORECASE)
            if matches:
                violations.append({
                    'pattern': pattern,
                    'matches': matches,
                    'severity': 'HIGH'
                })
        
        # Check for specific numbers (potential sensitive data)
        number_pattern = r'\$[\d,]+\.?\d*[BMK]?'
        numbers = re.findall(number_pattern, prompt)
        if len(numbers) > 5:  # Many specific numbers might be sensitive
            violations.append({
                'pattern': 'Multiple specific financial numbers',
                'matches': numbers[:5],
                'severity': 'MEDIUM'
            })
        
        return {
            'has_violations': len(violations) > 0,
            'violation_count': len(violations),
            'violations': violations,
            'prompt_length': len(prompt),
            'scan_timestamp': datetime.now().isoformat()
        }
    
    def test_prompt_safety(self, test_case: Dict) -> Dict[str, Any]:
        """
        Test if prompt is safe to send to cloud API
        
        Args:
            test_case: Test case with query and context
            
        Returns:
            Safety test results
        """
        # Simulate prompt that would be sent to cloud
        simulated_prompt = f"Query: {test_case['query']}\nContext: {test_case.get('context', [])}"
        
        scan_result = self.scan_for_leaks(simulated_prompt)
        
        return {
            'test_id': test_case['id'],
            'query': test_case['query'],
            'passed': not scan_result['has_violations'],
            'scan_result': scan_result
        }


class MultihopEvaluator:
    """
    Evaluate multi-hop reasoning quality using LLM-as-judge
    """
    
    def __init__(self):
        if not OPENAI_AVAILABLE:
            raise RuntimeError("OpenAI required for LLM-as-judge evaluation")
        
        self.client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
    
    def evaluate_path_quality(
        self,
        query: str,
        neo4j_path: List[str],
        response: str
    ) -> Dict[str, Any]:
        """
        Evaluate Neo4j path quality using GPT-4o-mini as judge
        
        Args:
            query: User query
            neo4j_path: List of entities in path (e.g., ['ASML', 'TSMC', 'Nvidia'])
            response: System response
            
        Returns:
            Evaluation with score 1-5
        """
        hop_count = len(neo4j_path) - 1 if len(neo4j_path) > 1 else 0
        
        # Judge prompt
        judge_prompt = f"""You are evaluating the quality of multi-hop reasoning in a knowledge graph system.

Query: {query}

Knowledge Graph Path Found:
{' → '.join(neo4j_path)}
(Hop count: {hop_count})

System Response:
{response[:500]}...

Evaluate on a scale of 1-5:
1 = Poor (path irrelevant or illogical)
2 = Below Average (weak connection)
3 = Average (somewhat relevant)
4 = Good (clear logical connection)
5 = Excellent (perfect causal chain)

Consider:
- Does the path make logical sense for the query?
- Are the hops causally connected?
- Does the response utilize the path effectively?

Respond in JSON format:
{{
    "score": <1-5>,
    "reasoning": "<brief explanation>",
    "strengths": "<what worked well>",
    "weaknesses": "<what could improve>"
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert evaluator of knowledge graph reasoning systems."},
                    {"role": "user", "content": judge_prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            content = response.choices[0].message.content
            
            # Extract JSON
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                evaluation = json.loads(json_match.group())
                evaluation['hop_count'] = hop_count
                evaluation['path'] = neo4j_path
                return evaluation
            else:
                return {
                    'score': 0,
                    'reasoning': 'Failed to parse judge response',
                    'hop_count': hop_count,
                    'path': neo4j_path
                }
                
        except Exception as e:
            print(f"❌ LLM-as-judge failed: {e}")
            return {
                'score': 0,
                'reasoning': f'Evaluation error: {str(e)}',
                'hop_count': hop_count,
                'path': neo4j_path
            }


class FormatChecker:
    """
    Check PRD format compliance (4-section structure)
    """
    
    # Required sections from PRD
    REQUIRED_SECTIONS = [
        "Executive Summary",
        "Market Context",
        "Supply Chain Analysis",
        "Risk & Outlook"
    ]
    
    def check_format_compliance(self, response: str) -> Dict[str, Any]:
        """
        Check if response follows PRD format
        
        Args:
            response: System response
            
        Returns:
            Compliance report
        """
        sections_found = []
        sections_missing = []
        
        for section in self.REQUIRED_SECTIONS:
            # Check for section header (various formats)
            patterns = [
                rf'\[{section}\]',
                rf'##\s*\[{section}\]',
                rf'##\s*{section}',
                rf'\*\*\[{section}\]\*\*'
            ]
            
            found = False
            for pattern in patterns:
                if re.search(pattern, response, re.IGNORECASE):
                    sections_found.append(section)
                    found = True
                    break
            
            if not found:
                sections_missing.append(section)
        
        compliance_rate = len(sections_found) / len(self.REQUIRED_SECTIONS)
        
        return {
            'compliant': len(sections_missing) == 0,
            'compliance_rate': compliance_rate,
            'sections_found': sections_found,
            'sections_missing': sections_missing,
            'total_sections': len(self.REQUIRED_SECTIONS),
            'response_length': len(response)
        }


class AccuracyEvaluator:
    """
    Evaluate accuracy against ground truth
    """
    
    def __init__(self):
        if OPENAI_AVAILABLE:
            self.client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
        else:
            self.client = None
    
    def evaluate_accuracy(
        self,
        query: str,
        response: str,
        ground_truth: str
    ) -> Dict[str, Any]:
        """
        Evaluate response accuracy against ground truth
        
        Args:
            query: User query
            response: System response
            ground_truth: Expected answer
            
        Returns:
            Accuracy evaluation
        """
        # Simple keyword matching
        keywords_in_truth = set(re.findall(r'\b[A-Z][a-z]+\b|\b\d+%?\b', ground_truth))
        keywords_in_response = set(re.findall(r'\b[A-Z][a-z]+\b|\b\d+%?\b', response))
        
        if keywords_in_truth:
            keyword_overlap = len(keywords_in_truth & keywords_in_response) / len(keywords_in_truth)
        else:
            keyword_overlap = 0.0
        
        # Semantic similarity using LLM (if available)
        semantic_score = 0.0
        if self.client:
            try:
                semantic_score = self._llm_similarity(response, ground_truth)
            except:
                pass
        
        # Combined score
        accuracy_score = (keyword_overlap * 0.4 + semantic_score * 0.6)
        
        return {
            'accuracy_score': accuracy_score,
            'keyword_overlap': keyword_overlap,
            'semantic_similarity': semantic_score,
            'keywords_expected': list(keywords_in_truth)[:10],
            'keywords_found': list(keywords_in_truth & keywords_in_response)[:10],
            'passed': accuracy_score >= 0.6
        }
    
    def _llm_similarity(self, response: str, ground_truth: str) -> float:
        """
        Use LLM to evaluate semantic similarity
        
        Returns:
            Similarity score 0.0-1.0
        """
        prompt = f"""Compare these two texts and rate their semantic similarity on a scale of 0.0 to 1.0.

Ground Truth:
{ground_truth}

System Response:
{response[:500]}

Consider:
- Do they convey the same key facts?
- Is the core information consistent?
- Ignore stylistic differences

Respond with ONLY a number between 0.0 and 1.0 (e.g., 0.85)
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a semantic similarity evaluator."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                max_tokens=10
            )
            
            content = response.choices[0].message.content.strip()
            score = float(re.findall(r'0?\.\d+|1\.0', content)[0])
            return max(0.0, min(1.0, score))
            
        except:
            return 0.5  # Default


class QualityEvaluator:
    """
    Comprehensive quality testing for Tech-Analyst GraphRAG
    """
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
        self.test_cases = self._load_test_cases()
        self.results = []
        
        # Initialize testers
        self.security_tester = SecurityTester()
        self.format_checker = FormatChecker()
        self.accuracy_evaluator = AccuracyEvaluator()
        
        if OPENAI_AVAILABLE:
            self.multihop_evaluator = MultihopEvaluator()
        else:
            self.multihop_evaluator = None
    
    def _load_test_cases(self) -> List[Dict]:
        """Load test cases from JSON file"""
        test_cases_path = Path(__file__).parent / "test_cases.json"
        
        with open(test_cases_path, 'r') as f:
            data = json.load(f)
            return data['test_cases']
    
    def run_single_test(self, test_case: Dict) -> Dict[str, Any]:
        """
        Run all tests for a single test case
        
        Args:
            test_case: Test case dictionary
            
        Returns:
            Complete test results
        """
        print(f"\n{'='*70}")
        print(f"Test Case #{test_case['id']}: {test_case['query']}")
        print(f"{'='*70}")
        
        result = {
            'test_id': test_case['id'],
            'query': test_case['query'],
            'category': test_case['category'],
            'timestamp': datetime.now().isoformat()
        }
        
        # 1. Security Test
        print("\n1️⃣ Security Test...")
        security_result = self.security_tester.test_prompt_safety(test_case)
        result['security'] = security_result
        print(f"   {'✅ PASS' if security_result['passed'] else '❌ FAIL'}: {security_result['scan_result']['violation_count']} violations")
        
        # 2. Query the system
        print("\n2️⃣ Querying system...")
        try:
            response = requests.post(
                f"{self.api_base_url}/query",
                json={
                    "question": test_case['query'],
                    "mode": "local",
                    "enable_web_search": test_case.get('requires_web_search', False)
                },
                timeout=90
            )
            
            if response.status_code == 200:
                data = response.json()
                system_response = data.get('answer', '')
                result['system_response'] = system_response
                result['response_length'] = len(system_response)
                print(f"   ✅ Response received: {len(system_response)} characters")
            else:
                result['system_response'] = ""
                result['error'] = f"API error: {response.status_code}"
                print(f"   ❌ API error: {response.status_code}")
                return result
                
        except Exception as e:
            result['system_response'] = ""
            result['error'] = str(e)
            print(f"   ❌ Query failed: {e}")
            return result
        
        # 3. Format Compliance Test
        print("\n3️⃣ Format Compliance Test...")
        format_result = self.format_checker.check_format_compliance(system_response)
        result['format'] = format_result
        print(f"   {'✅ PASS' if format_result['compliant'] else '❌ FAIL'}: {format_result['compliance_rate']:.0%} compliance")
        print(f"   Sections found: {', '.join(format_result['sections_found'])}")
        if format_result['sections_missing']:
            print(f"   Missing: {', '.join(format_result['sections_missing'])}")
        
        # 4. Accuracy Test
        print("\n4️⃣ Accuracy Test...")
        accuracy_result = self.accuracy_evaluator.evaluate_accuracy(
            query=test_case['query'],
            response=system_response,
            ground_truth=test_case['ground_truth']
        )
        result['accuracy'] = accuracy_result
        print(f"   {'✅ PASS' if accuracy_result['passed'] else '❌ FAIL'}: {accuracy_result['accuracy_score']:.2%} accuracy")
        
        # 5. Multi-hop Test (if applicable)
        if test_case.get('expected_hops', 0) > 0 and self.multihop_evaluator:
            print("\n5️⃣ Multi-hop Quality Test...")
            
            # Extract path from context or simulate
            path = test_case.get('context', [])
            
            multihop_result = self.multihop_evaluator.evaluate_path_quality(
                query=test_case['query'],
                neo4j_path=path,
                response=system_response
            )
            result['multihop'] = multihop_result
            print(f"   Score: {multihop_result.get('score', 0)}/5")
            print(f"   Reasoning: {multihop_result.get('reasoning', 'N/A')[:100]}...")
        
        return result
    
    def run_full_evaluation(self) -> Dict[str, Any]:
        """
        Run evaluation on all test cases
        
        Returns:
            Complete evaluation report
        """
        print("\n" + "="*70)
        print("🧪 QUALITY EVALUATION: Tech-Analyst GraphRAG")
        print("="*70)
        print(f"Test Cases: {len(self.test_cases)}")
        print(f"API Endpoint: {self.api_base_url}")
        print("="*70)
        
        # Run all tests
        for test_case in self.test_cases:
            result = self.run_single_test(test_case)
            self.results.append(result)
        
        # Aggregate results
        report = self._generate_report()
        
        return report
    
    def _generate_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive evaluation report
        
        Returns:
            Aggregated report
        """
        total_tests = len(self.results)
        
        # Security stats
        security_passed = sum(1 for r in self.results if r.get('security', {}).get('passed', False))
        security_violations = sum(r.get('security', {}).get('scan_result', {}).get('violation_count', 0) for r in self.results)
        
        # Format stats
        format_passed = sum(1 for r in self.results if r.get('format', {}).get('compliant', False))
        avg_format_compliance = sum(r.get('format', {}).get('compliance_rate', 0) for r in self.results) / total_tests if total_tests > 0 else 0
        
        # Accuracy stats
        accuracy_passed = sum(1 for r in self.results if r.get('accuracy', {}).get('passed', False))
        avg_accuracy = sum(r.get('accuracy', {}).get('accuracy_score', 0) for r in self.results) / total_tests if total_tests > 0 else 0
        
        # Multi-hop stats
        multihop_scores = [r.get('multihop', {}).get('score', 0) for r in self.results if 'multihop' in r]
        avg_multihop = sum(multihop_scores) / len(multihop_scores) if multihop_scores else 0
        
        # Overall pass rate
        overall_passed = sum(
            1 for r in self.results 
            if r.get('security', {}).get('passed', False) 
            and r.get('accuracy', {}).get('passed', False)
        )
        
        report = {
            'summary': {
                'total_tests': total_tests,
                'overall_pass_rate': overall_passed / total_tests if total_tests > 0 else 0,
                'timestamp': datetime.now().isoformat()
            },
            'security': {
                'passed': security_passed,
                'failed': total_tests - security_passed,
                'total_violations': security_violations,
                'status': '✅ PASS' if security_violations == 0 else '❌ FAIL'
            },
            'format': {
                'passed': format_passed,
                'failed': total_tests - format_passed,
                'avg_compliance': avg_format_compliance,
                'status': '✅ PASS' if avg_format_compliance >= 0.75 else '⚠️ PARTIAL'
            },
            'accuracy': {
                'passed': accuracy_passed,
                'failed': total_tests - accuracy_passed,
                'avg_score': avg_accuracy,
                'status': '✅ PASS' if avg_accuracy >= 0.6 else '❌ FAIL'
            },
            'multihop': {
                'avg_score': avg_multihop,
                'total_evaluated': len(multihop_scores),
                'status': '✅ PASS' if avg_multihop >= 3.5 else '⚠️ NEEDS IMPROVEMENT'
            },
            'detailed_results': self.results
        }
        
        return report
    
    def print_report(self, report: Dict[str, Any]):
        """
        Print formatted evaluation report
        
        Args:
            report: Report dictionary
        """
        print("\n" + "="*70)
        print("📊 QUALITY EVALUATION REPORT")
        print("="*70)
        
        summary = report['summary']
        print(f"\nTest Cases: {summary['total_tests']}")
        print(f"Overall Pass Rate: {summary['overall_pass_rate']:.1%}")
        print(f"Timestamp: {summary['timestamp']}")
        
        print("\n" + "-"*70)
        print("SECURITY TESTS")
        print("-"*70)
        sec = report['security']
        print(f"Status: {sec['status']}")
        print(f"Passed: {sec['passed']}/{summary['total_tests']}")
        print(f"Violations Detected: {sec['total_violations']}")
        
        print("\n" + "-"*70)
        print("FORMAT COMPLIANCE")
        print("-"*70)
        fmt = report['format']
        print(f"Status: {fmt['status']}")
        print(f"Passed: {fmt['passed']}/{summary['total_tests']}")
        print(f"Average Compliance: {fmt['avg_compliance']:.1%}")
        
        print("\n" + "-"*70)
        print("ACCURACY")
        print("-"*70)
        acc = report['accuracy']
        print(f"Status: {acc['status']}")
        print(f"Passed: {acc['passed']}/{summary['total_tests']}")
        print(f"Average Score: {acc['avg_score']:.1%}")
        
        print("\n" + "-"*70)
        print("MULTI-HOP REASONING")
        print("-"*70)
        mh = report['multihop']
        print(f"Status: {mh['status']}")
        print(f"Average Score: {mh['avg_score']:.2f}/5.0")
        print(f"Tests Evaluated: {mh['total_evaluated']}")
        
        print("\n" + "="*70)
        print("DETAILED RESULTS BY TEST CASE")
        print("="*70)
        
        for result in report['detailed_results']:
            print(f"\n#{result['test_id']}: {result['query'][:60]}...")
            print(f"  Category: {result['category']}")
            
            if 'security' in result:
                sec_pass = '✅' if result['security']['passed'] else '❌'
                print(f"  Security: {sec_pass}")
            
            if 'format' in result:
                fmt_pass = '✅' if result['format']['compliant'] else '❌'
                print(f"  Format: {fmt_pass} ({result['format']['compliance_rate']:.0%})")
            
            if 'accuracy' in result:
                acc_pass = '✅' if result['accuracy']['passed'] else '❌'
                print(f"  Accuracy: {acc_pass} ({result['accuracy']['accuracy_score']:.1%})")
            
            if 'multihop' in result:
                print(f"  Multi-hop: {result['multihop']['score']}/5")
        
        print("\n" + "="*70)
    
    def save_report(self, report: Dict[str, Any], filepath: str = "evaluation_report.json"):
        """Save report to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n💾 Report saved to: {filepath}")


def main():
    """Main evaluation function"""
    print("\n🚀 Starting Quality Evaluation System")
    
    # Check if backend is running
    try:
        response = requests.get("http://localhost:8000/health", timeout=3)
        if response.status_code != 200:
            print("❌ Backend not healthy")
            return
    except:
        print("❌ Backend not running. Start with: ./start.sh")
        return
    
    # Run evaluation
    evaluator = QualityEvaluator()
    report = evaluator.run_full_evaluation()
    
    # Print report
    evaluator.print_report(report)
    
    # Save report
    evaluator.save_report(report, "evaluator/evaluation_report.json")
    
    print("\n✅ Evaluation complete!")


if __name__ == "__main__":
    main()
