"""Read-only native card table contract/asset/layout checks (no game claimed)."""
from pathlib import Path
import re
import unittest

from PIL import Image
import doudizhu_gui as gui
from hoi4_politics_blocks import parse

ROOT = Path(__file__).resolve().parents[1]


class CardTableUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = gui.outputs()
        cls.window = parse(cls.sources['interface/RUS_doudizhu.gui'])[0].one('containerWindowType')
        cls.widgets = {n.value('name').strip('"'): n for n in cls.window.v if isinstance(n.v,list) and n.k in {'buttonType','iconType','instantTextBoxType'}}
        cls.script = parse(cls.sources['common/scripted_guis/RUS_doudizhu.txt'])[0].one('RUS_doudizhu_gui')
        cls.triggers = {n.k:n for n in cls.script.one('triggers').v}
        cls.effects = {n.k:n for n in cls.script.one('effects').v}
        cls.properties = {n.k:n for n in cls.script.one('properties').v}

    def test_unique_widget_names(self):
        names = [n.value('name') for n in self.window.v if n.k in {'buttonType','iconType','instantTextBoxType'}]
        self.assertEqual(len(names),len(set(names)))

    def test_every_script_reference_has_widget(self):
        for name in self.triggers:
            base = re.sub(r'_(click_enabled|visible)$','',name)
            self.assertIn(base,self.widgets,name)
        for name in self.effects:
            self.assertIn(name.removesuffix('_click'),self.widgets,name)
        self.assertLessEqual(self.properties.keys(),self.widgets.keys())

    def test_buttons_have_guarded_effects(self):
        for name,widget in self.widgets.items():
            if widget.k!='buttonType':continue
            effect=self.effects[name+'_click']
            guard=effect.one('hidden_effect').one('if').one('limit').raw()
            self.assertIn('has_country_flag = RUS_ddz_open',guard)
            for suffix in ('_visible','_click_enabled'):
                trigger=self.triggers.get(name+suffix)
                if trigger:
                    for child in trigger.v:self.assertIn(child.raw().strip(),guard)

    def test_card_controls_and_dynamic_positions(self):
        for card in range(1,55):
            name=f'ddz_hand_{card}'
            self.assertEqual(self.properties[name].value('x'),f'RUS_ddz_x_{card}')
            self.assertEqual(self.properties[name].value('y'),f'RUS_ddz_y_{card}')
            self.assertIn(f'RUS_ddz_owner_{card} = 1',self.triggers[name+'_visible'].raw())
            self.assertIn('RUS_ddz_phase = 2',self.triggers[name+'_click_enabled'].raw())
            self.assertIn('RUS_ddz_turn = 1',self.triggers[name+'_click_enabled'].raw())
            self.assertIn(f'RUS_ddz_select_{card} = yes',self.effects[name+'_click'].raw())
        self.assertFalse(any(name.startswith('ddz_table_') and name.removeprefix('ddz_table_').isdigit() for name in self.widgets))
        for seat in range(1,4):
            for slot in range(1,21):
                name=f'ddz_public_{seat}_{slot}'
                self.assertEqual(self.properties[name].value('frame'),f'RUS_ddz_public_card_{seat}_{slot}')
                self.assertEqual(self.properties[name].value('x'),f'RUS_ddz_public_x_{seat}_{slot}')
                pos=self.widgets[name].one('position')
                self.assertEqual((int(pos.value('x')),int(pos.value('y'))),gui.public_card_position(seat,slot))

    def test_bidding_and_play_visibility(self):
        for bid in range(4):
            trigger=self.triggers[f'ddz_bid_{bid}_click_enabled'].raw()
            self.assertIn('RUS_ddz_turn = 1',trigger)
            self.assertNotIn('RUS_ddz_bidder',trigger)
            if bid:self.assertIn(f'RUS_ddz_bid < {bid}',trigger)
        self.assertIn('RUS_ddz_last_kind > 0',self.triggers['ddz_pass_click_enabled'].raw())
        self.assertIn('RUS_ddz_phase = 0',self.triggers['ddz_new_visible'].raw())
        self.assertIn('RUS_ddz_phase = 3',self.triggers['ddz_new_visible'].raw())
        self.assertNotIn('RUS_ddz_new_game',self.effects['ddz_close_click'].raw())

    def test_bidding_allowed_before_high_bidder_exists(self):
        # Evaluate the real guard for two important states: an opening auction
        # with no highest bidder, and overcalling a computer's existing bid.
        def allowed(node,values):
            for condition in node.v:
                self.assertEqual(condition.k,'check_variable')
                for comparison in condition.v:
                    actual=values.get(comparison.k,0)
                    expected=float(comparison.v)
                    result={'=':actual==expected,'<':actual<expected,'>':actual>expected}[comparison.op]
                    if not result:return False
            return True
        for bid in range(4):
            trigger=self.triggers[f'ddz_bid_{bid}_click_enabled']
            self.assertTrue(allowed(trigger,{'RUS_ddz_phase':1,'RUS_ddz_turn':1,'RUS_ddz_bidder':0,'RUS_ddz_bid':0}))
        trigger=self.triggers['ddz_bid_3_click_enabled']
        self.assertTrue(allowed(trigger,{'RUS_ddz_phase':1,'RUS_ddz_turn':1,'RUS_ddz_bidder':2,'RUS_ddz_bid':2}))
        self.assertFalse(allowed(trigger,{'RUS_ddz_phase':1,'RUS_ddz_turn':2,'RUS_ddz_bidder':1,'RUS_ddz_bid':2}))

    def test_uniform_native_small_portraits(self):
        for seat in range(1,4):
            widget=self.widgets[f'ddz_person_{seat}']
            self.assertEqual(widget.value('scale'),'1')
        with Image.open(ROOT/gui.ASSET_DIR/'portrait_blank.png') as image:
            self.assertEqual(image.size,(65,67))

    def test_public_action_and_full_name_hover(self):
        definitions = {n.value('name'):n for n in parse(self.sources['common/scripted_localisation/RUS_doudizhu_gui.txt'])}
        loc = dict(re.findall(r'^ ([^ :]+):0 "(.*)"$',self.sources['localisation/RUS_doudizhu_l_simp_chinese.yml'],re.M))
        for seat in range(1,4):
            tooltip=f'RUS_ddz_person_{seat}_tt'
            for name in (f'ddz_person_{seat}',f'ddz_name_{seat}'):
                self.assertEqual(self.widgets[name].value('pdx_tooltip').strip('"'),tooltip)
                self.assertEqual(self.widgets[name].value('alwaystransparent'),'no')
            self.assertIn(f'[GetRUSDDZPerson{seat}Name]',loc[tooltip])
            self.assertIn(f'[GetRUSDDZLastAction{seat}]',loc[tooltip])
            action=definitions[f'GetRUSDDZLastAction{seat}'].raw()
            self.assertIn(f'RUS_ddz_action_{seat} = 1',action)
            self.assertIn(f'RUS_ddz_action_{seat} = 2',action)
            for rank in range(1,16):
                variable=f'RUS_ddz_play_{seat}_{rank}'
                function=definitions[f'GetRUSDDZPlaySeat{seat}Rank{rank}']
                self.assertIn(variable+' > 0',function.raw())
                value=loc[f'RUS_ddz_play_{seat}_{rank}']
                self.assertIn('[?'+variable+'|0]',value)
                for other in ({1,2,3}-{seat}):
                    self.assertNotIn(f'RUS_ddz_play_{other}_',value)
            # Only public played-card snapshots are referenced, never other hands.
            self.assertNotIn('RUS_ddz_owner_',loc[f'RUS_ddz_action_played_{seat}'])

    def test_visible_round_actions_distinguish_new_and_completed_tricks(self):
        from doudizhu_script_model import ScriptModel
        model = ScriptModel({})
        definitions = {n.value('name'): n for n in parse(self.sources['common/scripted_localisation/RUS_doudizhu_gui.txt'])}
        for seat in range(1, 4):
            name = f'ddz_round_action_{seat}'
            self.assertIn(name, self.widgets)
            self.assertEqual(self.widgets[name].one('position').value('y'), '440' if seat == 1 else '353')
            self.assertIn('RUS_ddz_phase > 1', self.triggers[name+'_visible'].raw())
            def label():
                for entry in definitions[f'GetRUSDDZRoundAction{seat}'].children('text'):
                    trigger = entry.one('trigger')
                    if trigger is None or model.check(trigger):
                        return entry.value('localization_key')
                self.fail('No round action fallback')
            model.vars.update({'RUS_ddz_trick': 4, 'RUS_ddz_trick_closed': 0,
                               'RUS_ddz_phase': 2, 'RUS_ddz_people_ready': 1,
                               f'RUS_ddz_action_trick_{seat}': 3, f'RUS_ddz_action_{seat}': 2})
            self.assertEqual(label(), 'RUS_ddz_previous_trick_passed')
            model.vars[f'RUS_ddz_action_trick_{seat}'] = 4
            self.assertEqual(label(), 'RUS_ddz_trick_passed')
            model.vars[f'RUS_ddz_action_{seat}'] = 1
            self.assertEqual(label(), 'RUS_ddz_trick_played')
            model.vars['RUS_ddz_trick_closed'] = 1
            self.assertEqual(label(), 'RUS_ddz_previous_trick_played')
            model.vars[f'RUS_ddz_action_{seat}'] = 2
            self.assertEqual(label(), 'RUS_ddz_previous_trick_passed')
            model.vars.update({'RUS_ddz_trick': 5, 'RUS_ddz_trick_closed': 0})
            self.assertEqual(label(), 'RUS_ddz_previous_trick_passed')
            model.vars['RUS_ddz_phase'] = 3
            self.assertEqual(label(), 'RUS_ddz_trick_ended')
            self.assertTrue(model.check(self.triggers[name+'_visible']))
            # No play ever happened when everyone declined the bid or abandoned
            # during bidding. Do not display a waiting-to-play status then.
            model.vars['RUS_ddz_trick'] = 0
            self.assertFalse(model.check(self.triggers[name+'_visible']))
            model.vars['RUS_ddz_phase'] = 2
            self.assertTrue(model.check(self.triggers[name+'_visible']))

    def test_public_piles_persist_through_pass_other_turn_and_trick_change(self):
        from doudizhu_script_model import ScriptModel
        model=ScriptModel({})
        for seat in range(1,4):
            model.vars.update({'RUS_ddz_phase':2,'RUS_ddz_people_ready':1,'RUS_ddz_trick':3,'RUS_ddz_trick_closed':0,
                               'RUS_ddz_turn':seat,'RUS_ddz_last_player':seat,
                               f'RUS_ddz_action_{seat}':1,f'RUS_ddz_public_n_{seat}':2,
                               f'RUS_ddz_public_card_{seat}_1':29,f'RUS_ddz_public_card_{seat}_2':31,
                               f'RUS_ddz_public_trick_{seat}':3})
            title=self.triggers[f'ddz_public_title_{seat}_visible']
            first=self.triggers[f'ddz_public_{seat}_1_visible']
            second=self.triggers[f'ddz_public_{seat}_2_visible']
            third=self.triggers[f'ddz_public_{seat}_3_visible']
            for changes in ({}, {f'RUS_ddz_action_{seat}':2},
                            {'RUS_ddz_turn':seat%3+1,'RUS_ddz_last_player':seat%3+1},
                            {'RUS_ddz_trick_closed':1}, {'RUS_ddz_trick':4,'RUS_ddz_trick_closed':0},
                            {'RUS_ddz_phase':3}):
                model.vars.update(changes)
                self.assertTrue(model.check(title))
                self.assertTrue(model.check(first))
                self.assertTrue(model.check(second))
                self.assertFalse(model.check(third))
            # A new game clears the seat's count. Even a stale old card ID must
            # stay hidden; another seat's populated pile must not activate it.
            model.vars.update({'RUS_ddz_phase':2,f'RUS_ddz_public_n_{seat}':0})
            self.assertFalse(model.check(title))
            self.assertFalse(model.check(first))
            model.vars.update({'RUS_ddz_people_ready':0,f'RUS_ddz_public_n_{seat}':2})
            self.assertFalse(model.check(title))
            self.assertFalse(model.check(first))
            for slot in range(1,21):
                raw=self.triggers[f'ddz_public_{seat}_{slot}_visible'].raw()
                self.assertNotIn('RUS_ddz_action_',raw)
                self.assertNotIn('RUS_ddz_trick',raw)
                self.assertNotIn('RUS_ddz_last_player',raw)

    def test_public_titles_distinguish_current_target_from_previous_cards(self):
        from doudizhu_script_model import ScriptModel
        model=ScriptModel({})
        definitions={n.value('name'):n for n in parse(self.sources['common/scripted_localisation/RUS_doudizhu_gui.txt'])}
        for seat in range(1,4):
            def label():
                for entry in definitions[f'GetRUSDDZPublicPileTitle{seat}'].children('text'):
                    condition=entry.one('trigger')
                    if condition is None or model.check(condition):
                        return entry.value('localization_key')
            model.vars.update({'RUS_ddz_phase':2,'RUS_ddz_trick':5,'RUS_ddz_trick_closed':0,
                               'RUS_ddz_last_kind':2,'RUS_ddz_last_player':seat,
                               f'RUS_ddz_public_trick_{seat}':5})
            self.assertEqual(label(),f'RUS_ddz_public_current_{seat}')
            for changes in ({'RUS_ddz_trick_closed':1}, {'RUS_ddz_trick_closed':0,'RUS_ddz_trick':6},
                            {'RUS_ddz_trick':5,'RUS_ddz_last_player':seat%3+1},
                            {'RUS_ddz_last_player':seat,'RUS_ddz_phase':3}):
                model.vars.update(changes)
                self.assertEqual(label(),f'RUS_ddz_public_previous_{seat}')

    def test_text_keys_and_dynamic_loc_exist(self):
        loc=self.sources['localisation/RUS_doudizhu_l_simp_chinese.yml']
        entries=re.findall(r'^ ([^ :]+):0 "(.*)"$',loc,re.M)
        keys={key for key,_ in entries}
        self.assertEqual(len(entries),len(keys))
        self.assertEqual(len(entries),len(loc.splitlines())-1,'Unescaped localisation newline or quotation')
        for widget in self.widgets.values():
            for field in ('text','buttonText','pdx_tooltip'):
                value=widget.value(field).strip('"')
                if value:self.assertIn(value,keys)
        for node in parse(self.sources['common/scripted_localisation/RUS_doudizhu_gui.txt']):
            for entry in node.children('text'):
                self.assertIn(entry.value('localization_key'),keys)
        # The roster module supplies live person labels and portrait selectors.
        from doudizhu_roster import outputs as roster_outputs
        scripted='\n'.join(v for p,v in {**self.sources,**roster_outputs(ROOT)}.items() if p.startswith('common/scripted_localisation/'))
        names=set(re.findall(r'\bname\s*=\s*"?([A-Za-z_0-9]+)',scripted))
        for ref in re.findall(r'\[(GetRUSDDZ\w+)\]','\n'.join(self.sources.values())):
            self.assertIn(ref,names)

    def test_static_geometry_inside_window(self):
        for name,widget in self.widgets.items():
            pos=widget.one('position')
            x,y=int(pos.value('x')),int(pos.value('y'))
            self.assertGreaterEqual(x,0,name)
            self.assertGreaterEqual(y,0,name)
            if widget.k=='instantTextBoxType':
                self.assertLessEqual(x+int(widget.value('maxWidth')),1000,name)
                self.assertLessEqual(y+int(widget.value('maxHeight')),680,name)
        # Maximum hand: all ranks/suits are visible in exposed columns; selected
        # cards remain below the selection label and above the footer buttons.
        self.assertLessEqual(gui.HAND_X+19*gui.HAND_STEP+gui.CARD_WIDTH,980)
        self.assertGreaterEqual(gui.HAND_SELECTED_Y,500)
        self.assertLess(gui.HAND_Y+gui.CARD_HEIGHT,614)
        self.assertGreaterEqual(gui.HAND_STEP,25)
        for seat in range(1,4):
            for count in range(1,21):
                rows={}
                for slot in range(1,count+1):
                    x,y=gui.public_card_position(seat,slot,count)
                    self.assertGreaterEqual(x,220)
                    self.assertLessEqual(x+34,780)
                    self.assertGreaterEqual(y,248)
                    self.assertLessEqual(y+50,438)
                    rows.setdefault(y,[]).append(x)
                for positions in rows.values():
                    actual_center=(min(positions)+max(positions)+34)/2
                    self.assertAlmostEqual(actual_center,gui.PUBLIC_PILES[seat]['center'],delta=.5)
                    self.assertLessEqual(len(positions),gui.PUBLIC_PILES[seat]['columns'])
            pile=gui.PUBLIC_PILES[seat]
            self.assertLessEqual(pile['title_y']+22,pile['y'])
        # The two AI piles cannot cross the midline and their second rows stay
        # above the player pile's title. The status line cannot cover any cards.
        self.assertLess(gui.public_card_position(2,10)[0]+34,500)
        self.assertGreater(gui.public_card_position(3,1)[0],500)
        self.assertLessEqual(gui.public_card_position(2,20)[1]+50,358)
        self.assertLessEqual(gui.public_card_position(1,20)[1]+50,438)

    def test_asset_integrity_and_frame_dimensions(self):
        self.assertEqual(gui.validate_assets(ROOT),[])
        for filename,size in [('faces.png',(54*46,68)),('table_faces.png',(54*34,50))]:
            with Image.open(ROOT/gui.ASSET_DIR/filename) as image:
                self.assertEqual(image.size,size)
                self.assertEqual(image.mode,'RGBA')
                for frame in range(54):
                    width=size[0]//54
                    tile=image.crop((frame*width,0,(frame+1)*width,size[1]))
                    self.assertIsNotNone(tile.getbbox())
        gfx=parse(self.sources['interface/RUS_doudizhu.gfx'])[0]
        for sprite in gfx.v:
            with Image.open(ROOT/sprite.value('texturefile').strip('"')) as image:
                self.assertEqual(image.width % int(sprite.value('noOfFrames')),0)

    def test_sprites_exist(self):
        sprites=set(re.findall(r'name\s*=\s*"([^"]+)"',self.sources['interface/RUS_doudizhu.gfx']))
        roots=[ROOT,ROOT.parent/'1521695605',Path('D:/steam/steamapps/common/Hearts of Iron IV')]
        for root in roots:
            for path in (root/'interface').rglob('*.gfx'):
                sprites.update(re.findall(r'name\s*=\s*"?([A-Za-z_0-9]+)',path.read_text(encoding='utf-8-sig',errors='replace')))
        for widget in self.widgets.values():
            for key in ('spriteType','quadTextureSprite'):
                sprite=widget.value(key).strip('"')
                if sprite:self.assertIn(sprite,sprites)


if __name__=='__main__':
    unittest.main(verbosity=2)
