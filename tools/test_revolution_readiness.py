"""Execute shipped upkeep effects against boundary and route fixtures; no game-runtime claim."""
from pathlib import Path
import re, math
ROOT = Path(__file__).resolve().parents[1]
# Reuse the existing Paradox parser, without running its scenario suite.
ns = {"__file__": str(ROOT / "tools/test_regional_diplomacy.py")}
exec((ROOT / "tools/test_regional_diplomacy.py").read_text(encoding="utf-8-sig").split("def country(")[0], ns)
parse, get = ns["parse"], ns["get"]
fx = dict((k,v) for k,_,v in parse((ROOT / "common/scripted_effects/RUS_revolution_readiness_effects.txt").read_text()))
def value(x, c):
 try: return float(x)
 except ValueError: return c["vars"].get(x, 0)
def check(nodes,c):
 def one(k,o,v):
  if k == "has_country_flag": return v in c["flags"]
  if k == "has_power_balance": return c["bop"]
  if k == "NOT": return not check(v,c)
  if k == "OR": return any(one(*n) for n in v)
  if k == "check_variable":
   return all({">=": lambda:value(a,c)>=value(b,c), ">": lambda:value(a,c)>value(b,c), "<": lambda:value(a,c)<value(b,c)}[op]() for a,op,b in v)
  raise AssertionError(k)
 return all(one(*n) for n in nodes)
def run(nodes,c):
 matched=False
 for k,o,v in nodes:
  if k in ("if","else_if","else"):
   if k == "if": matched=False
   if not matched and (k == "else" or check(get(v,"limit",[]),c)):
    run([n for n in v if n[0] != "limit"],c); matched=True
   continue
  matched=False
  if k in fx: run(fx[k],c)
  elif k in ("set_variable","set_temp_variable","add_to_variable","multiply_temp_variable","multiply_variable","divide_variable"):
   for name,_,operand in v:
    x=value(operand,c)
    c["vars"][name]=x if k.startswith("set_") else c["vars"].get(name,0)+x if k=="add_to_variable" else c["vars"].get(name,0)/x if k=="divide_variable" else c["vars"].get(name,0)*x
  elif k=="round_variable": c["vars"][v]=math.floor(c["vars"].get(v,0)+.50000001)
  elif k=="clamp_variable":
   name=get(v,"var");c["vars"][name]=max(float(get(v,"min")),min(float(get(v,"max")),c["vars"].get(name,0)))
  elif k=="add_power_balance_value": c["balance"]=max(-1,min(1,c["balance"]+value(get(v,"value"),c)))
  else: raise AssertionError(k)
def fixture(stage=0,plan=None,land=None,left=True,bop=True,success=False,unlocked=True):
 c={"vars":{},"flags":set(),"bop":bop,"balance":.7}
 if unlocked:c["flags"].add("RUS_europe_intervention_gui_unlocked")
 if left:c["flags"].add("RUS_auto_kamenev_vst_left_path")
 for n in range(1,stage+1):c["flags"].add("RUS_fr_reform_stage_"+str(n))
 if plan is not None:c["vars"]["RUS_first_five_year_plan_score"]=plan
 if land is not None:c["vars"]["RUS_maximalist_land_reform_score"]=land
 if success:c["flags"].add("RUS_maximalist_land_reform_success")
 return c
c=fixture(unlocked=False);run(fx["RUS_revolution_readiness_monthly"],c);assert c["balance"]==.7 and not c["vars"]
run(fx["RUS_revolution_readiness_refresh"],c);assert c["vars"]["RUS_readiness_decay_total"]==0
c["flags"].add("RUS_europe_intervention_gui_unlocked");run(fx["RUS_revolution_readiness_refresh"],c);assert c["balance"]==.7 and c["vars"]["RUS_readiness_decay_total"]==2
run(fx["RUS_revolution_readiness_monthly"],c);assert math.isclose(c["balance"],.68)
count=0
for stage,army in enumerate([.8,.6,.4,.2,0]):
 for plan,p in [(None,.7),(0,.7),(75,.35),(150,0),(200,0),(-10,.7)]:
  for land,l in [(None,.5),(0,.5),(100,.25),(200,0),(300,0),(-10,.5)]:
   c=fixture(stage,plan,land); run(fx["RUS_revolution_readiness_monthly"],c)
   assert math.isclose(c["balance"],.7-math.floor((army+p+l)*10+.50000001)/1000)
   count+=1
c=fixture(left=False);run(fx["RUS_revolution_readiness_monthly"],c);assert math.isclose(c["balance"],.7)
c=fixture(bop=False);run(fx["RUS_revolution_readiness_monthly"],c);assert c["balance"]==.7 and not c["vars"]
c=fixture(4,150,100,success=True);run(fx["RUS_revolution_readiness_monthly"],c);assert math.isclose(c["balance"],.7)
c=fixture(4,150,200);run(fx["RUS_revolution_readiness_refresh"],c);c["vars"]["RUS_first_five_year_plan_score"]-=1;run(fx["RUS_revolution_readiness_monthly"],c);assert math.isclose(c["balance"],.7)
c=fixture();c["balance"]=-.99;run(fx["RUS_revolution_readiness_monthly"],c);assert c["balance"]==-1
for _ in range(3):run(fx["RUS_revolution_readiness_refresh"],c)
assert c["vars"]["RUS_readiness_decay_total"]==2 and c["balance"]==-1
for stage,plan,land,total in [(0,0,0,2),(4,0,0,1.2),(2,75,100,1),(4,150,200,0)]:
 c=fixture(stage,plan,land);run(fx["RUS_revolution_readiness_refresh"],c);assert math.isclose(c["vars"]["RUS_readiness_decay_total"],total)
hooks=(ROOT/"common/on_actions/RUS_future_foreign_policy_on_actions.txt").read_text()
assert hooks.count("RUS_revolution_readiness_monthly = yes")==1
for lang in ["simp_chinese","english","russian"]:
 p=ROOT/"localisation"/lang/("RUS_readiness_balance_l_"+lang+".yml")
 assert p.read_bytes().startswith(bytes([239,187,191]))
 assert "RUS_readiness_decay_tt:" in p.read_text(encoding="utf-8-sig")
print(f"PASS: {count} boundary combinations; route isolation, missing BOP, legacy completion, exchange threshold, floor, refresh idempotence and monthly hook")
