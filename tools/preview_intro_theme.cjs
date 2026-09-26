// Offline UI layout proof from the deployed textures; this is not a game capture.
const fs = require('node:fs');
const path = require('node:path');
const {createCanvas, loadImage, GlobalFonts} = require('@napi-rs/canvas');
const root = path.resolve(__dirname, '..');
const out = path.join(root, 'output/intro-theme');
const pageArg = process.argv.indexOf('--page');
const page = pageArg < 0 ? 1 : Number(process.argv[pageArg + 1]);
const history = fs.readFileSync(path.join(root, 'history/countries/RUS - Russia.txt'), 'utf8');
const pages = Number(history.match(/country_intro_page_count\s*=\s*(\d+)/)[1]) + 1;
if (!Number.isInteger(page) || page < 1 || page > pages) throw new Error(`Page must be between 1 and ${pages}`);
function readLoc(file) {
  return Object.fromEntries([...fs.readFileSync(file, 'utf8').matchAll(/^\s*([^#\s:]+):(?:\d+)?\s*"(.*)"\s*$/gm)].map(m => [m[1], m[2]]));
}
const local = readLoc(path.join(root, 'localisation/replace/RUS_country_intro_l_simp_chinese.yml'));
const upstream = readLoc(path.join(root, '../2946487287/localisation/simp_chinese/KR_country_specific/RUS - Russia l_simp_chinese.yml'));
const key = kind => page === 1 ? `RUS_unfinished_october_intro_${kind}` : `RUS_country_intro_${kind}${page === 2 ? '' : `_${page - 2}`}`;
const pageLoc = page === 1 ? local : upstream;
const core = fs.readFileSync(path.join(root, '../1521695605/interface/core.gfx'), 'utf8');
const colors = Object.fromEntries([...core.matchAll(/^\s*([A-Za-z0-9])\s*=\s*\{\s*(\d+)\s+(\d+)\s+(\d+)\s*\}/gm)].map(m => [m[1], `rgb(${m[2]},${m[3]},${m[4]})`]));
colors['!'] = '#ece4d3';
GlobalFonts.registerFromPath('C:/Windows/Fonts/msyh.ttc', 'Microsoft YaHei');
async function main() {
  const canvas = createCanvas(840, 932), ctx = canvas.getContext('2d');
  ctx.fillStyle = '#274b3c'; ctx.fillRect(0, 0, 840, 932);
  const assets = {};
  for (const file of fs.readdirSync(path.join(root,'gfx/interface/rus_intro_theme'))) {
    if (file.endsWith('.png')) assets[file.slice(0,-4)] = await loadImage(path.join(root,'gfx/interface/rus_intro_theme',file));
  }
  const title = await loadImage(path.join(root,'gfx/interface/rus_intro_header/constructivist_title.png'));
  const country = await loadImage(path.join(root,'../1521695605/gfx/introscreen/RUS_intro.png'));
  // One native KR root; offline proof adds margins around its 720x840 contents.
  ctx.save(); ctx.translate(60, 40);
  function sprite(name,x,y,frame=0,frames=1) {
    const im=assets[name], w=im.width/frames;
    ctx.drawImage(im,frame*w,0,w,im.height,x,y,w,im.height);
  }
  function text(value,x,y,size=16,color='#ece4d3',align='left') {
    ctx.font=`${size>=18?'bold ':''}${size}px "Microsoft YaHei"`;
    ctx.fillStyle=color; ctx.textAlign=align; ctx.textBaseline='top'; ctx.fillText(value,x,y);
  }
  sprite('bridge',-4,324);
  ctx.drawImage(title,-31,18,title.width*.42,title.height*.42);
  sprite('underlay',-4,356); sprite('frame',-4,356);
  ['国家','路线指南','游戏教学','鸣谢'].forEach((label,i)=>{
    sprite('tab',45+i*170,382,i===0?1:0,2);
    text(label,106.5+i*170,389,18,'#ece4d3','center');
  });
  sprite('portrait_back',16,436); ctx.drawImage(country,18,438);
  text('— 选项 —',102,692,20,'#ece4d3','center');
  ['自定义成就','地区/胜利点重命名','事件音乐','地区新闻事件','世界新闻事件'].forEach((label,i)=>{
    sprite('checkbox',18,714+i*22,i===4?0:1,2); text(label,48,717+i*22,14);
  });
  text(pageLoc[key('header')],196,442,18);
  const raw=pageLoc[key('content')].replace(/\\n/g,'\n');
  let x=196,y=470,color='#ece4d3';
  ctx.save(); ctx.beginPath(); ctx.rect(196,464,500,325); ctx.clip();
  for (let i=0;i<raw.length;i++) {
    const ch=raw[i];
    if(ch==='§') { color=colors[raw[++i]]||'#ece4d3'; continue; }
    if(ch==='\n') { x=196; y+=20; continue; }
    ctx.font='16px "Microsoft YaHei"'; const advance=ctx.measureText(ch).width;
    if(x+advance>693) {x=196;y+=20;}
    text(ch,x,y,16,color); x+=advance;
  }
  ctx.restore();
  ctx.fillStyle='#746b58';ctx.fillRect(703,464,1,300);ctx.fillRect(701,471,5,79);
  sprite('page',498,800); sprite('back',476,796); sprite('forward',556,796);
  text(`${page}/${pages}`,536,806,18,'#ece4d3','center');
  sprite('continue',240,792); text('继续',360,810,24,'#ece4d3','center');
  ctx.restore();
  text('布局预览 · 非游戏截图；字体与控件状态以游戏内为准',420,902,14,'#d3d0c2','center');
  fs.mkdirSync(out,{recursive:true});
  const output = path.join(out, page === 1 ? 'intro-theme-layout.png' : `intro-theme-page-${page}.png`);
  fs.writeFileSync(output,canvas.toBuffer('image/png'));
  console.log(output);
}
main().catch(e=>{console.error(e);process.exitCode=1;});
