#!/usr/bin/env python3
"""
Automated test marking script for Phase 1.
Analyzes test methods and adds appropriate pytest markers (unit/integration/slow).
"""

import ast
import re
from pathlib import Path


class TestMarkerAnalyzer(ast.NodeVisitor):
    """Analyze test methods to determine appropriate markers."""
    
    def __init__(self):
        self.test_methods = []
        self.current_class = None
        
    def visit_ClassDef(self, node):
        self.current_class = node.name
        self.generic_visit(node)
        
    def visit_AsyncFunctionDef(self, node):
        if node.name.startswith('test_'):
            marker = self.analyze_test_method(node)
            self.test_methods.append({
                'name': node.name,
                'class': self.current_class,
                'marker': marker,
                'line': node.lineno
            })
            
    def analyze_test_method(self, node):
        """Determine appropriate marker based on test characteristics."""
        source = ast.get_source_segment(self.source_code, node)
        
        # Count API-like calls (mock assertions, await calls)
        api_calls = len(re.findall(r'\.assert_called|await \w+\.|mock_\w+\.', source))
        
        # Check for workflow keywords
        workflow_keywords = ['create.*start.*stop', 'lifecycle', 'complete.*workflow']
        is_workflow = any(re.search(keyword, source, re.IGNORECASE) 
                         for keyword in workflow_keywords)
        
        # Check for performance/slow indicators
        slow_indicators = ['task_monitoring', 'performance', 'benchmark', 'timeout']
        is_slow = any(indicator in source.lower() for indicator in slow_indicators)
        
        # Classification logic
        if is_slow:
            return 'slow'
        elif is_workflow or api_calls > 3:
            return 'integration'
        else:
            return 'unit'


def add_markers_to_file(file_path):
    """Add appropriate markers to all test methods in a file."""
    with open(file_path, 'r') as f:
        content = f.read()
        
    # Parse and analyze
    tree = ast.parse(content)
    analyzer = TestMarkerAnalyzer()
    analyzer.source_code = content
    analyzer.visit(tree)
    
    # Add markers
    lines = content.split('\n')
    offset = 0
    
    for method in sorted(analyzer.test_methods, key=lambda x: x['line'], reverse=True):
        line_idx = method['line'] - 1 + offset
        marker_line = f"    @pytest.mark.{method['marker']}"
        
        # Check if marker already exists
        if line_idx > 0 and '@pytest.mark.' in lines[line_idx - 1]:
            continue  # Skip if already marked
            
        lines.insert(line_idx, marker_line)
        offset += 1
        
    # Write back
    with open(file_path, 'w') as f:
        f.write('\n'.join(lines))
        
    return len(analyzer.test_methods)


def main():
    test_files = Path('tests').rglob('test_*.py')
    total_marked = 0
    
    for test_file in test_files:
        if test_file.name in ['__init__.py', 'conftest.py']:
            continue
            
        print(f"Processing {test_file}...")
        marked = add_markers_to_file(test_file)
        total_marked += marked
        print(f"  Added markers to {marked} test methods")
        
    print(f"\nTotal test methods marked: {total_marked}")


if __name__ == '__main__':
    main()