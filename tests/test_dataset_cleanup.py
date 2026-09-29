import ast
import importlib.util
import os
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('cleanup', ROOT / 'dataset_review/clean_archive.py')
cleanup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cleanup)


class DatasetCleanupTests(unittest.TestCase):
    def test_reviewed_nonfood_examples_excluded(self):
        for index in (113, 282, 347, 419, 528, 718, 765, 1000, 1456, 2172):
            self.assertEqual(cleanup.classify(index)[0], 'excluded_unrelated')

    def test_wrong_food_labels_not_approved(self):
        for index in (30, 90, 319, 1433, 1969, 2107):
            self.assertEqual(cleanup.classify(index)[0], 'label_review')

    def test_food_candidates_preserved(self):
        for index in (57, 126, 500, 739, 1700, 2187, 2243):
            self.assertEqual(cleanup.classify(index)[0], 'food_candidate')

    def test_training_skips_quarantine_even_when_nested(self):
        tree = ast.parse((ROOT / 'backend/train_local_model.py').read_text())
        fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'is_valid_image_file')
        scope = {'os': os}
        exec(compile(ast.Module(body=[fn], type_ignores=[]), '<dataset-filter>', 'exec'), scope)
        valid = scope['is_valid_image_file']
        for folder in ('pending_review', 'excluded_unrelated', 'label_review', 'food_candidate'):
            self.assertFalse(valid(f'data/{folder}/class/photo.jpg'))
        self.assertTrue(valid('reviewed/train/class/photo.jpg'))


if __name__ == '__main__':
    unittest.main()
