"""Only each exact Jupeng Runtime receives its own business handoff."""
import json,pathlib,sys,tempfile,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(0,str(ROOT/'skills/core/zhuojian-subsystem-builder/scripts'))
import build_release
import update_managed_skills as updater

class FinanceOrderHandoffTests(unittest.TestCase):
 def test_exact_runtime_host_and_enterprise_select_only_one_handoff(self):
  raw=json.loads((ROOT/'catalog.json').read_text(encoding='utf-8'))
  with tempfile.TemporaryDirectory() as td:
   base=pathlib.Path(td);entries={}
   for name in ['zhuojian-subsystem-builder','jupeng-finance-runtime-handover','jupeng-order-runtime-handover']:
    entry,_=build_release.package_skill(ROOT,base,name=name,source=raw['skills'][name],tag='local-test-only')
    entry['archiveUrl']=(base/(name+'-'+entry['skillVersion']+'.zip')).as_uri();entries[name]=entry
   catalog=base/'catalog.json';catalog.write_text(json.dumps({'schemaVersion':1,'channel':'stable','repository':updater.REPOSITORY,'skills':entries}),encoding='utf-8')
   cases=[('finance-runtime',['--enterprise-key','jupeng','--runtime-id','jupeng-finance-sg-01','--host','47.237.128.65'],{'jupeng-finance-runtime-handover'}),('finance-host',['--enterprise-key','jupeng','--host','47.237.128.65'],{'jupeng-finance-runtime-handover'}),('order-runtime',['--enterprise-key','jupeng','--runtime-id','jupeng-order-hz-01','--host','47.96.234.89'],{'jupeng-order-runtime-handover'}),('order-host',['--enterprise-key','jupeng','--host','47.96.234.89'],{'jupeng-order-runtime-handover'}),('wrong-enterprise',['--enterprise-key','alphabet','--host','47.96.234.89'],set()),('wrong-runtime',['--enterprise-key','jupeng','--runtime-id','unknown','--host','47.96.234.89'],set())]
   for label,args,expected in cases:
    with self.subTest(label=label):
     out=base/label;self.assertEqual(updater.main(['--catalog-url',catalog.as_uri(),'--allow-test-url','--skills-dir',str(out),'resolve',*args]),0)
     found={p.name for p in out.iterdir() if p.is_dir() and not p.name.startswith('.')} if out.exists() else set();self.assertEqual(found,expected)

if __name__=='__main__':unittest.main()
