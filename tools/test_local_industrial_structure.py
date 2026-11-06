"""Execute emitted state arithmetic and scope/refresh guards; not a combat engine."""
import copy,unittest
from doudizhu_script_model import ScriptModel,load_effects
from hoi4_politics_blocks import load
from generate_local_industrial_structure import ROOT,MOD,render_outputs

FX=load_effects((ROOT/'common/scripted_effects/RUS_local_industrial_structure.txt').read_text())
class Model(ScriptModel):
    def __init__(self,states,tag='RUS'):
        super().__init__(FX);self.states=copy.deepcopy(states);self.tag=tag;self.scope=None
        for state in self.states.values():
            state.setdefault('controller','RUS');state.setdefault('vars',{});state.setdefault('mods',set())
        self.refreshes=0
    def number(self,value):
        if isinstance(value,str) and value.startswith('building_level@'):
            return self.states[self.scope].get(value.split('@')[1],0)
        return super().number(value)
    def check(self,nodes):
        if hasattr(nodes,'v'):nodes=nodes.v
        for n in nodes:
            if n.k=='tag':ok=self.tag==n.v
            elif n.k=='controller':ok=self.states[self.scope]['controller']==n.v[0].v
            elif n.k=='has_dynamic_modifier':ok=n.value('modifier') in self.states[self.scope]['mods']
            else:ok=super().check([n])
            if not ok:return False
        return True
    def state_call(self,sid,name):
        old=self.scope,self.vars;self.scope=sid;self.vars=self.states[sid]['vars']
        self.call(name);self.scope,self.vars=old
    def run(self,nodes):
        handled={'every_controlled_state','add_dynamic_modifier','remove_dynamic_modifier','force_update_dynamic_modifier'}
        pending=[]
        for n in nodes:
            if n.k not in handled:pending.append(n);continue
            if pending:ScriptModel.run(self,pending);pending=[]
            if n.k=='every_controlled_state':
                for sid,state in self.states.items():
                    if state['controller']!=self.tag:continue
                    old=self.scope,self.vars;self.scope=sid;self.vars=state['vars']
                    if self.check(n.one('limit')):self.run([x for x in n.v if x.k!='limit'])
                    self.scope,self.vars=old
            elif n.k=='add_dynamic_modifier':self.states[self.scope]['mods'].add(n.value('modifier'))
            elif n.k=='remove_dynamic_modifier':self.states[self.scope]['mods'].discard(n.value('modifier'))
            else:self.refreshes+=1
        if pending:ScriptModel.run(self,pending)


class Tests(unittest.TestCase):
    def test_examples_and_zero_factories(self):
        for c,m,civ,mil in [(0,0,0,0),(5,0,40/3,0),(10,5,8,-10),(10,10,0,-50/3),(20,5,44/3,-10),(5,20,-50/3,-25)]:
            vm=Model({1:dict(industrial_complex=c,arms_factory=m)})
            vm.call('RUS_lis_refresh_country');v=vm.states[1]['vars']
            self.assertAlmostEqual(v['RUS_lis_civ_speed']*100,civ)
            self.assertAlmostEqual(v['RUS_lis_mil_speed']*100,mil)
            self.assertEqual(vm.states[1]['mods'],{MOD})
    def test_monotonicity_and_asymptotic_bounds(self):
        for c in (0,1,10,100,1000):
            before=None
            for m in range(101):
                vm=Model({1:dict(industrial_complex=c,arms_factory=m)});vm.call('RUS_lis_refresh_country')
                v=vm.states[1]['vars'];pair=v['RUS_lis_civ_speed'],v['RUS_lis_mil_speed']
                self.assertTrue(-.6<pair[0]<.4);self.assertTrue(-.5<pair[1]<=0)
                if before:self.assertLess(pair[0],before[0]);self.assertLess(pair[1],before[1])
                before=pair
        values=[]
        for c in range(30):
            vm=Model({1:dict(industrial_complex=c,arms_factory=5)});vm.call('RUS_lis_refresh_country')
            values.append(vm.states[1]['vars']['RUS_lis_civ_speed'])
        self.assertTrue(all(a<b for a,b in zip(values,values[1:])))
    def test_cache_and_factory_construction_conversion_and_destruction(self):
        vm=Model({1:dict(industrial_complex=10,arms_factory=5)})
        vm.call('RUS_lis_refresh_country');first=copy.deepcopy(vm.states[1])
        for _ in range(5):vm.call('RUS_lis_refresh_country')
        self.assertEqual(vm.states[1],first);self.assertEqual(vm.refreshes,1)
        vm.states[1].update(industrial_complex=9,arms_factory=6);vm.call('RUS_lis_refresh_country')
        self.assertEqual(vm.refreshes,2)
        vm.states[1].update(industrial_complex=0,arms_factory=0);vm.call('RUS_lis_refresh_country')
        self.assertEqual(vm.states[1]['vars']['RUS_lis_civ_speed'],0)
        self.assertEqual(vm.states[1]['vars']['RUS_lis_mil_speed'],0)
    def test_occupied_noncore_postwar_territory_and_control_loss(self):
        vm=Model({1:dict(owner='GER',core=False,industrial_complex=10,arms_factory=5),
                  2:dict(owner='RUS',controller='GER',industrial_complex=20,arms_factory=0)})
        vm.call('RUS_lis_refresh_country');self.assertIn(MOD,vm.states[1]['mods']);self.assertNotIn(MOD,vm.states[2]['mods'])
        vm.states[1]['controller']='GER';vm.state_call(1,'RUS_lis_refresh_state')
        self.assertNotIn(MOD,vm.states[1]['mods'])
        vm.states[2]['controller']='RUS';vm.state_call(2,'RUS_lis_refresh_state')
        self.assertIn(MOD,vm.states[2]['mods'])
        vm.tag='GER';snapshot=copy.deepcopy(vm.states);vm.call('RUS_lis_refresh_country');self.assertEqual(vm.states,snapshot)
    def test_recovery_of_missing_attachment_and_coexistence_with_rural_modifier(self):
        vm=Model({1:dict(industrial_complex=20,arms_factory=5,mods={'RUS_np_rural_infrastructure'})})
        vm.call('RUS_lis_refresh_country');vm.states[1]['mods'].remove(MOD);vm.call('RUS_lis_refresh_country')
        self.assertEqual(vm.states[1]['mods'],{MOD,'RUS_np_rural_infrastructure'})
        dm=load(ROOT/'common/dynamic_modifiers/RUS_local_industrial_structure.txt')[0]
        self.assertEqual({n.k for n in dm.v},{'icon','enable','state_production_speed_industrial_complex_factor','state_production_speed_arms_factory_factor'})
    def test_generation_hooks_and_localisation(self):
        from generation_io import encoded
        for p,t in render_outputs().items():self.assertEqual((ROOT/p).read_bytes(),encoded(p,t))
        actions=load(ROOT/'common/on_actions/RUS_local_industrial_structure.txt')[0]
        self.assertEqual({n.k for n in actions.v},{'on_startup','on_daily_RUS','on_state_control_changed'})
        self.assertIn('FROM.FROM',actions.one('on_state_control_changed').raw())

if __name__=='__main__':unittest.main(verbosity=2)
