#!/usr/bin/env python3
"""
Thread safety validation script for Phase 2.
Detects potential shared state issues in test files.
"""

import ast
import re
from pathlib import Path


class SharedStateDetector(ast.NodeVisitor):
    """Detect potential shared state issues in test files."""
    
    def __init__(self):
        self.issues = []
        self.current_class = None
        
    def visit_ClassDef(self, node):
        self.current_class = node.name
        
        # Check for class-level mutable attributes
        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        if self._is_mutable_assignment(item.value):
                            self.issues.append({
                                'type': 'class_mutable_state',
                                'class': node.name,
                                'variable': target.id,
                                'line': item.lineno
                            })
        
        self.generic_visit(node)
        
    def _is_mutable_assignment(self, node):
        """Check if assignment creates mutable object."""
        if isinstance(node, (ast.List, ast.Dict, ast.Set)):
            return True
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            mutable_constructors = {'list', 'dict', 'set', 'Mock', 'MagicMock'}
            return node.func.id in mutable_constructors
        return False
        
    def visit_FunctionDef(self, node):
        # Check for shared fixture scope issues
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call) and \
               hasattr(decorator.func, 'attr') and \
               decorator.func.attr == 'fixture':
                
                for keyword in decorator.keywords:
                    if keyword.arg == 'scope' and \
                       isinstance(keyword.value, ast.Constant) and \
                       keyword.value.value in ['session', 'module']:
                        
                        self.issues.append({
                            'type': 'shared_fixture_scope',
                            'function': node.name,
                            'scope': keyword.value.value,
                            'line': node.lineno
                        })
        
        self.generic_visit(node)


def validate_thread_safety():
    """Validate all test files for thread safety issues."""
    issues = []
    
    for test_file in Path('tests').rglob('*.py'):
        if test_file.name.startswith('test_') or test_file.name == 'conftest.py':
            with open(test_file, 'r') as f:
                content = f.read()
                
            tree = ast.parse(content)
            detector = SharedStateDetector()
            detector.visit(tree)
            
            for issue in detector.issues:
                issue['file'] = str(test_file)
                issues.append(issue)
                
    return issues


def main():
    issues = validate_thread_safety()
    
    if not issues:
        print("✅ No thread safety issues detected")
        return 0
        
    print(f"❌ Found {len(issues)} potential thread safety issues:")
    
    for issue in issues:
        print(f"  {issue['file']}:{issue['line']} - {issue['type']}")
        if issue['type'] == 'class_mutable_state':
            print(f"    Class {issue['class']} has mutable variable: {issue['variable']}")
        elif issue['type'] == 'shared_fixture_scope':
            print(f"    Fixture {issue['function']} has shared scope: {issue['scope']}")
            
    return 1


if __name__ == '__main__':
    exit(main())