#!/usr/bin/env python3
"""
Performance measurement script for Phase 3.
Benchmarks sequential vs parallel test execution.
"""

import subprocess
import time
import json
from pathlib import Path


def run_test_suite(args, description):
    """Run test suite with given arguments and measure performance."""
    print(f"\n=== {description} ===")
    
    start_time = time.time()
    result = subprocess.run(
        ['pytest'] + args + ['--tb=no', '-q'],
        capture_output=True,
        text=True
    )
    end_time = time.time()
    
    duration = end_time - start_time
    
    # Parse test results
    output_lines = result.stdout.split('\n')
    summary_line = [line for line in output_lines if 'passed' in line or 'failed' in line]
    
    if summary_line:
        summary = summary_line[-1]
        # Extract test count
        import re
        test_count_match = re.search(r'(\d+) passed', summary)
        test_count = int(test_count_match.group(1)) if test_count_match else 0
    else:
        test_count = 0
        
    return {
        'duration': duration,
        'test_count': test_count,
        'exit_code': result.returncode,
        'output': result.stdout,
        'errors': result.stderr
    }


def measure_baseline_performance():
    """Measure baseline (sequential) performance."""
    print("Measuring baseline performance...")
    
    # Warm-up run
    subprocess.run(['pytest', '--collect-only'], capture_output=True)
    
    # Baseline measurement
    baseline = run_test_suite(['tests/'], "Sequential Execution (Baseline)")
    
    return baseline


def measure_parallel_performance():
    """Measure parallel execution performance with different worker counts."""
    results = {}
    
    # Test different worker counts
    worker_counts = [2, 4, 'auto']
    
    for workers in worker_counts:
        worker_str = str(workers)
        description = f"Parallel Execution ({worker_str} workers)"
        
        args = ['tests/', '-n', worker_str]
        results[worker_str] = run_test_suite(args, description)
        
    return results


def measure_category_performance():
    """Measure performance by test category."""
    categories = {
        'unit': ['-m', 'unit'],
        'integration': ['-m', 'integration'], 
        'slow': ['-m', 'slow']
    }
    
    results = {}
    
    for category, marker_args in categories.items():
        # Sequential
        seq_args = ['tests/'] + marker_args
        results[f'{category}_sequential'] = run_test_suite(
            seq_args, f"{category.title()} Tests (Sequential)"
        )
        
        # Parallel 
        par_args = ['tests/', '-n', 'auto'] + marker_args
        results[f'{category}_parallel'] = run_test_suite(
            par_args, f"{category.title()} Tests (Parallel)"
        )
        
    return results


def generate_performance_report(baseline, parallel_results, category_results):
    """Generate comprehensive performance report."""
    
    report = {
        'timestamp': time.time(),
        'baseline': baseline,
        'parallel': parallel_results,
        'categories': category_results,
        'analysis': {}
    }
    
    # Calculate improvements
    if baseline['duration'] > 0:
        for workers, result in parallel_results.items():
            if result['exit_code'] == 0:
                improvement = (baseline['duration'] - result['duration']) / baseline['duration']
                report['analysis'][f'improvement_{workers}'] = {
                    'percentage': improvement * 100,
                    'time_saved': baseline['duration'] - result['duration'],
                    'speedup_factor': baseline['duration'] / result['duration']
                }
    
    # Save report
    report_file = Path('performance_report.json')
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
        
    return report


def main():
    print("🔍 Performance Measurement Suite")
    print("=" * 50)
    
    # Measure baseline
    baseline = measure_baseline_performance()
    
    if baseline['exit_code'] != 0:
        print("❌ Baseline tests failed - aborting performance measurement")
        print(baseline['errors'])
        return 1
        
    print(f"✅ Baseline: {baseline['duration']:.2f}s for {baseline['test_count']} tests")
    
    # Measure parallel performance
    parallel_results = measure_parallel_performance()
    
    # Measure category performance  
    category_results = measure_category_performance()
    
    # Generate report
    report = generate_performance_report(baseline, parallel_results, category_results)
    
    # Print summary
    print("\n📊 Performance Summary")
    print("=" * 50)
    
    for workers, result in parallel_results.items():
        if result['exit_code'] == 0:
            analysis = report['analysis'].get(f'improvement_{workers}', {})
            improvement_pct = analysis.get('percentage', 0)
            speedup = analysis.get('speedup_factor', 1)
            
            print(f"{workers:>4} workers: {result['duration']:>6.2f}s "
                  f"({improvement_pct:>5.1f}% faster, {speedup:.1f}x speedup)")
        else:
            print(f"{workers:>4} workers: FAILED")
            
    return 0


if __name__ == '__main__':
    exit(main())