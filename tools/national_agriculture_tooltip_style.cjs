// Keep display formatting separate from the production and scoring generator.
const terms = [
  {
    '4': ['农业生产','农机生产','库存与贸易','季度报告','实物产量','季节','地力疲劳','实际天气','平均农机覆盖','农业产量修正','行情','市场饱和','销售容量','售价','内需','储备','民用工厂','效率','产出系数','一五当前分数','国家工厂产出','效率上限','效率增长','在役','仓库','累计产量','平均覆盖率','承诺','推广拖拉机','累计自产','库存','优先级','订单','经济盈余','备件','内需积分','政治点','粮食储备','季度任务','可消费余额','年度精神'],
    R: ['预测不保证准确','隐藏天气与行情','停止生产','恶劣天气','损耗','失败后停止积分与兑换','出口没有额外土改积分','粮食短缺','工厂产出'],
    G: ['各永久+2点','土改成功','不降低改革阶段','恢复供给'],
    Y: ['确认后锁定配置','重新调整','自动配置','实际天数','西方同志','巴黎条约','仅交整单','从下一季生效','每农业年度最多12分','每年最多200','乌斯季诺夫','卡霍夫斯卡娅','仅正式土改进行中或成功后发分'],
  },
  {
    '4': ['Physical output','season','soil fatigue','actual weather','average machinery coverage','agricultural output modifiers','Markets','saturation','sales capacity','prices','domestic needs','reserves','civilian factories','efficiency','output factor','five-year-plan score','factory output','efficiency cap','efficiency growth','Domestic target','warehouse cap','Average coverage','cumulative production','crop order','orders','Base surplus','price multiplier','spare reserves','Domestic points','political power','food reserves','quarterly task','spendable balance','Annual spirits'],
    R: ['forecasts may be wrong','hidden weather and markets','adverse weather','wear','spoilage','Failure stops points and exchanges','Exports grant no additional reform points','Food shortages','reduce factory output'],
    G: ['each add 2 permanently','completing reform','without lowering stages','recovering one level'],
    Y: ['Confirmation locks the plan','reopened','allocated automatically','actual days','Western Comrades','Paris treaty','Whole orders only','next quarter','12 per agricultural year','200 per year','Ustinov','Kakhovskaya','Points require ongoing or successful formal reform'],
  },
  {
    '4': ['Урожай','сезона','истощения почвы','фактической погоды','средней обеспеченности техникой','модификаторов выпуска','Рынок','насыщение','ёмкость сбыта','цену','внутренние нужды','резерв','гражданские заводы','эффективность','коэффициент выпуска','очки пятилетки','модификаторы выпуска','предела и роста эффективности','Цель парка','склад','Среднее покрытие','накопленный выпуск','заказ','экономический профицит','множитель','Очки снабжения','политвласти','квартальный запас зерна','задание','расходуемым балансом','Годовые духи'],
    R: ['прогноз может ошибаться','скрытые погоду и рынок','плохой погоде','износ','Потери запасов','Провал останавливает очки и обмен','Экспорт не даёт очков реформы','Нехватка продовольствия','снижает выпуск заводов'],
    G: ['по 2 постоянные единицы','завершение реформы','без снижения этапа','снимает один уровень'],
    Y: ['Утверждённый план','открыть для изменения','автоплан','фактическим дням','Западные товарищи','Парижского договора','Только полные заказы','следующего квартала','12 за сельскохозяйственный год','200 за год','Устиновым','Каховской','Очки выдаются только при действующей или успешной официальной реформе'],
  },
];
const escape = t => t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
const protectedToken = /§[^!](?:(?!§!).)*§!|\[\?[^\]]+\]|\[[^\]]+\]|\$[^$]+\$|£[^£]+£/g;
function outsideTokens(text, transform) {
  let end = 0, result = '';
  for (const match of text.matchAll(protectedToken)) {
    result += transform(text.slice(end, match.index)) + match[0];
    end = match.index + match[0].length;
  }
  return result + transform(text.slice(end));
}
function numbers(text) {
  return outsideTokens(text, plain => plain.replace(/[+-]?\d+(?:[.,]\d+)?%?/g, value => `§${value.startsWith('+') ? 'G' : value.startsWith('-') ? 'R' : 'Y'}${value}§!`));
}
function tooltip(text, language) {
  const colors = new Map(Object.entries(terms[language]).flatMap(([color, words]) => words.map(word => [word, color])));
  const pattern = new RegExp([...colors.keys()].sort((a,b) => b.length-a.length).map(escape).join('|'), 'g');
  return numbers(outsideTokens(text, plain => plain.replace(pattern, word => `§${colors.get(word)}${word}§!`)));
}
const chineseHelp = [
  ['农业生产',
    '£RUS_nat_text_food£ 每季生产配置额度为20，每种作物最多配置10。',
    '农机承诺成功、土改成功各永久增加生产配置额度+2，总额度最多24。',
    '£RUS_nat_text_food£ 实物产量受季节、地力疲劳、实际天气、平均农机覆盖及农业产量修正影响。',
    '预估不计隐藏天气与行情，预测不保证准确。行情、市场饱和与销售容量只影响售价，不减少实物产量。',
    '单位产量表示每单位生产配置的预计实物产出，含当前公开修正及不足整季折算，未配置时也显示。例如单位产量1.25表示每配置1可产出1.25单位作物。',
    '£RUS_nat_text_income£ 各作物出口收入为预估可交付订单的经济盈余，包含可用旧库存。先满足内需并保留储备，无可交付订单时收入为0。下方收入总览还包含农机出口。',
    '£RUS_nat_text_orders£ 确认后锁定配置，季末前可重新调整。',
    '手动调整即时保存，未确认时沿用当前草案结算，下季保留手动配置。自动模式按内需与储备自动配置。首次及截止日的不足整季时段按实际天数结算。'],
  ['农机生产',
    '£RUS_nat_text_machinery£ 分配工厂会实际占用可用民用工厂。',
    '每厂日产 = 1.20 × 效率 × 产出系数',
    '一五当前分数与国家工厂产出、效率上限、效率增长修正参与计算。',
    '£RUS_nat_text_factories£ 新厂以30%效率加权并入。停产时效率每日-0.1%，最低30%。失去工厂时自动减少占用。',
    '国内在役目标已补满且农机仓库已满时停止生产，不增加累计产量。',
    '£RUS_nat_text_stock£ 国内在役农机目标为400单位，土改成功后的下一季提高至500单位。农机仓库上限4500单位。',
    '每季在役农机损耗率随机为10%/15%/20%/25%。恶劣天气使损耗率额外§R+5%§!，最高30%。仓库农机不参与在役损耗。',
    '平均覆盖率按本季每日在役数量计算，使作物产量变为90%至110%，季末补机不能追溯改善整季收成。',
    '£RUS_nat_text_orders£ 作出承诺后540天内须完成推广拖拉机3次，且从农业系统启动起累计自产农机达到3000单位。',
    '初始设备不计入累计自产。出口不扣累计自产成绩。'],
  ['库存与贸易',
    '£RUS_nat_text_food£ 完整和平季度内需：粮食（小麦与黑麦）合计8单位，甜菜2单位，纺织原料（亚麻与棉花）合计4单位。',
    '开季处于战争时，本季粮食内需额外§R+2§!、纺织原料内需额外§R+1§!。',
    '£RUS_nat_text_stock£ 先满足内需，再保留选定的半季/一季/两季储备，最后按优先级交付已接订单。仅交整单，同一库存不可重复交付。',
    '作物库存上限：小麦12、黑麦12、甜菜6、亚麻6、棉花6单位。',
    '满足内需与出口后，剩余作物库存先移除超出上限的部分，再损耗5%。卡霍夫斯卡娅任职时损耗率为2%。已消费、已出口的作物不再损耗。',
    '£RUS_nat_text_export£ 西方同志解锁普通作物订单。',
    '巴黎条约后，存在的不列颠联盟、法兰西公社各提供作物与农机订单，从下一季生效。',
    '每单位作物出口基价为1000经济盈余，每单位农机为150经济盈余。两国已交付订单售价倍率+10%，最终售价倍率40%至150%。',
    '农机出口前先补齐国内在役缺口，再保留在役目标25%的仓库备件，仅剩余农机可出口。'],
  ['季度报告',
    '£RUS_nat_text_reform£ 内需土改积分：粮食全部满足+2，满足90%至不足100%时+1。甜菜、纺织原料各自全部满足时各+0.5。',
    '仅内需这一项土改积分每完整季度最多3，每农业年度最多12，不包含下列储备、农机覆盖和任务积分。',
    '三类内需全部满足额外获得政治点：+50，每农业年度最多200。',
    '£RUS_nat_text_machinery£ 季末损耗后，粮食储备达到一季内需时，土改积分+2。平均农机覆盖至少90%时，土改积分+2。',
    '完成季度任务时，土改积分+4。乌斯季诺夫任职时完成任务，土改积分再+1。',
    '仅正式土改进行中或成功后发放土改积分。不足整季的积分与政治点奖励按实际天数折算。',
    '£RUS_nat_text_reform£ 乌斯季诺夫路线土改目标：150。土改期限：720天。成功后超额积分成为可消费余额，消费不降低改革阶段。',
    '失败后停止积分与兑换，农业继续运转。出口没有额外土改积分。',
    '£RUS_nat_text_food£ 年度精神依据内需平均满足率与年末储备评定。粮食内需满足率不足90%时惩罚加深一级，恢复至至少90%一季降低一级。甜菜或纺织原料短缺影响工厂产出。'],
];
function chinesePresentation(text, key = '') {
  const page = /^RUS_nat_tab_([0-3])_tt$/.exec(key);
  if (page) {
    const [title, ...paragraphs] = chineseHelp[+page[1]];
    return `§Y${title}§!\\n\\n` + paragraphs.map(p => tooltip(p, 0)).join('\\n\\n');
  }
  text = text
    .replace('§R这是保留目标，不会补发库存，也不是储存期限。§!', '')
    .replace(/(\d+(?:\.\d+)?)(§!)?个百分点/g, '$1%$2')
    .replace('每日降低§Y0.1%§!', '每日§R-0.1%§!')
    .replace('§R恶劣天气§!再§G+5%§!', '§R恶劣天气§!再§R+5%§!')
    .replace(/降低5%/g, '§G-5%§!')
    .replace('倍率§G+0.10§!', '倍率§G+10%§!')
    .replace('倍率§Y0.40§!至§Y1.50§!', '倍率§Y40%§!至§Y150%§!')
    .replace(/(\d(?:§!)?)[分点]/g, '$1')
    .replace('全部满足额外§G+50§!§4政治点§!', '全部满足额外获得§4政治点§!：§G+50§!')
    .replace(/；/g, !key || /(?:_tt|_desc|_effect|_cap_open)$/.test(key) ? '。\\n\\n' : '，');
  if (/_soil$/.test(key)) text = text.replace(' 容量 ', ' 销售容量 ');
  const replacements = {
    RUS_nat_needs: [['预计满足', '预计内需满足'], ['加工', '甜菜']],
    RUS_nat_gaps: [['本季缺口', '预计内需缺口'], ['加工', '甜菜']],
    RUS_nat_machine_1: [[/^日产：/, '农机日产：']],
    RUS_nat_machine_2: [['% / ', '% 上限 ']],
    RUS_nat_machine_4: [['  库存：', '  农机库存：']],
    RUS_nat_machine_5: [['。\\n\\n', '，']],
    RUS_nat_reserve_line: [['预计出口：', '预计出口收入：']],
    RUS_nat_report_head: [['  出口：', '  出口收入：'], ['农机损耗：', '农机损耗量：']],
    RUS_nat_report_weather: [['实际天气：', '天气产量修正：'], ['农机行情：', '农机售价修正：']],
    RUS_nat_report_supply: [['供给：', '内需满足：'], ['糖', '甜菜']],
    RUS_nat_report_shortage: [['上年平均供给：', '上年内需满足：']],
  };
  for (const [from, to] of replacements[key] || []) text = text.replace(from, to);
  if (/^RUS_nat_supply_/.test(key)) text = text.replace('加工', '甜菜').replace('预计供给', '供给/内需');
  if (/^RUS_nat_report_(wheat|rye|beet|flax|cotton)$/.test(key)) text = text.replace('实际行情', '售价修正');
  if (/^RUS_nat_report_/.test(key)) text = text.replace(/(\[\?RUS_nat_(?:last_weather|last_machine_market|\w+_last_market))\|2\]/g, '$1|%0]');
  return text.replace('包括最初四项的40', '含最初四项供分40')
    .replace('结算时补粮至90%内需，最多补4单位', '结算时补足粮食内需缺口，最多补充§Y4§!单位，使粮食内需满足率最高补至§Y90%§!');
}
module.exports = function style(loc) {
  const paragraphIcons = [
    ['food','food','orders'], ['machinery','factories','stock','orders'],
    ['food','stock','export'], ['reform','machinery','reform','food'],
  ];
  for (let page=0; page<4; page++) {
    const key = `RUS_nat_tab_${page}_tt`;
    loc[key] = loc[key].map((text, language) => {
      const [title, ...paragraphs] = tooltip(text, language).split('\\n');
      return [title, ...paragraphs.map((paragraph, i) => `£RUS_nat_text_${paragraphIcons[page][i]}£ ${paragraph}`)].join('\\n\\n');
    });
  }
  loc.RUS_nat_tab_1_tt = loc.RUS_nat_tab_1_tt.map((text, language) => {
    const expressions = [
      ['，日产为每厂§Y1.20§!×§4效率§!×§4产出系数§!。', '。\\n\\n每厂日产 = §Y1.20§! × §4效率§! × §4产出系数§!\\n\\n'],
      ['Daily output per factory is §Y1.20§! x §4efficiency§! x §4output factor§!. ', '\\n\\nDaily output per factory = §Y1.20§! x §4efficiency§! x §4output factor§!\\n\\n'],
      ['Выпуск одного завода в сутки: §Y1,20§! x §4эффективность§! x §4коэффициент выпуска§!. ', '\\n\\nВыпуск завода в сутки = §Y1,20§! x §4эффективность§! x §4коэффициент выпуска§!\\n\\n'],
    ];
    const [before, after] = expressions[language];
    if (!text.includes(before)) throw new Error('Machinery formula layout no longer matches locale '+language);
    return text.replace(before, after);
  });
  // Only annotate display values; never alter the variable names or formatting suffixes.
  for (const [key, values] of Object.entries(loc)) {
    if (!key.startsWith('RUS_nat_') || /^RUS_nat_tab_\d_tt$/.test(key)) continue;
    loc[key] = values.map(text => text.replace(protectedToken, token => token.startsWith('[?') ? `§Y${token}§!` : token));
  }
  for (const [key, color] of Object.entries({strong:'G',weak:'R',stable:'Y',weather_good:'G',weather_bad:'R',weather_normal:'Y',saturation:'R',plan_locked:'G',plan_open:'Y',accepted:'G',delivered:'G',cancelled:'g',promise_pending:'Y',promise_kept:'G',promise_failed:'R'})) {
    loc[`RUS_nat_${key}`] = loc[`RUS_nat_${key}`].map(text => `§${color}${text}§!`);
  }
  for (const [key, values] of Object.entries(loc)) {
    values[0] = chinesePresentation(values[0], key);
    if (/^RUS_nat_reserve_[012]_tt$/.test(key)) {
      values[1] = values[1].replace('§RThis is a stock target, not free supplies or a storage duration.§! ', '');
      values[2] = values[2].replace('§RЭто цель запаса, а не бесплатные поставки или срок хранения.§! ', '');
    }
  }
};
module.exports.chinesePresentation = chinesePresentation;
