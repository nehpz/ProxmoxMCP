#!/usr/bin/env python3
"""
Parallel configuration optimization script for Phase 3.
Finds optimal worker counts for different test categories.
"""

import subprocess
import json
import time
from concurrent.futures import ThreadPoolExecutor


def test_worker_configuration(worker_count, test_category=None):
    """Test specific worker configuration."""
    
    args = ['pytest', 'tests/', '-n', str(worker_count), '--tb=no', '-q']
    
    if test_category:
        args.extend(['-m', test_category])
        
    start_time = time.time()
    result = subprocess.run(args, capture_output=True, text=True)
    duration = time.time() - start_time
    
    return {
        'workers': worker_count,
        'category': test_category,
        'duration': duration,
        'success': result.returncode == 0,
        'output': result.stdout
    }


def find_optimal_configuration():
    """Find optimal worker configurations for each test category."""
    
    configurations = []
    
    # Test different worker counts for each category
    categories = ['unit', 'integration', None]  # None = all tests
    worker_counts = [1, 2, 4, 6, 8, 'auto']
    
    print("Testing worker configurations...")
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = []
        
        for category in categories:
            for workers in worker_counts:
                future = executor.submit(test_worker_configuration, workers, category)
                futures.append(future)
                
        for future in futures:
            result = future.result()
            configurations.append(result)
            
            category_str = result['category'] or 'all'
            status = "✅" if result['success'] else "❌"
            print(f"{status} {category_str:>11} tests, {result['workers']:>4} workers: {result['duration']:>6.2f}s")
    
    # Find optimal configurations
    optimal = {}
    
    for category in categories:
        category_configs = [c for c in configurations if c['category'] == category and c['success']]
        if category_configs:
            optimal_config = min(category_configs, key=lambda x: x['duration'])
            optimal[category or 'all'] = optimal_config
            
    return optimal


def generate_recommendations(optimal_configs):
    """Generate optimization recommendations."""
    
    recommendations = {
        'pytest_commands': {},
        'ci_cd_config': {},
        'developer_workflow': {}
    }
    
    # Pytest command recommendations
    for category, config in optimal_configs.items():
        workers = config['workers']
        category_name = category.replace('_', ' ').title()
        
        if category == 'all':
            recommendations['pytest_commands']['full_suite'] = f"pytest -n {workers}"
        else:
            recommendations['pytest_commands'][category] = f"pytest -m '{category}' -n {workers}"
    
    # CI/CD recommendations
    recommendations['ci_cd_config'] = {
        'fast_feedback': f"pytest -m 'unit' -n {optimal_configs.get('unit', {}).get('workers', 'auto')}",
        'full_validation': f"pytest -n {optimal_configs.get('all', {}).get('workers', 'auto')}",
        'integration_only': f"pytest -m 'integration' -n {optimal_configs.get('integration', {}).get('workers', 2)}"
    }
    
    # Developer workflow
    unit_time = optimal_configs.get('unit', {}).get('duration', 0)
    all_time = optimal_configs.get('all', {}).get('duration', 0)
    
    recommendations['developer_workflow'] = {
        'during_development': 'pytest -m "unit" -n auto  # Fast feedback loop',
        'before_commit': 'pytest -n auto  # Full validation',
        'estimated_times': {
            'unit_tests': f"{unit_time:.1f}s",
            'full_suite': f"{all_time:.1f}s"
        }
    }
    
    return recommendations


def main():
    print("🔧 Parallel Configuration Optimizer")
    print("=" * 50)
    
    # Find optimal configurations
    optimal_configs = find_optimal_configuration()
    
    # Generate recommendations
    recommendations = generate_recommendations(optimal_configs)
    
    # Save results
    results = {
        'optimal_configurations': optimal_configs,
        'recommendations': recommendations,
        'timestamp': time.time()
    }
    
    with open('parallel_optimization_results.json', 'w') as f:
        json.dump(results, f, indent=2)
        
    # Print summary
    print("\n🏆 Optimal Configurations")
    print("=" * 50)
    
    for category, config in optimal_configs.items():
        category_name = category.replace('_', ' ').title()
        print(f"{category_name:>12}: {config['workers']:>4} workers ({config['duration']:.2f}s)")
        
    print("\n🚀 Recommended Commands")
    print("=" * 50)
    
    for purpose, command in recommendations['pytest_commands'].items():
        purpose_name = purpose.replace('_', ' ').title()
        print(f"{purpose_name:>12}: {command}")
        
    return 0


if __name__ == '__main__':
    exit(main())