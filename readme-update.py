#!/usr/bin/env python3

import json
import os
import subprocess
import sys
from py_markdown_table.markdown_table import markdown_table

def main() -> int:
    try:
        result = subprocess.run(['git','tag'], stdout=subprocess.PIPE, text=True)
    except Exception as e:
        print(e)
        print("Error: Could not run git tag")
        return -1
    taglist = result.stdout.split("\n")
    out = {}
    out_text = ''
    rel = {'com.deinterlace.nnedi3': {'linux-glibc-x86_64': '✅', 'darwin-x86_64': '✅', 'darwin-aarch64': '✅' },
    'com.ifb.colorbars': {'linux-glibc-x86_64': '✅', 'darwin-x86_64': '✅', 'darwin-aarch64': '✅' },
    'com.vapoursynth.ffms2': {'linux-glibc-x86_64': '✅', 'darwin-x86_64': '✅', 'darwin-aarch64': '✅' }, }
    for t in taglist:
        t = t.strip()
        if t.startswith('vsplugin/') == False:
            continue
        r_info = t.split('/')
        rel.setdefault(r_info[1], {})
        rel[r_info[1]].setdefault(r_info[3], {})
        rel[r_info[1]][r_info[3]] = '✅'
    
    vsrepo = os.listdir(sys.argv[1])
    
    for vsr in vsrepo:
        fp = os.path.join(sys.argv[1], vsr)
        if os.path.splitext(vsr)[1] != '.json':
            continue
        with open(fp) as json_file:
            vsrepo = json.load(json_file)
            json_file.close()
        if vsrepo['type'] != 'VSPlugin':
            continue
        out.setdefault(vsrepo['category'], {})
        out[vsrepo['category']].setdefault(('total'), 0)
        out[vsrepo['category']]['total'] += 1
        fpb = os.path.join(os.path.dirname(os.path.realpath(__file__)),"plugins",vsr)
        if os.path.isfile(fpb):
            with open(fpb) as json_file:
                vspbuild = json.load(json_file)
                json_file.close()
        else:
            continue
        out[vsrepo['category']].setdefault(('plugins'), {})
        out[vsrepo['category']]['plugins'][vspbuild['identifier']] = rel.get(vspbuild['identifier'],{})
        out[vsrepo['category']]['plugins'][vspbuild['identifier']]['Name'] = '['+vspbuild['name']+']('+vspbuild.get('github', vspbuild.get('gitlab', None))+')'
        minos = vspbuild['releases'][0].get('os-min-version', {})
        for x in out[vsrepo['category']]['plugins'][vspbuild['identifier']].keys():
            m = minos.get(x,None)
            if m != None:
                out[vsrepo['category']]['plugins'][vspbuild['identifier']][x] += ' ('+m+')'
        for x in ['linux-glibc-x86_64', 'darwin-x86_64', 'darwin-aarch64']:
            out[vsrepo['category']]['plugins'][vspbuild['identifier']].setdefault(x,'❌')
    out = {k: out[k] for k in sorted(list(out.keys()))}
    for cat, c in out.items():
        if cat in ['Plugin Dependency']:
            continue
        plen = len(c.get('plugins',{}))
        out_text += '\n### '+cat+' ('+str(plen)+'/'+str(c['total'])+')'
        if plen > 0:
            out_list = []
            order = ['Name', 'linux-glibc-x86_64', 'darwin-x86_64', 'darwin-aarch64']
            for i,x in c['plugins'].items():
                out_list.append({k: x[k] for k in order})
            out_text += '\n'+markdown_table(sorted(out_list, key=lambda d: d['Name'].lower())).set_params(row_sep='markdown', quote=False, padding_weight={'Name': 'right', 'linux-glibc-x86_64': 'centerright' , 'darwin-x86_64': 'centerright', 'darwin-aarch64': 'centerright'}).get_markdown()+'\n'
        else:
            out_text += '\n'
    with open("README.template", encoding="utf-8") as f:
        data = f.read()
    data = data.format_map({'PLUGIN_GENERATED_LIST': out_text})
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(data)
    return 0

if __name__ == '__main__':
    sys.exit(main())
