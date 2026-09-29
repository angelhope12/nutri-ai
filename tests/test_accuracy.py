"""Offline regression tests for pure application logic, without service startup.

AST loading avoids importing optional cloud/DB/ML packages or contacting services.
These are not HTTP integration tests.
"""
import ast
import json
import os
from pathlib import Path
import re
import sys
import unittest

BACKEND = Path(__file__).resolve().parents[1] / 'backend'
sys.path.insert(0, str(BACKEND))
from component.common_foods import COMMON_FOODS


class HTTPException(Exception):
    def __init__(self, status_code, detail):
        self.status_code, self.detail = status_code, detail


def functions(path, names, extra=None):
    tree = ast.parse(path.read_text(encoding='utf-8'))
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    namespace = dict(re=re, json=json, os=os, COMMON_FOODS=COMMON_FOODS,
                     HTTPException=HTTPException)
    namespace.update(extra or {})
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), namespace)
    return namespace


class AccuracyTests(unittest.TestCase):
    def setUp(self):
        self.ns = functions(BACKEND / 'component/ai_service.py',
            {'find_local_food', 'check_local_medical_cautions', 'get_alternatives_for_allergy'})
        self.find = self.ns['find_local_food']

    def test_gram_scaling(self):
        result = self.find('200g banana')
        self.assertEqual(result['calories'], 178)
        self.assertEqual(result['portion_grams'], 200)
        self.assertFalse(result['portion_assumed'])

    def test_piece_scaling(self):
        self.assertEqual(self.find('2 eggs')['portion_grams'], 100)

    def test_default_portion_disclosed(self):
        self.assertTrue(self.find('banana')['portion_assumed'])

    def test_different_foods_not_substring_matched(self):
        for query in ('pineapple cake', 'banana bread with chocolate', 'eggplant surprise'):
            self.assertIsNone(self.find(query), query)

    def test_invalid_portions(self):
        for query in ('-100g banana', '0g banana', '0 eggs', '100ml banana', '2 cups banana', '2 chicken breast'):
            with self.subTest(query=query), self.assertRaises(HTTPException):
                self.find(query)

    def test_unknown_food_has_no_default_nutrition(self):
        # The only import inside this function is the HTTP exception type.
        tree = ast.parse((BACKEND / 'component/food101_mapping.py').read_text(encoding='utf-8'))
        fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'get_nutrition_for_class')
        fn.body = [n for n in fn.body if not isinstance(n, ast.ImportFrom)]
        scope = dict(COMMON_FOODS=COMMON_FOODS, FOOD101_ESTIMATED_PROFILES={},
                     format_class_name=lambda x: x, HTTPException=HTTPException,
                     Dict=dict, Any=object)
        exec(compile(ast.Module(body=[fn], type_ignores=[]), '<mapping>', 'exec'), scope)
        with self.assertRaises(HTTPException):
            scope['get_nutrition_for_class']('unsupported_dish')

    def test_password_recovery_fails_closed(self):
        tree = ast.parse((BACKEND / 'main.py').read_text(encoding='utf-8'))
        fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'forgot_password_immidiate_reset')
        fn.decorator_list = []
        fn.args.defaults = []
        for arg in fn.args.args:
            arg.annotation = None
        scope = dict(HTTPException=HTTPException)
        exec(compile(ast.Module(body=[fn], type_ignores=[]), '<reset>', 'exec'), scope)
        with self.assertRaises(HTTPException) as result:
            scope[fn.name](object(), object())
        self.assertEqual(result.exception.status_code, 503)


if __name__ == '__main__':
    unittest.main()
