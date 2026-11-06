"""Date-window/delivery regression, not an in-game rendering test."""
import datetime,json,re,unittest
from pathlib import Path
from hoi4_politics_blocks import load
from generate_people_we_event import ROOT,ID,FLAG,PICTURE,BODY,TITLE,OPTION,render_outputs

class EventTests(unittest.TestCase):
 def setUp(self):
  self.e=next(x for x in load(ROOT/'events/RUS_people_we_events.txt') if x.k=='country_event')
  self.h=load(ROOT/'common/on_actions/RUS_people_we_on_actions.txt')[0].one('on_daily_RUS').one('effect').one('if')
 def test_date_window_and_country_scope(self):
  dates=[n for n in self.h.one('limit').v if n.k=='date']
  def eligible(day,tag='RUS',fired=False):
   return tag=='RUS' and not fired and all(day>datetime.date(*map(int,n.v.split('.'))) if n.op=='>' else day<datetime.date(*map(int,n.v.split('.'))) for n in dates)
  for d in (datetime.date(1936,3,7),datetime.date(1936,3,8),datetime.date(1936,3,9),datetime.date(1937,3,8)):
   self.assertEqual(eligible(d),d==datetime.date(1936,3,8))
  self.assertFalse(eligible(datetime.date(1936,3,8),tag='GER'));self.assertFalse(eligible(datetime.date(1936,3,8),fired=True))
  self.assertEqual(self.e.one('trigger').value('tag'),'RUS')
 def test_once_before_dispatch_and_direct_test_suppresses_later_delivery(self):
  self.assertEqual(self.e.value('fire_only_once'),'yes');self.assertEqual(self.e.value('is_triggered_only'),'yes')
  self.assertEqual(self.e.one('immediate').value('set_country_flag'),FLAG)
  self.assertEqual(self.h.value('set_country_flag'),FLAG);self.assertEqual(self.h.value('country_event'),ID)
  self.assertLess(self.h.one('set_country_flag').a,self.h.one('country_event').a)
  self.assertEqual(self.h.one('limit').one('NOT').value('has_country_flag'),FLAG)
 def test_one_option_and_exact_native_popularity_effect(self):
  opts=self.e.children('option');self.assertEqual(len(opts),1)
  self.assertEqual([n.k for n in opts[0].v],['name','add_popularity'])
  p=opts[0].one('add_popularity');self.assertEqual(p.value('ideology'),'national_populist');self.assertEqual(float(p.value('popularity')),-.01)
  self.assertEqual(opts[0].value('name'),ID+'.a')
 def test_text_and_localisation_integrity(self):
  for lang in ('simp_chinese','english','russian'):
   p=ROOT/f'localisation/{lang}/RUS_people_we_l_{lang}.yml';self.assertTrue(p.read_bytes().startswith(b'\xef\xbb\xbf'))
   lines=p.read_text(encoding='utf-8-sig').splitlines()[1:]
   data={line.strip().split(':0 ',1)[0]:json.loads(line.strip().split(':0 ',1)[1]) for line in lines}
   self.assertEqual(data,{ID+'.t':TITLE,ID+'.d':BODY,ID+'.a':OPTION})
  self.assertEqual(BODY.count('\n\n'),4)
  for name in ('奥尔佳·达尼洛夫娜·特里波列娃','索尼娅·米哈伊里芙娜','安东·舍斯托夫','娜塔莉亚·罗斯托娃','“俄罗斯学生联合会”','“俄罗斯学生联合大会”','“卓雅”'):
   self.assertIn(name,BODY)
 def test_picture_dependency_and_generation(self):
  gfx=(ROOT.parent/'1521695605/interface/kaiserreich/event_pictures.gfx').read_text(encoding='utf-8-sig')
  self.assertIn('name = "'+PICTURE+'"',gfx)
  self.assertTrue((ROOT.parent/'1521695605/gfx/event_pictures/Europe/Russia/GFX_report_event_RUS_protest.png').is_file())
  for path,text in render_outputs().items():self.assertEqual((ROOT/path).read_text(encoding='utf-8-sig'),text)

if __name__=='__main__':unittest.main()
