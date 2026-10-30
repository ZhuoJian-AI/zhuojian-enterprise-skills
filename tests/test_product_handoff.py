"""Product host selection must not leak onto customer or shared runtimes."""
import json,pathlib,sys,tempfile,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
sys.path.insert(0,str(ROOT/'skills/core/zhuojian-subsystem-builder/scripts'))
import build_release
import update_managed_skills as updater

class ProductHandoffTests(unittest.TestCase):
 def test_only_exact_product_runtime_or_host_matches(self):
  with tempfile.TemporaryDirectory() as td:
   target=pathlib.Path(td);catalog=json.loads((ROOT/'catalog.json').read_text());entries={}
   for name in ['jupeng-product-runtime-handover','jupeng-customer-runtime-handover','jupeng-readonly-runtime-handover']:
    entry,_=build_release.package_skill(ROOT,target,name=name,source=catalog['skills'][name],tag='local-test-only')
    entry['archiveUrl']=(target/(name+'-'+entry['skillVersion']+'.zip')).as_uri();entries[name]=entry
   cp=target/'catalog.json';cp.write_text(json.dumps({'schemaVersion':1,'channel':'stable','repository':updater.REPOSITORY,'skills':entries}))
   cases=[('runtime',['--enterprise-key','jupeng','--runtime-id','jupeng-product-hz-01','--host','47.98.203.195'],{'jupeng-product-runtime-handover'}),('host',['--enterprise-key','jupeng','--host','47.98.203.195'],{'jupeng-product-runtime-handover'}),('wrong-runtime',['--enterprise-key','jupeng','--runtime-id','unknown','--host','47.98.203.195'],set()),('wrong-tenant',['--enterprise-key','alphabet','--host','47.98.203.195'],set()),('customer',['--enterprise-key','jupeng','--runtime-id','jupeng-customer-hz-01','--host','121.43.59.104'],{'jupeng-customer-runtime-handover'})]
   for label,args,expected in cases:
    out=target/label
    self.assertEqual(updater.main(['--catalog-url',cp.as_uri(),'--allow-test-url','--skills-dir',str(out),'resolve',*args]),0)
    self.assertEqual({p.name for p in out.iterdir() if p.is_dir() and not p.name.startswith('.')} if out.exists() else set(),expected)

if __name__=='__main__':unittest.main()
