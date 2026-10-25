"""Create the illustrated education decision and full USSR poster catalogue.

Reads the supplied archive without extracting its paths. Does not modify game files.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import math
from pathlib import Path
import zipfile

from PIL import Image, ImageOps
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor
from education_reform_content import ACTIVITIES, CONTROLS, POOL_CAPS, POSTER_CATEGORIES

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT/'tools/design/education_system_20261024/poster_catalog.json'
MODIFIERS = {
 'research_speed_factor':'科研速度', 'industrial_capacity_factory':'工厂产出',
 'stability_factor':'稳定度', 'consumer_goods_factor':'生活消费品工厂系数',
 'political_power_factor':'政治点获取', 'political_power_cost':'每日政治点消耗',
}

def modifier_text(values):
    return '；'.join(f'{MODIFIERS[k]} {v:+g}' if k=='political_power_cost' else f'{MODIFIERS[k]} {v*100:+g}%' for k,v in values.items()) or '无'

def configure(doc):
    section=doc.sections[0];section.page_width=Inches(8.2677);section.page_height=Inches(11.6929)
    section.top_margin=section.bottom_margin=Inches(.60)
    section.left_margin=section.right_margin=Inches(.65)
    for node in list(doc.styles.element.iter(qn('w:pBdr'))):
        node.getparent().remove(node)
    for name in ['Normal','Title','Subtitle','Heading 1','Heading 2','Caption']:
        st=doc.styles[name];st.font.name='Microsoft YaHei';st.font.color.rgb=RGBColor(0,0,0)
        st.element.get_or_add_rPr().get_or_add_rFonts().set(qn('w:eastAsia'),'Microsoft YaHei')
    doc.styles['Normal'].font.size=Pt(10)
    doc.styles['Normal'].paragraph_format.space_after=Pt(5)
    doc.styles['Normal'].paragraph_format.line_spacing=1.12
    doc.styles['Title'].font.size=Pt(24)
    doc.styles['Subtitle'].font.italic=False
    doc.styles['Heading 1'].font.size=Pt(17)
    doc.styles['Heading 2'].font.size=Pt(12)
    doc.core_properties.title='教育改革宣传决议与苏联海报图录'
    doc.core_properties.author=''
    footer=section.footer.paragraphs[0];footer.alignment=WD_ALIGN_PARAGRAPH.CENTER
    r=footer.add_run();r.font.size=Pt(9)
    field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE')
    cached=OxmlElement('w:r');text=OxmlElement('w:t');text.text='1';cached.append(text);field.append(cached);footer._p.append(field)

def table(doc, rows, widths, header=False):
    t=doc.add_table(rows=rows,cols=len(widths));t.alignment=WD_TABLE_ALIGNMENT.CENTER;t.autofit=False
    pr=t._tbl.tblPr;borders=OxmlElement('w:tblBorders')
    for edge in ['top','left','bottom','right','insideH','insideV']:
        n=OxmlElement('w:'+edge);n.set(qn('w:val'),'single');n.set(qn('w:sz'),'5');n.set(qn('w:color'),'D9D9D9');borders.append(n)
    pr.append(borders)
    for row in t.rows:
        no_split=OxmlElement('w:cantSplit');row._tr.get_or_add_trPr().append(no_split)
        for cell,width in zip(row.cells,widths):
            cell.width=Inches(width);cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            margins=OxmlElement('w:tcMar')
            for edge in ['top','left','bottom','right']:
                e=OxmlElement('w:'+edge);e.set(qn('w:w'),'90');e.set(qn('w:type'),'dxa');margins.append(e)
            cell._tc.get_or_add_tcPr().append(margins)
    if header:
        repeat=OxmlElement('w:tblHeader');t.rows[0]._tr.get_or_add_trPr().append(repeat)
        for c in t.rows[0].cells:
            fill=OxmlElement('w:shd');fill.set(qn('w:fill'),'E9EEF2');c._tc.get_or_add_tcPr().append(fill)
    return t

def para(cell,text='',bold=False,size=10):
    p=cell.add_paragraph();r=p.add_run(text);r.bold=bold;r.font.size=Pt(size);return p

def image(cell,data,title,maxw,maxh):
    im=Image.open(io.BytesIO(data)).convert('RGB');im=ImageOps.contain(im,(900,900))
    f=io.BytesIO();im.save(f,format='JPEG',quality=88);f.seek(0)
    scale=min(maxw/im.width,maxh/im.height)
    p=cell.paragraphs[0];p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    shape=p.add_run().add_picture(f,width=Inches(im.width*scale),height=Inches(im.height*scale))
    shape._inline.docPr.set('descr',title)

def build(archive, output):
    manifest=json.loads(DATA.read_text(encoding='utf-8'))
    assert hashlib.sha256(archive.read_bytes()).hexdigest()==manifest['sha256'],'Archive differs from recorded source'
    posters=manifest['posters'];by_code={p['code']:p for p in posters}
    assert len(posters)==len(by_code)==271
    doc=Document();configure(doc)
    doc.add_paragraph('教育改革宣传决议与苏联海报图录','Title')
    doc.add_paragraph('测试版现有宣传效果与完整素材目录','Subtitle')
    doc.add_paragraph('本册列出教育改革系统现有的14项海报宣传与2项热情调节，并按六类收录03_USSR素材包的全部271张海报。已采用海报标明对应决议；其余标明未采用及效果未配置。')
    doc.add_paragraph('素材中文标题用于检索，以画面和原文件名拟定，不作为经过考证的历史正式译名。游戏宣传口号另列，保留模组背景下的改编名称。')
    doc.add_heading('六类目录',1)
    t=table(doc,7,[1.65,1.25,1.1,2.9],True)
    for c,s in zip(t.rows[0].cells,['分类','原文件夹','素材数量','已实装宣传数量']):c.text=s
    for row,(cat,(name,folders)) in zip(t.rows[1:],POSTER_CATEGORIES.items()):
        vals=[name,' '.join(f'{x:02}' for x in folders),str(sum(p['category']==cat for p in posters)),str(sum(a['category']==cat for a in ACTIVITIES))]
        for c,s in zip(row.cells,vals):c.text=s
    doc.add_heading('阅读说明',1)
    doc.add_paragraph('决议页中的教育增量为基础总增量，实际提升受热情和教育路线影响；热情变化按每30天列示。正常完成宣传次数加1，取消不增加次数及永久效果。每类教学活动最多并行1项，总栏位为2项，完成对文化革命后为3项。')
    doc.add_paragraph('六类按钮用于浏览素材主题，不改变基础教育、高等教育、职业技术、文化活动的原有并行限制。热情调节决议在所有分类中保留。')
    doc.add_paragraph('14项宣传完成后的永久修正计入教育改革精神，同类累计上限分别为工厂产出10%、稳定度15%、每日政治点消耗减少0.20、政治点获取10%、科研速度5%。活动临时修正另计。')
    with zipfile.ZipFile(archive) as z:
        for start in range(0,len(ACTIVITIES),3):
            doc.add_page_break();doc.add_heading(f'已实装宣传决议 {start//3+1}',1)
            for a in ACTIVITIES[start:start+3]:
                item=by_code[a['poster']];t=table(doc,1,[2.35,4.55]);left,right=t.rows[0].cells
                image(left,z.read(item['file']),item['title_zh'],2.10,2.25)
                p=left.add_paragraph(f"{item['code']}  {item['title_zh']}");p.alignment=WD_ALIGN_PARAGRAPH.CENTER
                right.paragraphs[0].add_run(a['name']).bold=True
                para(right,'分类  '+POSTER_CATEGORIES[a['category']][0])
                para(right,f"花费 {a['cost']}政治点    持续 {a['days']}天    冷却90天")
                gains=[]
                if a['basic']:gains.append(f"基础教育 +{a['basic']:g}")
                if a['higher']:gains.append(f"高等教育 +{a['higher']:g}")
                para(right,'教育基础增量  '+('；'.join(gains) or '无'))
                para(right,f"热情变化  每30天 {a['heat']:+g}")
                para(right,'期间效果  '+modifier_text(a['modifiers']))
                perm={k:v/5 for k,v in a['modifiers'].items() if k in POOL_CAPS}
                para(right,'完成后永久效果  '+modifier_text(perm))
                access={'basic':'完成共产主义教育理念','higher':'完成对文化革命且基础教育至少35','technical':'完成专业技能培训','culture':'完成对文化革命'}[a['kind']]
                para(right,'解锁条件  '+access,size=9)
                doc.add_paragraph().paragraph_format.space_after=Pt(3)
        doc.add_page_break();doc.add_heading('热情调节与使用规则',1)
        for a in CONTROLS:
            doc.add_heading(a['name'].strip('！'),2)
            condition='热情低于35' if a['id']=='listen' else '热情至少70'
            doc.add_paragraph(f"条件 {condition}。花费20政治点，持续30天，冷却60天。期间每日政治点消耗减少0.025；结束时热情{a['heat']:+g}，永久减少每日政治点消耗0.005。")
        doc.add_paragraph('热情调节不占海报栏位，两项不能同时进行，不计完成宣传次数，也没有单独海报。')
        doc.add_heading('教育系统初值',2)
        doc.add_paragraph('基础教育46，高等教育7，民众热情32。热情每日自然下降0.10；两个教育水平不自然衰减。')
        doc.add_heading('热情与经济动员',2)
        doc.add_paragraph('工厂产出、基础生产效率及生产效率增长的正向收益随热情增强，科研等其他收益不统一放大。基础生产效率最高10%，效率增长最高12.5%；热情提供的工厂产出最高5%，另加已累计的永久贡献。')
        doc.add_paragraph('热情超过75后，每周损失稳定度，损失随热情连续加重：80热情时每周降低0.04个百分点，90时降低0.36，100时降低1。教育收益与其他过热惩罚仍各自生效。')
        doc.add_heading('国策解锁要求',2)
        for line in ['第一组  完成宣传3次，基础教育至少30。','第二组  完成宣传6次，基础教育至少45，高等教育至少15。','第三组  完成宣传10次，基础教育至少60，高等教育至少25。']:
            doc.add_paragraph(line)
        doc.add_heading('素材采用状态',2)
        doc.add_paragraph('已实装14张；未采用257张，均未配置决议效果。未采用素材只收录于后续图录，不加入GUI或可执行决议。')
        for category,(name,folders) in POSTER_CATEGORIES.items():
            entries=[p for p in posters if p['category']==category]
            for start in range(0,len(entries),6):
                doc.add_page_break();doc.add_heading(f'{category} {name} 海报图录 {start//6+1}',1)
                doc.add_paragraph('原文件夹 '+ ' '.join(f'{n:02}' for n in folders)+f'    本类共{len(entries)}张',style='Caption')
                selected=entries[start:start+6];t=table(doc,math.ceil(len(selected)/2),[3.45,3.45])
                for cell,item in zip((c for row in t.rows for c in row.cells),selected):
                    image(cell,z.read(item['file']),item['title_zh'],3.05,1.95)
                    p=para(cell,f"{item['code']}  {item['title_zh']}",True,10);p.alignment=WD_ALIGN_PARAGRAPH.CENTER
                    status='已实装  效果见前文同编号宣传决议' if item['activity'] else '未采用  效果未配置'
                    p=para(cell,status,False,9);p.alignment=WD_ALIGN_PARAGRAPH.CENTER
                    p=para(cell,f"原目录 {item['folder']:02}",False,8);p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    output.parent.mkdir(parents=True,exist_ok=True);doc.save(output)
    print(f'Created {output} ({output.stat().st_size:,} bytes); 271 catalogue entries and 14 illustrated decisions.')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--archive',type=Path,default=Path('C:/Users/Administrator/Downloads/03_USSR.zip'))
    parser.add_argument('--output',type=Path,default=ROOT/'output/education_catalog_20261024/教育改革宣传决议与苏联海报图录.docx')
    args=parser.parse_args();build(args.archive,args.output)
