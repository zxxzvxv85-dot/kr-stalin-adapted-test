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
};
