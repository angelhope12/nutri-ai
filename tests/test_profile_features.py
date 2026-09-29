import sys
from pathlib import Path
from datetime import datetime, timedelta
from types import SimpleNamespace
from io import BytesIO
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from component.reminders import learn_schedule
from component.profile_photo import prepare_photo
from PIL import Image
class ProfileFeaturesTests(unittest.TestCase):
    def test_learning_requires_three_days(self):
        now=datetime(2026,9,29,20)
        log=SimpleNamespace(meal_type='Breakfast',logged_at=now.replace(hour=9))
        self.assertEqual(learn_schedule([log]*20,now)['details']['Breakfast']['source'],'default')
    def test_median_ignores_outlier_and_duplicate_items(self):
        now=datetime(2026,9,29,20)
        logs=[SimpleNamespace(meal_type='Breakfast',logged_at=(now-timedelta(days=i)).replace(hour=h,minute=0)) for i,h in enumerate([9,9,9,12,9])]
        logs += [logs[3]]*10
        result=learn_schedule(logs,now)
        self.assertEqual(result['times']['Breakfast'],'09:00 AM')
        self.assertEqual(result['details']['Breakfast']['days'],5)
    def test_old_and_future_logs_ignored(self):
        now=datetime(2026,9,29,20)
        logs=[SimpleNamespace(meal_type='Dinner',logged_at=now+timedelta(days=d)) for d in [-40,-50,1]]
        self.assertEqual(learn_schedule(logs,now)['details']['Dinner']['days'],0)
    def test_avatar_reencoded_and_cropped(self):
        source=BytesIO();Image.new('RGB',(800,500),'green').save(source,format='PNG')
        with Image.open(BytesIO(prepare_photo(source.getvalue()))) as image:
            self.assertEqual(image.size,(384,384));self.assertEqual(image.format,'JPEG');self.assertFalse(image.getexif())
    def test_avatar_rejects_non_image_and_oversize(self):
        for data in [b'<svg></svg>',b'',b'x'*(4*1024*1024+1)]:
            with self.assertRaises(ValueError):prepare_photo(data)
class MedicalWarningTests(unittest.TestCase):
    def test_all_conditions_acknowledged_without_unchecked_substitutions(self):
        from test_accuracy import functions, BACKEND
        check=functions(BACKEND/'component/ai_service.py',{'check_local_medical_cautions'})['check_local_medical_cautions']
        warning=check('peanut sauce',{'allergies':'peanuts, soy','illnesses':'Diabetes, Hypertension'})
        self.assertIn('peanuts',warning)
        self.assertIn('Diabetes, Hypertension',warning)
        self.assertIn('No verified alternative',warning)
        self.assertNotIn('almonds',warning)
    def test_meal_time_requires_timezone_and_rejects_future(self):
        import ast
        from datetime import timezone
        from pydantic import BaseModel, field_validator, ValidationError
        from typing import Optional
        path=Path(__file__).resolve().parents[1]/'backend/db/schemas.py'
        cls=next(n for n in ast.parse(path.read_text()).body if isinstance(n,ast.ClassDef) and n.name=='FoodLogCreate')
        ns={'FoodLogBase':BaseModel,'Optional':Optional,'datetime':datetime,'timezone':timezone,'timedelta':timedelta,'field_validator':field_validator}
        exec(compile(ast.Module(body=[cls],type_ignores=[]),str(path),'exec'),ns)
        model=ns['FoodLogCreate']
        with self.assertRaises(ValidationError):model(eaten_at='2026-01-01T12:00:00')
        with self.assertRaises(ValidationError):model(eaten_at=datetime.now(timezone.utc)+timedelta(days=1))
        self.assertIsNotNone(model(eaten_at='2026-01-01T12:00:00+08:00').eaten_at)
if __name__=='__main__':unittest.main()
