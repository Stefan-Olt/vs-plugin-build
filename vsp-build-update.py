#!/usr/bin/env python3

import argparse
import hashlib
import io
import json
import os
import re
import sys
import tarfile
import urllib.request
from select import select
from typing import Optional
from urllib.parse import urlparse, urlsplit
try:
    import tqdm  # type: ignore
except ImportError:
    pass

test_defaults = {
    "filter": {
        "start": "import vapoursynth as vs\ncore = vs.core\ncore.std.LoadPlugin('{TESTDIR}/{PLUGIN_FILENAME}')\nc = core.std.BlankClip(format=vs.YUV420P8,width=320,height=240,length=10)\nc = core.",
        "end": "\nc.set_output(0)\n"
    },
    "source": {
        "start": "import vapoursynth as vs\ncore = vs.core\ncore.std.LoadPlugin('{TESTDIR}/{PLUGIN_FILENAME}')\nc = core.",
        "end": "\nc.set_output(0)\n"
    }
}

def get_build_system_defaults(btype: str, builddef: dict) -> dict:
    build_system_defaults = {
        "plugin": {
            "autotools": [ { "cmd": [ "tar", "xzf", "{DL_FILENAME}" ] },
                        { "cwd": "{DL_DIRECTORY}", "cmd": [ "./autogen.sh" ] },
                        { "cwd": "{DL_DIRECTORY}", "cmd": [ "./configure", "--prefix={WORKSPACEDIR}" ] },
                        { "cwd": "{DL_DIRECTORY}", "cmd": [ "make", "-j{NPROC}" ] },
                        { "cwd": "{DL_DIRECTORY}", "cmd": [ "make", "install" ] }
                    ],
            "autotools_bs": [ { "cmd": [ "tar", "xzf", "{DL_FILENAME}" ] },
                        { "cwd": "{DL_DIRECTORY}", "cmd": [ "./bootstrap" ] },
                        { "cwd": "{DL_DIRECTORY}", "cmd": [ "./configure", "--prefix={WORKSPACEDIR}" ] },
                        { "cwd": "{DL_DIRECTORY}", "cmd": [ "make", "-j{NPROC}" ] },
                        { "cwd": "{DL_DIRECTORY}", "cmd": [ "make", "install" ] }
                    ],
            "configure": [ { "cmd": [ "tar", "xzf", "{DL_FILENAME}" ] },
                        { "cwd": "{DL_DIRECTORY}", "cmd": [ "chmod", "+x", "configure" ] },
                        { "cwd": "{DL_DIRECTORY}", "cmd": [ "./configure", "--prefix={WORKSPACEDIR}" ] },
                        { "cwd": "{DL_DIRECTORY}", "cmd": [ "make", "-j{NPROC}" ] },
                        { "cwd": "{DL_DIRECTORY}", "cmd": [ "make", "install" ] }
                    ],
            "cmake": [ { "cmd": [ "tar", "xzf", "{DL_FILENAME}" ] },
                        { "cwd": "{DL_DIRECTORY}", "cmd": [ "mkdir", "._vsp_build" ] },
                        { "cwd": "{DL_DIRECTORY}/._vsp_build", "cmd": [ "cmake", "-DCMAKE_INSTALL_PREFIX:PATH={WORKSPACEDIR}", ".." ] },
                        { "cwd": "{DL_DIRECTORY}/._vsp_build", "cmd": [ "make" ] },
                        { "cwd": "{DL_DIRECTORY}/._vsp_build", "cmd": [ "make", "install" ] }
                    ],
            "meson": [ { "cmd": [ "tar", "xzf", "{DL_FILENAME}" ] },
                        { "cwd": "{DL_DIRECTORY}", "cmd": [ "meson", "rewrite", "kwargs", "delete", "target", "", "install_dir", "foobar" ] },
                        { "cwd": "{DL_DIRECTORY}", "cmd": [ "meson", "setup", "--prefix={WORKSPACEDIR}", "--libdir={WORKSPACEDIR}/lib", "build" ] },
                        { "cwd": "{DL_DIRECTORY}", "cmd": [ "ninja", "-C", "build" ] },
                        { "cwd": "{DL_DIRECTORY}", "cmd": [ "ninja", "-C", "build", "install" ] }
                    ],
            "other": [ { "cmd": [ "tar", "xzf", "{DL_FILENAME}" ] } ]
        },
        "dependency": {
            "autotools": [ { "cmd": [ "tar", "xzf", "{DL_FILENAME}" ] },
                        { "cwd": "{DL_DIRECTORY}", "cmd": [ "./autogen.sh" ] },
                        { "flags": { "CFLAGS": "-fPIC", "LDFLAGS": "-fPIC" }, "cwd": "{DL_DIRECTORY}", "cmd": [ "./configure", "--prefix={WORKSPACEDIR}", "--enable-static", "--disable-shared", "--enable-pic" ] },
                        { "cwd": "{DL_DIRECTORY}", "cmd": [ "make", "-j{NPROC}" ] },
                        { "cwd": "{DL_DIRECTORY}", "cmd": [ "make", "install" ] }
                    ],
            "autotools_bs": [ { "cmd": [ "tar", "xzf", "{DL_FILENAME}" ] },
                        { "cwd": "{DL_DIRECTORY}", "cmd": [ "./bootstrap" ] },
                        { "flags": { "CFLAGS": "-fPIC", "LDFLAGS": "-fPIC" }, "cwd": "{DL_DIRECTORY}", "cmd": [ "./configure", "--prefix={WORKSPACEDIR}", "--enable-static", "--disable-shared", "--enable-pic" ] },
                        { "cwd": "{DL_DIRECTORY}", "cmd": [ "make", "-j{NPROC}" ] },
                        { "cwd": "{DL_DIRECTORY}", "cmd": [ "make", "install" ] }
                    ],
            "configure": [ { "cmd": [ "tar", "xzf", "{DL_FILENAME}" ] },
                        { "cwd": "{DL_DIRECTORY}", "cmd": [ "chmod", "+x", "configure" ] },
                        { "flags": { "CFLAGS": "-fPIC", "LDFLAGS": "-fPIC" }, "cwd": "{DL_DIRECTORY}", "cmd": [ "./configure", "--prefix={WORKSPACEDIR}", "--enable-static", "--disable-shared", "--enable-pic" ] },
                        { "cwd": "{DL_DIRECTORY}", "cmd": [ "make", "-j{NPROC}" ] },
                        { "cwd": "{DL_DIRECTORY}", "cmd": [ "make", "install" ] }
                    ],
            "cmake": [ { "cmd": [ "tar", "xzf", "{DL_FILENAME}" ] },
                        { "cwd": "{DL_DIRECTORY}", "cmd": [ "mkdir", "._vsp_build" ] },
                        { "flags": { "CFLAGS": "-fPIC", "LDFLAGS": "-fPIC" }, "cwd": "{DL_DIRECTORY}/._vsp_build", "cmd": [ "cmake", "-DCMAKE_INSTALL_PREFIX:PATH={WORKSPACEDIR}", "-DBUILD_SHARED_LIBS=OFF", "-DCMAKE_POSITION_INDEPENDENT_CODE=ON", ".." ] },
                        { "cwd": "{DL_DIRECTORY}/._vsp_build", "cmd": [ "make" ] },
                        { "cwd": "{DL_DIRECTORY}/._vsp_build", "cmd": [ "make", "install" ] }
                    ],
            "meson": [ { "cmd": [ "tar", "xzf", "{DL_FILENAME}" ] },
                        { "flags": { "CFLAGS": "-fPIC", "LDFLAGS": "-fPIC" }, "cwd": "{DL_DIRECTORY}", "cmd": [ "meson", "setup", "--prefix={WORKSPACEDIR}", "--libdir={WORKSPACEDIR}/lib", "--buildtype=release", "--default-library=static" "build" ] },
                        { "cwd": "{DL_DIRECTORY}", "cmd": [ "ninja", "-C", "build" ] },
                        { "cwd": "{DL_DIRECTORY}", "cmd": [ "ninja", "-C", "build", "install" ] }
                    ],
            "other": [ { "cmd": [ "tar", "xzf", "{DL_FILENAME}" ] } ]
        },
        "buildtool-dependency": {
            "autotools": {
                ".*": [
                        {
                            "name": "automake",
                            "version": [">=", "1.15"]
                        },
                        {
                            "name": "autoconf",
                            "version": [">=", "2.7"]
                        }
                    ],
                    "linux-.*": [
                        {
                            "name": "libtool",
                            "version": [">=", "2.4"]
                        }
                    ],
                    "darwin-.*": [
                        {
                            "name": "glibtool",
                            "version": [">=", "2.4"]
                        }
                    ]
            },
            "autotools_bs": {
                ".*": [
                        {
                            "name": "automake",
                            "version": [">=", "1.15"]
                        },
                        {
                            "name": "autoconf",
                            "version": [">=", "2.7"]
                        }
                    ],
                    "linux-.*": [
                        {
                            "name": "libtool",
                            "version": [">=", "2.4"]
                        }
                    ],
                    "darwin-.*": [
                        {
                            "name": "glibtool",
                            "version": [">=", "2.4"]
                        }
                    ]
            },
            "configure": {
            },
            "cmake": {
                ".*": [
                        {
                            "name": "cmake",
                            "version": [">=", "3.24.0"]
                        }
                    ]
            },
            "meson": {
                ".*": [
                        {
                            "name": "meson",
                            "version": [">=", "0.60.0"]
                        },
                        {
                            "name": "ninja",
                            "version": [">=", "1.10.0"]
                        }
                    ]
            },
            "other": {
            },
        }
    }
    ret = build_system_defaults[btype][builddef['buildsystem']]
    if builddef['buildsystem'] == 'meson' and btype == 'plugin':
        ret[1]['cmd'][5] = builddef['targetname']
    return ret

def data_merge(a, b):
    if isinstance(a, list):
        if isinstance(b, list) == False:
            return None
        for e in b:
            if e not in a:
                a.append(e)
    if isinstance(a, dict):
        if isinstance(b, dict) == False:
            return None
        for e in b.keys():
            if e in a.keys():
                if isinstance(a[e], list) or isinstance(a[e], dict):
                    data_merge(a[e], b[e])
                else:
                    a[e] = b[e]
            else:
                a[e] = b[e]
    return None

def get_git_api_url(url: str) -> Optional[str]:
    if url.startswith('https://github.com/'):
        s = url.strip('/').rsplit('/', 3)
        return f'https://api.github.com/repos/{s[-2]}/{s[-1]}/releases'
    else:
        return None

def get_git_commit_url(url: str, commit: str) -> Optional[str]:
    if url.startswith('https://github.com/'):
        s = url.strip('/').rsplit('/', 3)
        return f'https://api.github.com/repos/{s[-2]}/{s[-1]}/commits/{commit}'
    else:
        return None

def get_gitlab_api_url(url: str) -> str:
    s = url.strip('/').rsplit('/', 3)
    return f'https://{urlsplit(url).hostname}/api/v4/projects/{s[-2]}%2F{s[-1]}/releases'

def get_gitlab_commit_url(url: str, commit: str) -> str:
    print(url)
    s = url.strip('/').rsplit('/', 3)
    return f'https://{urlsplit(url).hostname}/api/v4/projects/{s[-2]}%2F{s[-1]}/repository/commits/{commit}'

def get_gitlab_commit_dl_url(url: str, commit: str) -> str:
    s = url.strip('/').rsplit('/', 3)
    return f'https://{urlsplit(url).hostname}/api/v4/projects/{s[-2]}%2F{s[-1]}/repository/archive.tar.gz?sha={commit}'

def fetch_url(url: str, desc: Optional[str] = None, token: Optional[str] = os.environ.get('GIT_TOKEN')) -> bytearray:
    req = urllib.request.Request(url, headers={'Authorization': 'token ' + token}) if token is not None else urllib.request.Request(url)
    with urllib.request.urlopen(req) as urlreq:
        if ('tqdm' in sys.modules) and (urlreq.headers['content-length'] is not None):
            size = int(urlreq.headers['content-length'])
            remaining = size
            data = bytearray()
            with tqdm.tqdm(total=size, unit='B', unit_scale=True, unit_divisor=1024, desc=desc) as t:
                while remaining > 0:
                    blocksize = min(remaining, 1024*128)
                    data.extend(urlreq.read(blocksize))
                    remaining = remaining - blocksize
                    t.update(blocksize)
            return data
        else:
            print('Fetching: ' + url)
            return urlreq.read()

def create_tar_filename(data: bytearray) -> str:
    file_obj = io.BytesIO(data)
    tar = tarfile.open(fileobj=file_obj, mode="r")
    return os.path.commonprefix(tar.getnames())

def get_tar_buildsystem(data: bytearray) -> str:
    file_obj = io.BytesIO(data)
    tar = tarfile.open(fileobj=file_obj, mode="r")
    prefix = os.path.commonprefix(tar.getnames())
    if os.path.join(prefix,"meson.build") in tar.getnames():
        return "meson"
    if os.path.join(prefix,"CMakeLists.txt") in tar.getnames():
        return "cmake"
    if os.path.join(prefix,"autogen.sh") in tar.getnames():
        return "autotools"
    if os.path.join(prefix,"configure") in tar.getnames():
        return "configure"
    if os.path.join(prefix,"bootstrap") in tar.getnames():
        return "autotools_bs"
    return "other"

def get_meson_target(data: bytearray) -> Optional[str]:
    file_obj = io.BytesIO(data)
    tar = tarfile.open(fileobj=file_obj, mode="r")
    prefix = os.path.commonprefix(tar.getnames())
    meson_file = tar.extractfile(os.path.join(prefix,"meson.build")).read().decode('utf8')
    res = re.search("shared_module\\s*\\(\\s*'([A-Za-z0-9_]+)'", meson_file, flags=re.MULTILINE)
    if res == None:
        return None
    else:
        return str(res[1])
    

def get_tar_additional_files(data: bytearray) -> list:
    ret = []
    file_obj = io.BytesIO(data)
    tar = tarfile.open(fileobj=file_obj, mode="r")
    for n in tar.getnames():
        if n.count('/') != 1:
            continue
        if n.lower().find('readme') > 0 or n.lower().find('license') > 0 or n.lower().find('copying') > 0:
            ret.append('{BUILDDIR}/{DL_DIRECTORY}/'+n.split('/')[1])
    return ret

def get_git_commit(pkg: dict, commit: str) -> Optional[dict]: # version, published, source, filename, hash
    ret = None
    if pkg.get('github', None) != None:
        ret = {}
        com_json = json.loads(fetch_url(get_git_commit_url(pkg['github'], commit)))
        ret['version'] = 'git:'+commit
        ret['published'] = com_json['commit']['committer']['date']
        ret['source'] = pkg['github'].strip('/') + "/archive/"+commit+".tar.gz"
    elif pkg.get('gitlab', None) != None:
        ret = {}
        com_json = json.loads(fetch_url(get_gitlab_commit_url(pkg['gitlab'], commit)))
        ret['version'] = 'git:'+commit
        ret['published'] = com_json['committed_date']
        ret['source'] = get_gitlab_commit_dl_url(pkg['gitlab'], commit)
    else:
        return None
    if ret == {}:
        return ret
    fdata = fetch_url(ret['source'])
    ret['hash'] = hashlib.sha256(fdata).hexdigest()
    ret['filename'] = create_tar_filename(fdata)+".tar.gz" # pkg['github'].rsplit('/', 3)[-1]+"-"+rel['tag_name']+".tar.gz"
    ret['buildsystem'] = get_tar_buildsystem(fdata)
    if ret['buildsystem'] == 'meson':
        ret['targetname'] = get_meson_target(fdata)
    ret['additional_files'] = get_tar_additional_files(fdata)
    return ret

def get_latest_release(pkg: dict, cur_version: str = "", cur_date: Optional[str] = None, force_version: Optional[str] = None) -> Optional[dict]: # version, published, source, filename, hash
    ret = None
    if pkg.get('github', None) != None:
        ret = {}
        rel_json = json.loads(fetch_url(get_git_api_url(pkg['github'])))
        for rel in rel_json:
            if rel['prerelease'] or rel['draft']:
                continue
            if rel['tag_name'] in pkg.get('ignore', []):
                continue
            if force_version != None and rel['tag_name'] != force_version:
                continue
            if rel['tag_name'] != cur_version and (cur_date is None or cur_date < rel['published_at']):
                ret['version'] = rel['tag_name']
                ret['published'] = rel['published_at']
                ret['source'] = pkg['github'].strip('/') + "/archive/refs/tags/"+rel['tag_name']+".tar.gz"
            break
    elif pkg.get('gitlab', None) != None:
        ret = {}
        rel_json = json.loads(fetch_url(get_gitlab_api_url(pkg['gitlab'])))
        for rel in rel_json:
            if rel['upcoming_release']:
                continue
            if rel['tag_name'] in pkg.get('ignore', []):
                continue
            if force_version != None and rel['tag_name'] != force_version:
                continue
            if rel['tag_name'] != cur_version and (cur_date is None or cur_date < rel['released_at']):
                ret['version'] = rel['tag_name']
                ret['published'] = rel['released_at']
                ret['source'] = pkg['gitlab'].strip('/') + "/-/archive/"+rel['tag_name']+"/"+pkg['gitlab'].rsplit('/', 3)[-1]+"-"+rel['tag_name']+".tar.gz"
            break
    else:
        return None
    if ret == {}:
        return ret
    fdata = fetch_url(ret['source'])
    ret['hash'] = hashlib.sha256(fdata).hexdigest()
    ret['filename'] = create_tar_filename(fdata)+".tar.gz" # pkg['github'].rsplit('/', 3)[-1]+"-"+rel['tag_name']+".tar.gz"
    ret['buildsystem'] = get_tar_buildsystem(fdata)
    if ret['buildsystem'] == 'meson':
        ret['targetname'] = get_meson_target(fdata)
    ret['additional_files'] = get_tar_additional_files(fdata)
    return ret

def get_url_pkg(url: str, version: str) -> dict:
    ret = {}
    ret['version'] = version
    ret['source'] = url
    fdata = fetch_url(ret['source'])
    ret['hash'] = hashlib.sha256(fdata).hexdigest()
    ret['filename'] = create_tar_filename(fdata)+".tar.gz" # pkg['github'].rsplit('/', 3)[-1]+"-"+rel['tag_name']+".tar.gz"
    ret['buildsystem'] = get_tar_buildsystem(fdata)
    if ret['buildsystem'] == 'meson':
        ret['targetname'] = get_meson_target(fdata)
    ret['additional_files'] = get_tar_additional_files(fdata)
    return ret

def update_plugin(filename: str, dependencies: bool = False, version_upd: Optional[str] = None, git_upd: Optional[str] = None) -> bool:
    build_def = None
    with open(filename) as json_file:
        build_def = json.load(json_file)
        json_file.close()
    if build_def['type'] != 'VSPlugin':
        print("Error: Don't recognize type of "+build_def['name'])
        return False

    print("Start updating "+build_def['name']+"...")
    # get last release
    build_rel = build_def['releases'][0]
    version = build_rel['version']

    new_deps = {}

    if dependencies == True:
        for k, d in build_def.get('runtime_dependencies', {}).items():
            v = get_latest_release(d, list(d['versions'].keys())[0])
            if v == None:
                print("Cannot auto-update "+k+", only github and gitlab supported at the moment")
                continue
            if v != {}:
                build_def['runtime_dependencies'][k]['versions'][v['version']] = dict(build_def['runtime_dependencies'][k]['versions'][list(d['versions'].keys())[0]])
                del v['buildsystem']
                del v['additional_files']
                if 'targetname' in v.keys():
                    del v['targetname']
                build_def['runtime_dependencies'][k]['versions'][v['version']].update(v)
                new_deps[k] = v['version']
                print("Updated "+k+" to version "+v['version'])
            else:
                print(k+" already lastest version")
    
    if git_upd != None:
        v = get_git_commit(build_def, git_upd)
    else:
        v = get_latest_release(build_def,build_def['releases'][0]['version'], build_def['releases'][0]['published'], version_upd)
    if v == None:
        print("Cannot auto-update "+build_def['name']+", only github and gitlab supported at the moment")
    if v == {}:
        print(build_def['name']+" already lastest version")
    if v == None or v == {}:
        if len(new_deps)>0:
            print("Will only update dependencies")
        else:
            print("Nothing to update...")
            return False
    if 'buildsystem' in v.keys():
        del v['buildsystem']
    if 'additional_files' in v.keys():
        del v['additional_files']
    if 'targetname' in v.keys():
        del v['targetname']
    build_def['releases'].insert(0, dict(build_def['releases'][0]))
    build_def['releases'][0].update(v)
    #for k, d in new_deps:
    for k in build_def['releases'][0]['build'].keys():
        for i in range(len(build_def['releases'][0]['build'][k]['dependencies'])):
            v = new_deps.get(build_def['releases'][0]['build'][k]['dependencies'][i]['name'], None)
            if v != None:
                build_def['releases'][0]['build'][k]['dependencies'][i]['version'] = v
    with open(filename,"w") as json_file:
        json_file.write(json.dumps(build_def, indent='\t'))
        json_file.close()

    return True

def new_dependency(dependencies: dict, new_dependencies: list = []) -> list:
    out = {}
    for d in new_dependencies:
        dep = {}
        if d.get('url', None) == None:
            if d.get('git_com', None) != None:
                v = get_git_commit(d, d['git_com'])
            else:
                v = get_latest_release(d, None, None, d['version'])
        else:
            v = get_url_pkg(d['url'], d['version'])
        if d['name'] in dependencies.keys():
            dependencies[d['name']]['versions'][v['version']] = v
        else:
            dependencies[d['name']] = { 'versions': { v['version'] : v } }
        for k in set.intersection({'github','gitlab'},d.keys()):
             dependencies[d['name']][k] = d[k]
        dependencies[d['name']]['versions'][v['version']]['build'] = { '.*': { 'commands': get_build_system_defaults('dependency',dependencies[d['name']]['versions'][v['version']]) } }
        data_merge(out, get_build_system_defaults('buildtool-dependency',dependencies[d['name']]['versions'][v['version']]))
        #dependencies[d['name']]['versions'][v['version']]['build'] = { '.*': { 'commands': build_system_defaults['dependency'][dependencies[d['name']]['versions'][v['version']]['buildsystem']] } }
        #data_merge(out, build_system_defaults['buildtool-dependency'][dependencies[d['name']]['versions'][v['version']]['buildsystem']])
       
        del v['buildsystem']
        del v['additional_files']
        if 'targetname' in list(v.keys()):
            del v['targetname']
    return out

def new_plugin(vsrepofile: str, dependencies: list = [], tests: list = [], version: Optional[str] = None, git_upd: Optional[str] = None, gh_source: Optional[str] = None, gl_source: Optional[str] = None, url_source: Optional[str] = None) -> bool:
    build_def = {}
    vsrepo = None
    with open(vsrepofile) as json_file:
        vsrepo = json.load(json_file)
        json_file.close()
    if vsrepo['type'] != 'VSPlugin':
        print("Error: This will only work with type VSPlugin, "+vsrepo['name']+" is of type "+vsrepo['type'])
        return False

    print("Start creating build definition for "+vsrepo['name']+"...")
    
    build_def['name'] = vsrepo['name']
    build_def['type'] = vsrepo['type']
    build_def['description'] = vsrepo['description']
    build_def['identifier'] = vsrepo['identifier']
    if 'github' in vsrepo.keys():
        build_def['github'] = vsrepo['github']
    if gh_source != None:
        build_def['github'] = gh_source[0]
    if gl_source != None:
        build_def['gitlab'] = gl_source[0]
        del build_def['github']
    if url_source != None:
        del build_def['github']
        del build_def['gitlab']
    # get last release

    if url_source == None:
        if git_upd != None:
            v = get_git_commit(build_def, git_upd)
        else:
            v = get_latest_release(build_def, None, None, version)
    else:
        v = get_url_pkg(url_source, version)
    if v == {} or v == None:
        print("Could not find any release or specified version of plugin "+build_def['name']+", you have to use a specific git commit")
        return False
    build_def['file_definitions'] = {}
    build_def['tests'] = []
    if len(tests) == 0:
        tests.append({ 'type': 'filter', 'test': vsrepo['namespace'].title()+'(c)' })
    for i,t in enumerate(tests):
        build_def['file_definitions']['test-'+t['type']+'-'+str(i)+'.vpy'] = { "path": "{TESTDIR}", "encoding": "text/utf-8", "data": test_defaults[t['type']]['start']+vsrepo['namespace']+'.'+vsrepo['namespace'].title()+'(c)'+test_defaults[t['type']]['end'] }
        build_def['tests'].append({ "name" : 'test-'+t['type']+'-'+str(i), "create_files" : ['test-'+t['type']+'-'+str(i)+'.vpy'], "commands": [ { "cwd": "{TESTDIR}", "cmd": ["{VSPIPE}", 'test-'+t['type']+'-'+str(i)+'.vpy', "--"] } ]})
    deps = {}
    buildtools = new_dependency(deps, dependencies)
    if deps != {}:
        build_def["runtime_dependencies"] = deps
    #print(v)
    build_def["releases"] = [v]
    #build_def["releases"][0]['build'] = { '.*': { 'commands': build_system_defaults['plugin'][build_def["releases"][0]["buildsystem"]] } }
    #data_merge(buildtools, build_system_defaults['buildtool-dependency'][build_def["releases"][0]["buildsystem"]])
    build_def["releases"][0]['build'] = { '.*': { 'commands': get_build_system_defaults('plugin',build_def["releases"][0]) } }
    data_merge(buildtools, get_build_system_defaults('buildtool-dependency',build_def["releases"][0]))
    build_def["releases"][0]["buildtools_dependencies"] = buildtools
    if build_def["releases"][0]["buildsystem"] == "other":
        print("Could not auto-detect build system of plugin "+build_def['name']+", you have to add build commands manually to json")
        #return False
    else:
        print("Detected build-system "+build_def["releases"][0]["buildsystem"]+" for plugin "+build_def['name']+" and created default commands, may need adjustment")

    build_def["releases"][0]['build']['.*']["dependencies"] = []
    for d in deps.keys():
        build_def["releases"][0]['build']['.*']["dependencies"].append({ 'name': d, 'version': list(deps[d]['versions'].keys())[0] })
    build_def["releases"][0]["release_files"] = { "linux-.*": [ "{WORKSPACEDIR}/lib/lib"+v.get('targetname',build_def['name'].lower())+".so" ], "darwin-.*": [ "{WORKSPACEDIR}/lib/lib"+v.get('targetname',build_def['name'].lower())+".dylib" ]}
    if len(build_def["releases"][0]["additional_files"]) > 0:
        build_def["releases"][0]["additional_files"] = { '.*': build_def["releases"][0]["additional_files"] }
    else:
        del v['additional_files']
    build_def["releases"][0]["tests"] = { '.*': [ 'test-'+t['type']+'-'+str(i) for i,t in enumerate(tests) ] }
    del v['buildsystem']
    if 'targetname' in list(v.keys()):
        del v['targetname']
    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)),"plugins",os.path.splitext(os.path.basename(vsrepofile))[0]+'.json'),"w") as json_file:
        json_file.write(json.dumps(build_def, indent='\t'))
        json_file.close()

    return True

def main() -> int:
    global config_vars, platform

    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--version", type=str, help="add specific version of plugin", default=None)
    parser.add_argument("-g", "--git-commit", type=str, help="add specific git-commit of plugin", default=None)
    parser.add_argument("-d", "--update-dependencies", help="update dependencies of plugin", default=False, action='store_true')
    parser.add_argument("-n", "--new-plugin", help="create new build definition for plugin", default=False, action='store_true')
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--github-source", nargs=1, type=str, default=None, help="github url of plugin")
    group.add_argument("--gitlab-source", nargs=1, type=str, default=None, help="gitlab url of plugin")
    group.add_argument("--url-source", nargs=1, default=None, type=str, help="version and source-url of plugin")
    parser.add_argument("--github-dependency", nargs=1, type=str, action='append', default=[], help="add github dependency of plugin")
    parser.add_argument("--gitlab-dependency", nargs=1, type=str, action='append', default=[], help="add gitlab dependency of plugin")
    parser.add_argument("--github-dependency-version", nargs=2, metavar=('SOURCE', 'VERSION'), default=[], type=str, action='append', help="add github dependency of plugin")
    parser.add_argument("--gitlab-dependency-version", nargs=2, metavar=('SOURCE', 'VERSION'), default=[], type=str, action='append', help="add gitlab dependency of plugin")
    parser.add_argument("--github-dependency-commit", nargs=2, metavar=('SOURCE', 'COMMIT_SHA'), default=[], type=str, action='append', help="add github dependency of plugin")
    parser.add_argument("--gitlab-dependency-commit", nargs=2, metavar=('SOURCE', 'COMMIT_SHA'), default=[], type=str, action='append', help="add gitlab dependency of plugin")
    parser.add_argument("--url-dependency", nargs=3, metavar=('URL', 'NAME', 'VERSION'), action='append', default=[], type=str, help="name, version and source-url of dependency")
    parser.add_argument("--test-filter", nargs=1, type=str, action='append', default=[], help="add filter test (input clip is called c)")
    parser.add_argument("--test-source", nargs=1, type=str, action='append', default=[], help="add source test")
    parser.add_argument("plugin", type=str, help="plugin to add/update (ALL for updating all)")

    args = parser.parse_args()

    if args.url_source != None and args.version == None:
        print("--url-source requires --version argument!")
        return 1


    deps = []
    for d in args.github_dependency:
        deps.append({'github': d[0], 'version': None, 'git_com': None})
    for d in args.gitlab_dependency:
        deps.append({'gitlab': d[0], 'version': None, 'git_com': None})
    for d in args.github_dependency_version:
        deps.append({'github': d[0], 'version': d[1], 'git_com': None})
    for d in args.gitlab_dependency_version:
        deps.append({'gitlab': d[0], 'version': d[1], 'git_com': None})
    for d in args.github_dependency_commit:
        deps.append({'github': d[0], 'version': None, 'git_com': d[1]})
    for d in args.gitlab_dependency_commit:
        deps.append({'gitlab': d[0], 'version': None, 'git_com': d[1]})
    for d in args.url_dependency:
        deps.append({'url': d[0], 'name': d[1], 'version': d[2]})
    tests = []
    for t in args.test_filter:
        deps.append({'type': 'filter', 'test': t[0]})
    for t in args.test_source:
        deps.append({'type': 'source', 'test': t[0]})
    for d in deps:
        if 'github' in d.keys():
            d['name'] = d['github'].strip('/').rsplit('/', 1)[-1]
        elif 'gitlab' in d.keys():
            d['name'] = d['gitlab'].strip('/').rsplit('/', 1)[-1]
    if args.new_plugin == False:
        if args.plugin == 'ALL':
            plugin_list = os.listdir(os.path.join(os.path.dirname(os.path.realpath(__file__)),"plugins"))
            for p in plugin_list:
                if update_plugin(os.path.join(os.path.dirname(os.path.realpath(__file__)),"plugins",p), args.update_dependencies, args.version, args.git_commit) is True:
                    print("Updated plugin: "+os.path.splitext(p)[0])
        else:
            plugin_json = args.plugin
            if plugin_json.endswith('.json') is False:
                plugin_json = os.path.join(os.path.dirname(os.path.realpath(__file__)),"plugins",plugin_json+'.json')
            if update_plugin(plugin_json, args.update_dependencies, args.version, args.git_commit) is True:
                return 0
    else:
        if new_plugin(args.plugin, deps, tests, args.version, args.git_commit, args.github_source, args.gitlab_source, args.url_source) is True:
            return 0
    return -1

if __name__ == '__main__':
    sys.exit(main())
