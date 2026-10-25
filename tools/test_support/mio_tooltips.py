"""Compare donor logic while allowing only the two named display wrappers."""
import copy


def without_merge_display(node):
    node=copy.deepcopy(node)

    def unwrap(fields):
        result=[]
        for field in fields:
            if field.k=='custom_trigger_tooltip' and field.value('tooltip') in ('RUS_odb_not_merged_tt','RUS_adb_not_merged_tt'):
                prefix=field.value('tooltip').removesuffix('_not_merged_tt')
                condition=field.one('NOT')
                assert len(field.v)==2 and condition is not None
                assert len(condition.v)==1 and condition.value('has_country_flag').startswith(prefix+'_merged_')
                result.append(condition)
            else:
                if isinstance(field.v,list):field.v=unwrap(field.v)
                result.append(field)
        return result

    if isinstance(node.v,list):node.v=unwrap(node.v)
    return node.norm()
