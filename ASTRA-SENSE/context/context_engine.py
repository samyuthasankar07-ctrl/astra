from utils.privacy import redact_person_label

class ContextEngine:
    def generate(self,persons,objects,interactions):
        objmap={o.track_id:o for o in objects}; lines=[]
        for x in interactions:
            p=next((p for p in persons if p.track_id==x.person_id),None); o=objmap.get(x.object_id)
            if p and o and x.state not in ('NONE','NEAR'):
                verb={'HOLDING':'is holding','CARRYING':'is carrying','PICKING_UP':'is picking up','PUTTING_DOWN':'is putting down','PUSHING':'is pushing','PULLING':'is pulling','THROWING':'is throwing','DROPPING':'is dropping','USING':'is using','REACHING':'is reaching toward'}.get(x.state,f'is {x.state.lower()}')
                lines.append(f'{redact_person_label(f"Person #{p.track_id}")} {verb} {o.class_name} #{o.track_id}.')
        for p in persons:
            if not any(i.person_id==p.track_id and i.state not in ('NONE','NEAR') for i in interactions):
                lines.append(f'{redact_person_label(f"Person #{p.track_id}")} is {p.activity.lower()}.')
        return lines[:12]
