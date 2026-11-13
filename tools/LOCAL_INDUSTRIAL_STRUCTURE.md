# 地方工业结构（测试开发版，2026-11-06）

用户确认的州级工业集聚机制。C为当地已建成民工等级，M为当地已建成军工等级，I为当地已建成基础设施等级（2026-11-13增加）：

- 当地民工建造速度 = 0.4×C/(C+10) − 0.6×M/(M+20) + 0.02×I。
- 当地军工建造速度 = −0.5×M/(M+20)×(1−0.1×I)，基建减负系数限制在0.5–1之间。
- 民工仍每级基建额外加2个百分点，5级共10个百分点；军工改为每级基建减轻原惩罚的10%，5级减半，无军工时该项始终为0，不产生额外正加成。不替代引擎原有基建加成或乡村修正的5级基建奖励。

从新局on_startup初始化；所有政体下，只要州控制者是RUS就生效，包括非核心、占领及战后新增控制区，不要求所有者是俄罗斯。盟友/加盟国独立控制区不算RUS直接控制。失控即时由on_state_control_changed移除，动态修正enable也按controller禁用；接管则在FROM.FROM州作用域立即重算。

每天由KR既有on_daily_RUS调用every_controlled_state，只检查民工、军工、基建等级缓存和修正是否存在，只有变化才重新计算、挂载及force_update；不在每日遍历世界所有州。建筑转换、拆除、事件增减建筑均由等级变化覆盖；在建项目、工厂临时占用或可用工厂数不参与。实际小数按引擎变量精度和原生提示显示。

修正仅含state_production_speed_industrial_complex_factor和state_production_speed_arms_factory_factor，与“落后的基础设施”等现有加成叠加。没有添加造价字段，不改变其他建筑、基础造价、建筑位、国策、教育、一五分数或原地区修正。没有玩家可点击的初始化决议或额外国策门槛。

原生依据：modifiers_documentation.md的state_production_speed_<Building>；aat_dynamic_modifiers.txt中的州民工速度；effects_documentation.md的every_controlled_state；KR on_actions_Ukraine.txt及原版00_on_actions.txt的控制权变更ROOT/FROM/FROM.FROM说明。动态修正数值由引擎显示，不显示介绍正文或计算算法。

源为generate_local_industrial_structure.py，默认/--check只读，--write生成6份效果、动态修正、on_actions和三语本地化。test_local_industrial_structure.py执行生成后的脚本，验证样例/零工厂、边际递减/范围、缓存防重复、转换拆除、非核心占领/接管失控及与农村修正并存。模型不替代引擎：须完全重启新局核对开局州提示、建造队列加成、建成次日刷新及控制权变化。未额外接入旧档迁移。
