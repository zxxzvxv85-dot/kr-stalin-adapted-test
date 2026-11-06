"""Retain project completion flags used by the national plan, with no GUI or polling."""
import re
from hoi4_politics_blocks import parse

def augment(out):
    import generate_provisional_industry_gui as g
    text=out[g.DECISIONS]
    text=re.sub(r'(?ms)^[ \t]*# RUS_RECOVERY_LEDGER_BEGIN\n.*?^[ \t]*# RUS_RECOVERY_LEDGER_END[ \t]*\n','',text)
    cat=next(n for n in parse(text) if n.k==g.CATEGORY)
    projects=[n for n in cat.v if isinstance(n.v,list) and n.one('days_remove') and n.one('remove_effect')]
    edits=[]
    def observe(n,field,code):
        effect=n.one(field)
        if effect:
            at=effect.ib;line=text.rfind('\n',0,at)+1
            if not text[line:at].strip():at=line;prefix=''
            else:prefix='\n'
            body='hidden_effect = { '+code+' }'
        else:
            at=n.ib;line=text.rfind('\n',0,at)+1
            if not text[line:at].strip():at=line;prefix=''
            else:prefix='\n'
            body=field+' = { hidden_effect = { '+code+' } }'
        edits.append((at,prefix+' # RUS_RECOVERY_LEDGER_BEGIN\n '+body+'\n # RUS_RECOVERY_LEDGER_END\n'))
    for n in projects:
        observe(n,'complete_effect','set_country_flag = RUS_rc_running_'+n.k+' clr_country_flag = RUS_rc_settled_'+n.k+'')
        observe(n,'remove_effect','set_country_flag = RUS_rc_finished_'+n.k+' set_country_flag = RUS_rc_settled_'+n.k+' clr_country_flag = RUS_rc_running_'+n.k+'')
        observe(n,'cancel_effect','set_country_flag = RUS_rc_settled_'+n.k+' clr_country_flag = RUS_rc_running_'+n.k+'')
    for at,s in sorted(edits,reverse=True):text=text[:at]+s+text[at:]
    out[g.DECISIONS]=text
    return out
