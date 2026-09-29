"""Local UI preview with labeled, synthetic data. Never starts the backend.

Run: python tests/preview_server.py, then open http://127.0.0.1:8877/
Only this preview server injects fixtures; production HTML is unchanged.
"""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import io

FRONTEND = Path(__file__).resolve().parents[1] / 'frontend'
FIXTURE = '''<script>
localStorage.setItem('nutri_token','local-preview-only');
localStorage.setItem('nutri_intro_completed_v1','true');
const realFetch=window.fetch.bind(window);
window.fetch=async (input,options={})=>{
 const url=new URL(typeof input==='string'?input:input.url,location.href);
 if(!url.pathname.startsWith('/api/'))return realFetch(input,options);
 if(options.method && options.method!=='GET')return new Response(JSON.stringify({detail:'Preview only: changes are not saved.'}),{status:400,headers:{'Content-Type':'application/json'}});
 const profile={height_cm:165,weight_kg:65,target_weight_kg:63,bmi:23.9,daily_calorie_goal:2000,illnesses:'',allergies:''};
 const today=new Date().toISOString();
 let data={};
 if(url.pathname.includes('/users/me'))data={id:'preview',name:'Alex Rivera',first_name:'Alex',last_name:'Rivera',email:'alex@example.com',has_completed_tour:true};
 else if(url.pathname.includes('/profile'))data=profile;
 else if(url.pathname.includes('/logs'))data=[{id:'demo1',food_name:'Chicken, rice & greens',meal_type:'Lunch',calories:520,protein_g:36,carbs_g:62,fat_g:14,vitamin_c_mg:24,calcium_mg:80,iron_mg:2.1,logged_at:today},{id:'demo2',food_name:'Banana & oats',meal_type:'Breakfast',calories:310,protein_g:9,carbs_g:54,fat_g:7,vitamin_c_mg:10,calcium_mg:40,iron_mg:1.5,logged_at:today}];
 else if(url.pathname.includes('/weight'))data=[66.2,66,65.8,65.6,65.7,65.2,65].map((weight_kg,i)=>({weight_kg,logged_at:new Date(Date.now()-(6-i)*86400000).toISOString()}));
 else if(url.pathname.includes('/reminders'))data={Breakfast:'08:00 AM',Lunch:'12:30 PM',Dinner:'07:00 PM'};
 else if(url.pathname.includes('/medical-conditions'))data=[{id:'1',name:'Diabetes',description:'Blood glucose considerations'},{id:'2',name:'Hypertension',description:'Blood pressure considerations'},{id:'3',name:'Lactose Intolerance',description:'Dairy preferences'}];
 return new Response(JSON.stringify(data),{status:200,headers:{'Content-Type':'application/json'}});
};
if(navigator.mediaDevices) navigator.mediaDevices.getUserMedia=async()=>{throw new Error('Camera disabled in preview');};
document.addEventListener('DOMContentLoaded',()=>{const label=document.createElement('div');label.textContent='DESIGN PREVIEW · SAMPLE DATA · CHANGES NOT SAVED';label.style.cssText='background:#eee4cc;color:#665a3e;text-align:center;font:10px/1.5 sans-serif;padding:7px;letter-spacing:1px';document.body.prepend(label);});
</script>'''

class PreviewHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(FRONTEND), **kwargs)

    def send_head(self):
        path = Path(self.translate_path(self.path))
        if path.is_dir():
            path = path / 'index.html'
        if path.suffix == '.html' and path.is_file():
            data = path.read_text(encoding='utf-8').replace('<head>', '<head>' + FIXTURE, 1).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            return io.BytesIO(data)
        return super().send_head()

if __name__ == '__main__':
    print('Sample-data UI preview: http://127.0.0.1:8877/', flush=True)
    ThreadingHTTPServer(('127.0.0.1', 8877), PreviewHandler).serve_forever()
