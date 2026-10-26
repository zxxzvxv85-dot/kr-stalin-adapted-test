"""Package archived HOI4/library artwork; default checks never repaint assets."""
from pathlib import Path
import argparse
import hashlib
import json

ROOT=Path(__file__).resolve().parents[1]
DESIGN=Path('tools/design/education_workbench_20261026')
ART=Path('gfx/interface/RUS_education/workbench')


def spec():
    return json.loads((ROOT/DESIGN/'spec.json').read_text(encoding='utf-8'))


def check_assets():
    data=spec()
    for entry in data['sources'].values():
        path=ROOT/DESIGN/entry['file']
        assert hashlib.sha256(path.read_bytes()).hexdigest()==entry['sha256'],path
    manifest=json.loads((ROOT/DESIGN/'manifest.json').read_text(encoding='utf-8'))
    for entry in manifest['outputs']:
        path=ROOT/entry['path']
        assert hashlib.sha256(path.read_bytes()).hexdigest()==entry['sha256'],path


def render():
    from PIL import Image,ImageOps,ImageEnhance,ImageFilter,ImageDraw
    data=spec()
    images={key:Image.open(ROOT/DESIGN/value['file']).convert('RGBA') for key,value in data['sources'].items()}
    def nine(image,size,borders=(12,12,12,12)):
        left,top,right,bottom=borders;w,h=size
        sx=[0,left,image.width-right,image.width];sy=[0,top,image.height-bottom,image.height]
        dx=[0,left,w-right,w];dy=[0,top,h-bottom,h]
        out=Image.new('RGBA',size)
        for row in range(3):
            for col in range(3):
                tile=image.crop((sx[col],sy[row],sx[col+1],sy[row+1]))
                tile=tile.resize((dx[col+1]-dx[col],dy[row+1]-dy[row]),Image.Resampling.LANCZOS)
                out.alpha_composite(tile,(dx[col],dy[row]))
        return out
    def fit(image,size):
        image=image.crop(image.getchannel('A').getbbox())
        return ImageOps.contain(image,size,Image.Resampling.LANCZOS)
    def paste(out,image,xy,shadow=True):
        if shadow:
            mask=image.getchannel('A').filter(ImageFilter.GaussianBlur(1))
            shade=Image.new('RGBA',image.size,(0,0,0,0));shade.putalpha(mask.point(lambda a:round(a*.5)))
            out.alpha_composite(shade,(xy[0]+1,xy[1]+2))
        out.alpha_composite(image,xy)
    def plate(size):
        out=nine(images['paper_frame'],size,(10,10,10,10))
        dark=images['dark_panel'].resize((size[0]-12,size[1]-12),Image.Resampling.LANCZOS)
        # Match the warm native metal edge; keep bright metric text on a dark face.
        out.alpha_composite(dark,(6,6));return out
    paper_source=images['clipboard'].crop((9,35,491,456))
    def paper(size):return nine(paper_source,size,(6,6,6,6))
    def paper_button(subject,size,box,top=5):
        out=Image.new('RGBA',size)
        sheet=paper((size[0]-8,size[1]-6))
        paste(out,sheet,(4,3))
        icon=fit(subject,box);paste(out,icon,((size[0]-icon.width)//2,top))
        return out
    out={}
    # Anchor the untouched native board at y334, then reflect its grain above
    # and below. Matching edge rows avoid horizontal repeat seams or a colour
    # jump under the native overlay. Use opaque RGB so its ragged alpha edge
    # does not leave black holes at the extension joints.
    wood=images['wood'].convert('RGB');desk=Image.new('RGBA',tuple(data['canvas']))
    for y in range(desk.height):
        phase=(y-334)%(2*wood.height)
        source_y=phase if phase<wood.height else 2*wood.height-1-phase
        desk.paste(wood.crop((0,source_y,wood.width,source_y+1)),(0,y))
    ImageDraw.Draw(desk).rectangle((0,0,desk.width-1,desk.height-1),outline='#66523b',width=2)
    out['desk']=desk
    out['memo']=plate((406,64));out['metric_plate']=plate((160,82))
    out['clipboard']=nine(images['clipboard'],(498,350),(18,44,18,16))
    for row in data['categories']:
        subject=images[row['object']]
        if row['id']==6:
            subject=subject.copy();star=fit(images['star'],(36,36));subject.alpha_composite(star,((subject.width-star.width)//2,(subject.height-star.height)//2))
        out['category_'+str(row['id'])]=paper_button(subject,(72,84),(52,49),7)
    out['intro']=paper_button(images['documents'],(72,68),(44,42),1)
    page=paper_button(images['documents'],(44,44),(26,29),2)
    glass=fit(images['magnifier'],(34,25));paste(page,glass,(9,16));out['page']=page
    selected=nine(images['paper_frame'],(80,92),(9,9,9,9))
    selected=ImageOps.colorize(selected.convert('L'),'#4b3218','#e4c16b').convert('RGBA')
    ImageDraw.Draw(selected).rectangle((5,5,74,86),fill=(0,0,0,0))
    out['selection']=selected
    pockets=Image.new('RGBA',(320,205))
    for frame in range(2):
        pocket=Image.new('RGBA',(160,205));sheet=paper((148,193))
        if frame==0:sheet=ImageEnhance.Color(sheet).enhance(.05)
        paste(pocket,sheet,(6,5))
        draw=ImageDraw.Draw(pocket)
        for y in range(34,176,15):draw.line((18,y,141,y),fill=(100,91,72,65),width=1)
        mark=fit(images['lock'] if frame==0 else images['book'],(44,48))
        mark.putalpha(mark.getchannel('A').point(lambda a:round(a*(.55 if frame==0 else .18))))
        paste(pocket,mark,((160-mark.width)//2,(205-mark.height)//2),False)
        pockets.alpha_composite(pocket,(frame*160,0))
    out['pockets']=pockets
    return out


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--write',action='store_true');parser.add_argument('--check',action='store_true');args=parser.parse_args()
    if args.write:
        outputs=[]
        for name,image in render().items():
            path=ROOT/ART/(name+'.png');path.parent.mkdir(parents=True,exist_ok=True);image.save(path,optimize=True)
            outputs.append({'path':path.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'size':list(image.size)})
        (ROOT/DESIGN/'manifest.json').write_text(json.dumps({'tool':'deterministic Pillow packaging; no image generation','outputs':outputs},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    check_assets();print('PASS: education workbench source/archive and packaged art hashes.')


if __name__=='__main__':main()
