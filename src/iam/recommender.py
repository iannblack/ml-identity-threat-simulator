def suggest_removals(findings):
    return [{'action':'replace','member':f['binding']['member'],'from':f['binding']['role'],'to':'roles/viewer'} for f in findings if f['binding']['role'] in {'roles/owner','roles/editor'}]
