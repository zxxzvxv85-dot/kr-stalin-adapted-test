// Offline UI layout proof from the deployed textures; this is not a game capture.
const fs = require('node:fs');
const path = require('node:path');
const {createCanvas, loadImage, GlobalFonts} = require('@napi-rs/canvas');
const root = path.resolve(__dirname, '..');
const out = path.join(root, 'output/intro-theme');
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
  // Final canvas starts at (40,20) inside the 800x880 viewport; add 20px proof margin.
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
  sprite('frame',-4,356); sprite('panel',0,360);
  sprite('content_border',12,432); sprite('content',16,436);
  ['国家','路线指南','游戏教学','鸣谢'].forEach((label,i)=>{
    sprite('tab',45+i*170,382,i===0?1:0,2);
    text(label,106.5+i*170,389,18,'#ece4d3','center');
  });
  sprite('portrait_back',16,436); ctx.drawImage(country,18,438);
  text('— 选项 —',102,692,20,'#ece4d3','center');
  ['自定义成就','地区/胜利点重命名','事件音乐','地区新闻事件','世界新闻事件'].forEach((label,i)=>{
    sprite('checkbox',18,714+i*22,i===4?0:1,2); text(label,48,717+i*22,14);
  });
  text('俄罗斯民主联邦共和国',196,442,18);
  const loc=fs.readFileSync(path.join(root,'../2946487287/localisation/simp_chinese/KR_country_specific/RUS - Russia l_simp_chinese.yml'),'utf8');
  const raw=loc.match(/^ RUS_country_intro_content:\s*"(.*)"$/m)[1].replace(/\\n/g,'\n');
  let x=196,y=470,color='#ece4d3';
  ctx.save(); ctx.beginPath(); ctx.rect(196,464,500,325); ctx.clip();
  const colors={'!':'#ece4d3',P:'#8f958b',o:'#be3426',a:'#9aaca7',l:'#d5b331',m:'#ebe127',t:'#d44c33'};
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
  text('1/4',536,806,18,'#ece4d3','center');
  sprite('continue',240,792); text('继续',360,810,24,'#ece4d3','center');
  ctx.restore();
  text('布局预览 · 非游戏截图；字体与控件状态以游戏内为准',420,902,14,'#d3d0c2','center');
  fs.mkdirSync(out,{recursive:true});
  fs.writeFileSync(path.join(out,'intro-theme-layout.png'),canvas.toBuffer('image/png'));
  console.log(path.join(out,'intro-theme-layout.png'));
}
main().catch(e=>{console.error(e);process.exitCode=1;});
