"""Execute generated education scripts. Engine rendering/timing still needs HOI4."""
from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path
import re
import unittest
from itertools import product
from doudizhu_script_model import ScriptModel,load_effects
from hoi4_politics_blocks import load,parse
from education_reform_content import ACTIVITIES,CONTROLS,BODY,POOL_CAPS,education_focuses
from generate_education_reform import ROOT,FX,DEC,DM,GUI,SGUI,GFX,VARS,pv,bv,active,remain,render_outputs,DESIGN,ART

EFFECTS=load_effects((ROOT/FX).read_text(encoding='utf-8-sig'))
DECISIONS={n.k:n for root in load(ROOT/DEC) for n in root.v}

class EducationModel(ScriptModel):
    def __init__(self):
        super().__init__(EFFECTS);self.ideas=set();self.dynamic=set();self.done=set();self.expiry={};self.day=0
    def check(self,nodes):
        if hasattr(nodes,'v'): nodes=nodes.v
        for n in nodes:
            if n.k=='has_idea': ok=n.v in self.ideas
            elif n.k=='has_completed_focus':ok=n.v in self.done
            elif n.k=='has_socialist_government':ok=n.v=='yes'
            elif n.k=='has_dynamic_modifier':ok=n.value('modifier') in self.dynamic
            elif n.k in ('custom_trigger_tooltip','custom_override_tooltip'):ok=self.check([x for x in n.v if x.k!='tooltip'])
            else:ok=super().check([n])
            if not ok:return False
        return True
    def run(self,nodes):
        pending=[]
        native={'remove_ideas','add_ideas','add_dynamic_modifier','remove_dynamic_modifier','force_update_dynamic_modifier','effect_tooltip','custom_effect_tooltip','set_country_flag','add_timed_idea'}
        for n in nodes:
            if n.k not in native:pending.append(n);continue
            if pending:super().run(pending);pending=[]
            if n.k=='set_country_flag':
                if isinstance(n.v,str):self.flags.add(n.v)
                else:self.flags.add(n.value('flag'));self.expiry[n.value('flag')]=self.day+int(n.value('days'))
            elif n.k in ('remove_ideas','add_ideas'):
                self.ideas.discard(n.v) if n.k=='remove_ideas' else self.ideas.add(n.v)
            elif n.k=='add_dynamic_modifier':self.dynamic.add(n.value('modifier'))
            elif n.k=='remove_dynamic_modifier':self.dynamic.discard(n.value('modifier'))
            elif n.k=='add_timed_idea':self.ideas.add(n.value('idea'))
            # Tooltip blocks are display only; never execute their effects.
        if pending:super().run(pending)
    def start(self,aid):
        d=DECISIONS['RUS_education_'+aid]
        if not self.check(d.one('visible')) or not self.check(d.one('available')):return False
        self.run(d.one('complete_effect').v);return True
    def end(self,aid,cancel=False):self.run(DECISIONS['RUS_education_'+aid].one('cancel_effect' if cancel else 'remove_effect').v)
    def advance(self,days,auto_finish=True):
        for _ in range(days):
            self.day+=1
            for f,day in list(self.expiry.items()):
                if day<=self.day:self.flags.discard(f);del self.expiry[f]
            self.call('RUS_education_daily')
            if auto_finish:
                for a in ACTIVITIES+CONTROLS:
                    if active(a) in self.flags and self.vars[remain(a)]<=0:self.end(a['id'])

def initialized():
    m=EducationModel();m.call('RUS_education_initialize');return m

class EducationTests(unittest.TestCase):
    def test_exact_initial_and_optimal_maxima(self):
        m=initialized()
        for mod,(lo,hi,w) in BODY.items():self.assertAlmostEqual(m.vars[bv(mod)],lo)
        m.vars.update({VARS['basic']:100,VARS['higher']:100,VARS['heat']:55});m.call('RUS_education_refresh')
        for mod,(lo,hi,w) in BODY.items():self.assertAlmostEqual(m.vars[bv(mod)],.05 if mod=='political_power_factor' else hi)
        for cap in POOL_CAPS:self.assertEqual(m.vars[pv(cap)],0)
        self.assertEqual(m.dynamic,{'RUS_education_social_capacity'})
    def test_one_education_spirit_includes_pooled_results_without_refresh_stacking(self):
        m=initialized();m.vars.update({VARS['basic']:100,VARS['higher']:100,VARS['heat']:55})
        for mod,cap in POOL_CAPS.items():m.vars[pv(mod)]=cap
        # Remove only the retired attachment, preserving all earned contributions.
        m.dynamic.add('RUS_education_permanent_results');m.call('RUS_education_refresh')
        expected={'research_speed_factor':.20,'industrial_capacity_factory':.10,'stability_factor':.15,'political_power_factor':.15,'political_power_cost':-.20}
        for mod,value in expected.items():self.assertAlmostEqual(m.vars[bv(mod)],value)
        self.assertEqual(m.dynamic,{'RUS_education_social_capacity'})
        before={mod:m.vars[bv(mod)] for mod in expected}
        for _ in range(4):m.call('RUS_education_refresh')
        self.assertEqual(before,{mod:m.vars[bv(mod)] for mod in expected})
        primary=next(n for n in load(ROOT/DM) if n.k=='RUS_education_social_capacity')
        for mod in expected:self.assertEqual(primary.value(mod),bv(mod))
    def test_heat_curve_and_continuity(self):
        m=initialized()
        for t in [0,19.999,20,39.999,40,47.39,54.9999,55,55.0001,69.999,70,84.999,85,100]:
            m.vars[VARS['heat']]=t;m.call('RUS_education_refresh')
            d=(t-55)/(55 if t<=55 else 45);q=1-(.5 if t<=55 else .4)*d*d
            self.assertAlmostEqual(m.vars['RUS_edu_quality'],q,places=10)
            self.assertAlmostEqual(m.vars[bv('stability_factor')],-.05*d*d,places=10)
        for edge in (20,40,55,70,85):
            values=[]
            for t in (edge-.00001,edge+.00001):
                m.vars[VARS['heat']]=t;m.call('RUS_education_refresh');values.append(m.vars['RUS_edu_quality'])
            self.assertLess(abs(values[0]-values[1]),.000001)
        m.vars[VARS['heat']]=47.39;m.call('RUS_education_refresh')
        self.assertAlmostEqual(m.vars['RUS_edu_quality_percent'],99.042777,places=5)
    def test_daily_decay_no_education_decay(self):
        m=initialized();m.advance(30)
        self.assertAlmostEqual(m.vars[VARS['heat']],52)
        self.assertEqual(m.vars[VARS['basic']],20);self.assertEqual(m.vars[VARS['higher']],5)
    def test_entry_only_and_idempotence(self):
        m=EducationModel();m.call('RUS_education_reform_start');self.assertNotIn('RUS_education_system_active',m.flags)
        m.done.add('RUS_future_domestic_205');m.call('RUS_education_reform_start');m.advance(5)
        saved=m.vars.copy();m.call('RUS_education_initialize');self.assertEqual(saved,m.vars)
    def test_slots_kind_conflicts_and_unlocks(self):
        m=initialized();self.assertFalse(m.start('university'));self.assertFalse(m.start('technical'))
        self.assertTrue(m.start('literacy'));self.assertFalse(m.start('schools'))
        m.flags.update({'RUS_edu_culture_open','RUS_edu_technical_open'});m.call('RUS_education_refresh')
        self.assertTrue(m.start('reading'));self.assertTrue(m.start('technical'));self.assertFalse(m.start('science'))
        self.assertEqual(m.vars['RUS_edu_active_count'],3)
        m.end('reading',True);self.assertEqual(m.vars['RUS_edu_active_count'],2)
        self.assertFalse(m.start('reading'));self.assertEqual(m.vars['RUS_education_completed_activities'],0)
    def test_all_activity_lifecycles_and_native_pool_rewards(self):
        for a in ACTIVITIES:
            with self.subTest(a=a['id']):
                m=initialized();m.flags.update({'RUS_edu_culture_open','RUS_edu_technical_open'});m.vars[VARS['basic']]=40;m.call('RUS_education_refresh')
                self.assertTrue(m.start(a['id']));m.advance(a['days']);self.assertNotIn(active(a),m.flags)
                self.assertEqual(m.vars['RUS_education_completed_activities'],1);self.assertEqual(m.vars['RUS_edu_active_count'],0)
                self.assertTrue(all(m.vars[f'RUS_edu_slot_{i}']==0 for i in range(1,4)))
                for mod,v in a['modifiers'].items():
                    if mod in POOL_CAPS:self.assertAlmostEqual(m.vars[pv(mod)],v/5)
                saved={mod:m.vars[pv(mod)] for mod in POOL_CAPS};m.end(a['id']);self.assertEqual(saved,{mod:m.vars[pv(mod)] for mod in POOL_CAPS})
                self.assertEqual(m.vars['RUS_education_completed_activities'],1)
                self.assertFalse(any(x.startswith('RUS_edu_result_') for x in m.dynamic))
    def test_cancellation_and_final_daily_pulse(self):
        m=initialized();m.start('literacy');m.advance(45);self.assertGreater(m.vars[VARS['basic']],20)
        m.end('literacy',True);self.assertEqual(m.vars['RUS_education_completed_activities'],0);self.assertEqual(m.vars[pv('research_speed_factor')],0)
        m=initialized();m.start('literacy');m.advance(89);before=m.vars[VARS['basic']];m.end('literacy')
        self.assertGreater(m.vars[VARS['basic']],before);self.assertEqual(m.vars['RUS_education_completed_activities'],1)
    def test_controls_do_not_use_slots_or_count(self):
        for aid,start in [('listen',20),('restore_order',80)]:
            m=initialized();m.vars[VARS['heat']]=start;m.call('RUS_education_refresh');self.assertTrue(m.start(aid))
            self.assertEqual(m.vars['RUS_edu_active_count'],0);m.advance(30)
            self.assertEqual(m.vars['RUS_education_completed_activities'],0)
            self.assertAlmostEqual(m.vars[VARS['heat']],start-3+(10 if aid=='listen' else -12))
            self.assertAlmostEqual(m.vars[pv('political_power_cost')],-.005)
    def test_permanent_caps_and_all_decimal_inputs(self):
        m=initialized()
        for key in VARS.values():m.vars[key]=123.456
        for mod,cap in POOL_CAPS.items():m.vars[pv(mod)]=100 if cap>0 else -100
        m.call('RUS_education_refresh')
        for key in VARS.values():self.assertEqual(m.vars[key],100)
        for mod,cap in POOL_CAPS.items():self.assertEqual(m.vars[pv(mod)],cap)
        self.assertAlmostEqual(.15+m.vars[pv('research_speed_factor')],.20)
        for mod in POOL_CAPS:
            for a in ACTIVITIES+CONTROLS:
                name='RUS_edu_reward_'+a['id']+'_'+mod
                if name in m.vars:self.assertAlmostEqual(m.vars[name],0)
    def test_routes_multipliers_and_focus_gates(self):
        for theory,central,future in product([False,True],repeat=3):
            m=initialized();m.flags.update({'RUS_edu_theory' if theory else 'RUS_edu_practice','RUS_edu_central' if central else 'RUS_edu_amateur'})
            if future:m.flags.add('RUS_edu_future')
            m.call('RUS_education_refresh')
            self.assertAlmostEqual(m.vars['RUS_edu_basic_multiplier'],(1 if theory else 1.2)*(1 if central else 1.1))
            self.assertAlmostEqual(m.vars['RUS_edu_higher_multiplier'],(1.2 if theory else 1)*(1.2 if future else 1)*(1 if central else 1.1))
            self.assertAlmostEqual(m.vars['RUS_edu_cost_literacy'],20 if central else 25)
        for suffix,n,b,h in [('218',3,30,0),('224',6,45,15),('229',10,60,25)]:
            req=parse('\n'.join(education_focuses()[suffix]['available']))
            m=initialized();m.vars.update({'RUS_education_completed_activities':n,VARS['basic']:b,VARS['higher']:h})
            self.assertTrue(m.check(req))
            for key in ['RUS_education_completed_activities',VARS['basic']]+([VARS['higher']] if h else []):
                m.vars[key]-=.001;self.assertFalse(m.check(req));m.vars[key]+=.001
    def test_no_events_no_old_stacking(self):
        text=(ROOT/FX).read_text(encoding='utf-8-sig')+(ROOT/DEC).read_text(encoding='utf-8-sig')
        self.assertNotIn('country_event =',text);self.assertNotIn('repeat_limit',text)
        self.assertNotIn('RUS_education_recruitable_population_factor',text)
    def test_three_year_bounded_daily_campaign_schedule(self):
        m=initialized();m.flags.update({'RUS_edu_culture_open','RUS_edu_technical_open','RUS_edu_practice','RUS_edu_amateur','RUS_edu_future'});m.call('RUS_education_refresh')
        checkpoints=[]
        for day in range(1095):
            for a in ACTIVITIES:
                if a['id']=='construction' and m.vars[VARS['heat']]>60:continue
                if a['id'] in ('reading','outreach','library') and m.vars[VARS['heat']]<50:continue
                m.start(a['id'])
            if m.vars[VARS['heat']]<35:m.start('listen')
            if m.vars[VARS['heat']]>=70:m.start('restore_order')
            m.advance(1)
            self.assertLessEqual(m.vars['RUS_edu_active_count'],3)
            for v in VARS.values():self.assertGreaterEqual(m.vars[v],0);self.assertLessEqual(m.vars[v],100)
            if day in (364,729,1094):checkpoints.append((m.vars[VARS['basic']],m.vars[VARS['higher']],m.vars[bv('research_speed_factor')] ))
        self.assertLess(checkpoints[0][2],0);self.assertGreater(checkpoints[1][2],0)
        self.assertGreater(checkpoints[2][0],95);self.assertGreater(checkpoints[2][1],70)
        for mod,cap in POOL_CAPS.items():self.assertLessEqual(abs(m.vars[pv(mod)]),abs(cap)+.000001)
    def test_outputs_encoding_assets_and_gui_bounds(self):
        outputs=render_outputs()
        for p,b in outputs.items():self.assertEqual((ROOT/p).read_bytes(),b,str(p))
        for p in outputs:
            if p.suffix=='.yml':
                data=(ROOT/p).read_bytes();self.assertTrue(data.startswith(b'\xef\xbb\xbf'))
                keys=re.findall(r'^ ([\w.]+):',data.decode('utf-8-sig'),re.M);self.assertEqual(len(keys),len(set(keys)))
            else:parse((ROOT/p).read_text(encoding='utf-8-sig'))
        from PIL import Image
        for kind in ('basic','higher','heat','activity'):
            with Image.open(ROOT/ART/(kind+'_bar.dds')) as im:self.assertEqual(im.size,(11918,21))
        with Image.open(ROOT/ART/'posters.dds') as im:self.assertEqual(im.size,(2560,205))
        manifest=json.loads((ROOT/DESIGN/'poster_sources.json').read_text(encoding='utf-8'))
        self.assertEqual(len(manifest['sources']),14)
        for a in manifest['sources']:self.assertEqual(hashlib.sha256((ROOT/a['path']).read_bytes()).hexdigest(),a['sha256'])
        for container in load(ROOT/GUI)[0].v:
            for n in container.v:
                if n.k not in ('iconType','instantTextBoxType'):continue
                pos=n.one('position');x=int(pos.value('x'));y=int(pos.value('y'))
                if n.k=='iconType':
                    sprites={x.value('name').strip('"'):x for root in load(ROOT/GFX) for x in root.v}
                    sprite=sprites[n.value('spriteType').strip('"')];relative=sprite.value('texturefile').strip('"')
                    path=next(r/relative for r in (ROOT,ROOT.parents[3]/'common/Hearts of Iron IV') if (r/relative).is_file())
                    with Image.open(path) as im:w=im.width//int(sprite.value('noOfFrames','1'));h=im.height
                    self.assertLessEqual(y+h,509)
                else:w=int(n.value('maxWidth'))
                self.assertGreaterEqual(x,0);self.assertLessEqual(x+w,498);self.assertGreaterEqual(y,0);self.assertLess(y,509)
    def test_native_bar_art_noticeboard_and_empty_slot_visibility(self):
        from PIL import Image
        game=ROOT.parents[3]/'common/Hearts of Iron IV'
        for kind,source in [('basic','prod_progress_bar2.dds'),('higher','prod_progress_bar2_yellow.dds'),('heat','prod_progress_bar2_red.dds'),('activity','prod_progress_bar2.dds')]:
            with Image.open(ROOT/ART/(kind+'_bar.dds')) as image, Image.open(game/'gfx/interface/prod_progress_bar2_bg.dds') as bg, Image.open(game/'gfx/interface'/source) as fg:
                strip=image.convert('RGBA');base=bg.convert('RGBA');fill=fg.convert('RGBA').crop((0,21,118,42))
                for pct in (0,20,55,100):
                    expected=base.copy();right=round(118*pct/100)
                    if right:expected.alpha_composite(fill.crop((0,0,right,21)),(0,0))
                    self.assertEqual(strip.crop((pct*118,0,(pct+1)*118,21)).tobytes(),expected.tobytes())
                self.assertNotEqual(strip.getpixel((20*118+10,10)),base.getpixel((10,10)),'The native fill layer must be visibly nonempty')
        sprites={x.value('name').strip('"'):x for root in load(ROOT/GFX) for x in root.v}
        self.assertEqual(sprites['GFX_RUS_education_noticeboard'].value('texturefile').strip('"'),'gfx/interface/propaganda/propaganda_bg.dds')
        controls=load(ROOT/GUI)[0].v[0].v;names=[n.value('name').strip('"') for n in controls if n.value('name')]
        self.assertLess(names.index('education_noticeboard'),names.index('poster_1'))
        triggers=load(ROOT/SGUI)[0].v[0].one('triggers');m=initialized()
        for i in range(1,4):
            self.assertFalse(m.check(triggers.one(f'activity_progress_{i}_visible')))
            self.assertFalse(m.check(triggers.one(f'activity_days_{i}_visible')))
        m.start('literacy');self.assertTrue(m.check(triggers.one('activity_progress_1_visible')))
        m.end('literacy',True);self.assertFalse(m.check(triggers.one('activity_progress_1_visible')))
        window=load(ROOT/GUI)[0].v[0]
        self.assertEqual(window.one('position').value('x'),'8')
        by_name={n.value('name').strip('"'):n for n in controls if n.value('name')}
        for kind in ('basic','higher','heat'):
            panel=by_name[kind+'_panel'];px=int(panel.one('position').value('x'));py=int(panel.one('position').value('y'))
            self.assertLess(names.index(kind+'_panel'),names.index(kind+'_label'))
            for suffix,w,h in [('name_panel',150,28),('value_panel',96,22),('label',150,24),('value',96,18),('bar',118,21)]:
                n=by_name[kind+'_'+suffix];x=int(n.one('position').value('x'));y=int(n.one('position').value('y'))
                self.assertGreaterEqual(x,px);self.assertGreaterEqual(y,py)
                self.assertLessEqual(x+w,px+160);self.assertLessEqual(y+h,py+82)
                self.assertEqual(x+w/2,px+80)
            for plate,label,w,h in [('name_panel','label',150,24),('value_panel','value',96,18)]:
                self.assertLess(names.index(kind+'_'+plate),names.index(kind+'_'+label))
                frame=by_name[kind+'_'+plate].one('position');text=by_name[kind+'_'+label].one('position')
                self.assertEqual(frame.value('x'),text.value('x'))
                self.assertGreaterEqual(int(text.value('y')),int(frame.value('y')))
                self.assertLessEqual(int(text.value('y'))+h,int(frame.value('y'))+(28 if plate=='name_panel' else 22))
    def test_education_texticons_transparent_distinct_cool_warm_palettes(self):
        from PIL import Image
        sprites={x.value('name').strip('"'):x for root in load(ROOT/GFX) for x in root.v}
        for kind in ('basic','higher'):
            with Image.open(ROOT/ART/(kind+'_texticon.dds')) as image:
                icon=image.convert('RGBA');self.assertEqual(icon.size,(24,24));self.assertEqual(icon.getchannel('A').getextrema(),(0,255))
                pixels=[icon.getpixel((x,y)) for y in range(24) for x in range(24)];total=sum(c[3] for c in pixels)
                means=[sum(c[i]*c[3] for c in pixels)/total for i in range(3)]
                self.assertGreater(means[2]-means[0] if kind=='basic' else means[0]-means[2],10)
                self.assertEqual(sprites[f'GFX_RUS_edu_{kind}_texticon'].value('texturefile').strip('"'),f'{ART.as_posix()}/{kind}_texticon.dds')

if __name__=='__main__':unittest.main(verbosity=2)
