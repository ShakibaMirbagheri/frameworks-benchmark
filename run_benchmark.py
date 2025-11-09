"""
Main Benchmark Runner
Runs all framework tests and compares results
"""
import subprocess
import sys
import time
import json
from typing import Dict, Any, List
from tabulate import tabulate
import os


class BenchmarkRunner:
    """Runner for all framework benchmarks"""
    
    def __init__(self):
        self.results: List[Dict[str, Any]] = []
        self.frameworks = {
            "CrewAI": "test_crewai.py",
            "LangGraph": "test_langgraph.py",
            "DSPy": "test_dspy.py",
            "Langchain": "test_langchain.py"
        }
        
    def run_test(self, framework_name: str, test_file: str) -> Dict[str, Any]:
        """Run a single framework test"""
        print(f"\n{'='*70}")
        print(f"Running {framework_name} Benchmark")
        print(f"{'='*70}\n")
        
        start_time = time.time()
        
        try:
            # Run the test file
            result = subprocess.run(
                [sys.executable, test_file],
                capture_output=True,
                text=True,
                timeout=120  # 2 minute timeout
            )
            
            elapsed_time = time.time() - start_time
            
            # Print output
            print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
            
            # Try to load detailed results from JSON file
            json_file = f"results_{framework_name.lower()}.json"
            detailed_results = None
            if os.path.exists(json_file):
                with open(json_file, 'r') as f:
                    detailed_results = json.load(f)
            
            return {
                "framework": framework_name,
                "success": result.returncode == 0,
                "total_time": elapsed_time,
                "return_code": result.returncode,
                "detailed_results": detailed_results,
                "error": None if result.returncode == 0 else result.stderr
            }
            
        except subprocess.TimeoutExpired:
            elapsed_time = time.time() - start_time
            return {
                "framework": framework_name,
                "success": False,
                "total_time": elapsed_time,
                "return_code": -1,
                "detailed_results": None,
                "error": "Timeout (>120s)"
            }
        except Exception as e:
            elapsed_time = time.time() - start_time
            return {
                "framework": framework_name,
                "success": False,
                "total_time": elapsed_time,
                "return_code": -1,
                "detailed_results": None,
                "error": str(e)
            }
    
    def run_all_tests(self):
        """Run all framework tests"""
        print("\n" + "="*70)
        print("AI FRAMEWORK BENCHMARK SUITE")
        print("Testing: CrewAI, LangGraph, DSPy, Langchain")
        print("="*70)
        
        for framework_name, test_file in self.frameworks.items():
            result = self.run_test(framework_name, test_file)
            self.results.append(result)
            
            # Short delay between tests
            time.sleep(2)
        
        return self.results
    
    def generate_comparison_report(self):
        """Generate comparison report"""
        print("\n" + "="*70)
        print("BENCHMARK COMPARISON REPORT")
        print("="*70 + "\n")
        
        # Summary table
        summary_data = []
        for result in self.results:
            summary_data.append([
                result['framework'],
                "✓" if result['success'] else "✗",
                f"{result['total_time']:.4f}s",
                result.get('error', '-')[:50] if result.get('error') else '-'
            ])
        
        print("\n📊 SUMMARY TABLE")
        print(tabulate(
            summary_data,
            headers=['Framework', 'Success', 'Total Time', 'Error'],
            tablefmt='grid'
        ))
        
        # Detailed step timing
        print("\n⏱️  DETAILED STEP TIMING\n")
        
        for result in self.results:
            if result['detailed_results'] and result['detailed_results'].get('steps'):
                print(f"\n{result['framework']}:")
                print("-" * 50)
                
                steps_data = []
                for step in result['detailed_results']['steps']:
                    steps_data.append([
                        step['step'],
                        f"{step['duration']:.4f}s",
                        step.get('details', '-')
                    ])
                
                print(tabulate(
                    steps_data,
                    headers=['Step', 'Duration', 'Details'],
                    tablefmt='simple'
                ))
                
                total = result['detailed_results'].get('total_time', 0)
                print(f"\nTotal: {total:.4f}s")
        
        # Ranking
        print("\n🏆 PERFORMANCE RANKING (by total time)\n")
        
        successful_results = [r for r in self.results if r['success']]
        if successful_results:
            ranked = sorted(successful_results, key=lambda x: x['total_time'])
            
            ranking_data = []
            for i, result in enumerate(ranked, 1):
                ranking_data.append([
                    i,
                    result['framework'],
                    f"{result['total_time']:.4f}s"
                ])
            
            print(tabulate(
                ranking_data,
                headers=['Rank', 'Framework', 'Time'],
                tablefmt='grid'
            ))
        else:
            print("No successful benchmarks to rank.")
        
        # Save full report to JSON
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "results": self.results
        }
        
        with open("benchmark_report.json", 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n✅ Full report saved to: benchmark_report.json")
        
        return report
    
    def run(self):
        """Run complete benchmark suite"""
        self.run_all_tests()
        self.generate_comparison_report()
        
        # Print conclusion
        print("\n" + "="*70)
        print("BENCHMARK COMPLETE")
        print("="*70)
        
        successful = sum(1 for r in self.results if r['success'])
        total = len(self.results)
        
        print(f"\nResults: {successful}/{total} frameworks completed successfully")
        
        if successful > 0:
            fastest = min([r for r in self.results if r['success']], key=lambda x: x['total_time'])
            print(f"Fastest: {fastest['framework']} ({fastest['total_time']:.4f}s)")


def main():
    """Main entry point"""
    runner = BenchmarkRunner()
    runner.run()


if __name__ == "__main__":
    main()

