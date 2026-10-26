"""Package individually edited posters; checking never generates or repaints art."""
from pathlib import Path
import hashlib
import json

ROOT=Path(__file__).resolve().parents[1]
DESIGN=Path('tools/design/education_poster_individual_20261026')
WEAR_SPRITES=('GFX_RUS_education_posters','GFX_RUS_education_posters_wear_12',
              'GFX_RUS_education_posters_aged_1','GFX_RUS_education_posters_wear_37',
              'GFX_RUS_education_posters_aged_2','GFX_RUS_education_posters_wear_62',
              'GFX_RUS_education_posters_aged_3')


def paper_bounds(image):
    """Remove transparent padding and isolated generator specks, not poster art."""
    import numpy as np
    alpha=np.array(image.getchannel('A'))>64
    rows=alpha.sum(1);cols=alpha.sum(0)
    ys=np.flatnonzero(rows>rows.max()*.3);xs=np.flatnonzero(cols>cols.max()*.3)
    assert len(xs) and len(ys),'Empty generated poster'
    return (max(0,int(xs[0])-2),max(0,int(ys[0])-2),min(image.width,int(xs[-1])+3),min(image.height,int(ys[-1])+3))


def check_inputs():
    from education_reform_content import ACTIVITIES
    manifest=json.loads((ROOT/DESIGN/'manifest.json').read_text(encoding='utf-8'))
    assert {r['id'] for r in manifest['posters']}=={a['id'] for a in ACTIVITIES}
    assert len({r['edited_source'] for r in manifest['posters']})==len(ACTIVITIES)
    assert len({r['edited_source_sha256'] for r in manifest['posters']})==len(ACTIVITIES)
    for row in manifest['posters']:
        for field in ('original','edited_source','metadata'):
            path=ROOT/row[field]
            assert hashlib.sha256(path.read_bytes()).hexdigest()==row[field+'_sha256'],path
        assert row['alpha_extrema'][0]==0 and row['alpha_extrema'][1]>=250,row['id']
        meta=json.loads((ROOT/row['metadata']).read_text(encoding='utf-8'))
        assert meta['id']==row['id'] and meta['original']==row['original'],row['id']


def record_manifest():
    from PIL import Image
    from education_reform_content import ACTIVITIES
    rows=[]
    for a in ACTIVITIES:
        meta_path=ROOT/DESIGN/(a['id']+'.json')
        meta=json.loads(meta_path.read_text(encoding='utf-8'))
        edited=ROOT/DESIGN/meta['edited_source']
        with Image.open(edited) as image:
            image=image.convert('RGBA');bounds=paper_bounds(image)
            with Image.open(ROOT/meta['original']) as original:
                ratio=(bounds[2]-bounds[0])/(bounds[3]-bounds[1])/(original.width/original.height)
            row={'id':a['id'],'name':a['name'],'original':meta['original'],
                 'edited_source':edited.relative_to(ROOT).as_posix(),'metadata':meta_path.relative_to(ROOT).as_posix(),
                 'size':list(image.size),'alpha_extrema':list(image.getchannel('A').getextrema()),
                 'paper_bounds':list(bounds),'relative_aspect_ratio':ratio}
        for field in ('original','edited_source','metadata'):
            row[field+'_sha256']=hashlib.sha256((ROOT/row[field]).read_bytes()).hexdigest()
        rows.append(row)
    data={'tool':'built-in image_gen, one edit call per poster; model not reported',
          'frame_size':[160,205],'content_fit':[154,199],
          'wear_thresholds':[12.5,25,37.5,50,62.5,75],
          'posters':rows}
    (ROOT/DESIGN/'manifest.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    check_inputs()


def poster_tiles(a,index,originals):
    from PIL import Image,ImageOps,ImageChops,ImageFilter
    import numpy as np
    meta=json.loads((ROOT/DESIGN/(a['id']+'.json')).read_text(encoding='utf-8'))
    source=Image.open(ROOT/DESIGN/meta['edited_source']).convert('RGBA')
    paper=ImageOps.contain(source.crop(paper_bounds(source)),(154,199),Image.Resampling.LANCZOS)
    w,h=paper.size;x,y=(160-w)//2,(205-h)//2
    original=np.array(paper,dtype=float)
    masks=[Image.new('L',(w,h),255)]+[
        im.crop((index*160,0,(index+1)*160,205)).getchannel('A').resize((w,h),Image.Resampling.BILINEAR)
        for im in originals[1:]]
    # These masks only add later edge loss. The initial paper, its folds and
    # printing come from this poster's own edit, never a shared paper backdrop.
    result=[]
    for level in range(7):
        age=level/2;stage=int(age);part=age-stage
        damage=masks[stage] if not part else Image.blend(masks[stage],masks[stage+1],part)
        alpha=ImageChops.multiply(paper.getchannel('A'),damage)
        rgb=original[:,:,:3];luma=rgb.mean(2,keepdims=True)
        rgb=rgb*(1-age*.035)+luma*(age*.035)
        # Gradual print fading and subdued surface abrasion, without moving
        # artwork or replacing the sheet's own crease pattern.
        rgb=rgb*(1-age*.035)+np.array([202,191,165])*(age*.035)
        sheet=Image.fromarray(np.clip(rgb,0,255).astype('uint8'),'RGB').convert('RGBA');sheet.putalpha(alpha)
        tile=Image.new('RGBA',(160,205));shade=Image.new('RGBA',(w+3,h+3))
        shadow_mask=Image.new('L',shade.size);shadow_mask.paste(alpha,(1,1))
        shade.putalpha(shadow_mask.filter(ImageFilter.GaussianBlur(.55)).point(lambda v:round(v*.15)))
        tile.alpha_composite(shade,(x,y));tile.alpha_composite(sheet,(x,y));result.append(tile)
    return result


def render_atlases():
    from PIL import Image
    from education_reform_content import ACTIVITIES
    check_inputs()
    art=ROOT/'gfx/interface/RUS_education'
    originals=[Image.open(art/('posters.dds' if stage==0 else f'posters_aged_{stage}.dds')).convert('RGBA') for stage in range(4)]
    atlases=[Image.new('RGBA',originals[0].size) for _ in range(7)]
    for atlas in atlases:atlas.paste(originals[0].crop((0,0,320,205)),(0,0))
    for index,a in enumerate(ACTIVITIES,2):
        for atlas,tile in zip(atlases,poster_tiles(a,index,originals)):atlas.paste(tile,(index*160,0))
    return {f'posters_posted_{level}':atlas for level,atlas in enumerate(atlases)}


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--record',action='store_true');args=parser.parse_args()
    if args.record:record_manifest()
    check_inputs();print('PASS: all individually edited education posters and source hashes.')
