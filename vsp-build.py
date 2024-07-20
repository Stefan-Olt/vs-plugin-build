#!/usr/bin/env python3

import argparse
import base64
import click
import errno
import hashlib
import json
import os
import platform as pf
import pty
import pyzstd
import re
import subprocess
import sys
from datetime import datetime, timezone
from select import select
from typing import Optional
from urllib.parse import urlparse

environment = None
platform = None
config_vars = {
    "NPROC": None,
    "BUILDDIR": None,
    "WORKSPACEDIR": None,
    "OUTPUTDIR": None,
    "TESTDIR": None,
    "VSPIPE": None,
    "PLUGIN_FILENAME": None
}

def get_platform() -> Optional[str]:
    pl = pf.uname()
    if pl.system == 'Linux':
        if pl.machine == 'x86_64':
            return 'linux-glibc-x86_64'
        if pl.machine == 'arm64' or pl.machine == 'aarch64':
            return 'linux-glibc-aarch64'
    elif pl.system == 'Darwin':
        if pl.machine == 'x86_64':
            return 'darwin-x86_64'
        elif pl.machine == 'arm64' or pl.machine == 'aarch64':
            return 'darwin-aarch64'
    return None

def setup_environment() -> bool:
    global environment

    environment = dict(os.environ)
    environment['PATH'] = os.path.join(config_vars['WORKSPACEDIR'],'bin')+':'+environment['PATH']
    environment['PKG_CONFIG_PATH'] = os.path.join(config_vars['WORKSPACEDIR'],'lib/pkgconfig')
    environment['LD_LIBRARY_PATH'] = os.path.join(config_vars['WORKSPACEDIR'],'lib')
    environment['CFLAGS'] = '-I'+os.path.join(config_vars['WORKSPACEDIR'],'include')+' '+environment.get('CFLAGS','')
    environment['LDFLAGS'] = '-L'+os.path.join(config_vars['WORKSPACEDIR'],'lib')+' '+environment.get('LDFLAGS','')
    return True

def compare_version(ver_a: str, ver_b: str) -> int:
    ver_a = ver_a.split('.')
    ver_b = ver_b.split('.')
    i = 0
    while i < len(ver_a) or i < len(ver_b):
        if i < len(ver_a) and i < len(ver_b):
            if ver_a[i] < ver_b[i]:
                return -1
            elif ver_a[i] > ver_b[i]:
                return 1
        elif i < len(ver_a):
            if ver_a[i] != 0:
                return 1
        elif i < len(ver_b):
            if ver_b[i] != 0:
                return -1
        i += 1
    return 0

# tested to work with autoconf, automake, libtool, cmake, nasm, yasm, ninja, meson
def check_version(command: str, cmp_version: str, comp: str) -> bool:
    comp_str = {'>=': 'At least version', '>': 'Newer than version', '==': 'exactly version', '<': 'Older than version', '<=': 'At maximum version'}

    try:
        result = subprocess.run([command,'--version'], stdout=subprocess.PIPE, env=environment, text=True)
    except:
        print("Error: '"+command+"' not found, check if installed. "+comp_str[comp]+" "+cmp_version+" is required.")
        return False
    cur_version = ("x "+result.stdout.split("\n",1)[0]).rsplit(' ',1)[1]

    r = compare_version(cur_version, cmp_version)

    if r == 0 and (comp == '>=' or comp == '==' or comp == '<='):
        return True
    elif r > 0 and (comp == '>' or comp == '>='):
        return True
    elif r < 0 and (comp == '<' or comp == '<='):
        return True

    print("Error: '"+command+"' version "+cur_version+" found. "+comp_str[comp]+" "+cmp_version+" is required.")
    return False

def exec_command(cmd: list, env: dict = {}, cwd: str = '') -> int:
    """
     modified from https://github.com/terminal-labs/cli-passthrough/blob/master/cli_passthrough/_passthrough.py
     Largely found in https://stackoverflow.com/a/31953436
    """
    masters, slaves = zip(pty.openpty(), pty.openpty())
    with subprocess.Popen(cmd, stdin=sys.stdin, stdout=slaves[0], stderr=slaves[1], cwd=os.path.join(config_vars['BUILDDIR'],cwd), env = env) as p:
        for fd in slaves:
            os.close(fd)  # no input
        readable = {
            masters[0]: sys.stdout.buffer,  # store buffers seperately
            masters[1]: sys.stderr.buffer,
        }
        while readable:
            for fd in select(readable, [], [])[0]:
                try:
                    data = os.read(fd, 1024)  # read available
                except OSError as e:
                    del readable[fd]  # EIO means EOF on some systems
                    if e.errno != errno.EIO:
                        print("Error executing command '"+' '.join(cmd)+"'")
                        return -1
                        #raise  # XXX cleanup
                else:
                    if not data:  # EOF
                        del readable[fd]
                    else:
                        if fd == masters[0]:  # We caught stdout
                            click.echo(data, nl=False)
                        else:  # We caught stderr
                            click.echo(data, nl=False, err=True)
                        readable[fd].flush()
    for fd in masters:
        os.close(fd)
    return p.returncode

def process_commands(commands: list) -> bool:
    for c in commands:
        cur_env = environment | {k:v.format_map(config_vars) for k, v in c.get('env',dict()).items()}
        for k, v in c.get('flags',dict()).items():
            cur_env[k] = cur_env.get(k,'')+' '+v
        ret = exec_command([i.format_map(config_vars) for i in c['cmd']], cur_env, c.get('cwd','').format_map(config_vars))
        if ret != 0:
            print("Error running '"+' '.join([i.format_map(config_vars) for i in c['cmd']])+"'")
            return False
    return True

def download_and_build(commands: list, url: str, chash: str, fname: Optional[str] = None) -> bool:
    if fname == None or fname == '':
        fname = ('x/'+urlparse(url).path).rsplit("/", 1)[1]
    ret = process_commands([{'env': {}, 'cwd': '', 'cmd': ['wget', '-O', fname, url] }])
    if ret != True:
        print("Could not download '"+url+"'")
        return False
    try:
        with open(os.path.join(config_vars['BUILDDIR'], fname), 'rb') as fh:
            fhash = hashlib.sha256(fh.read()).hexdigest()
    except FileNotFoundError:
        print("Could not find '"+fname+"', downloaded from '"+url+"'")
        return False
    if chash != fhash:
        print("Hash of file '"+fname+"' not correct")
        return False
    return process_commands(commands)

def create_file(fname: str, file_def: dict) -> bool:
    try:
        with open(os.path.join(file_def['path'].format_map(config_vars), fname), 'wb') as f:
            output = None
            if file_def['encoding'].startswith('text/'):
                output = bytearray(file_def['data'].format_map(config_vars),file_def['encoding'].split('/',1)[1])
            elif file_def['encoding'].startswith('base64/'):
                compression = file_def['encoding'].split('/',1)[1]
                data = base64.b64decode(file_def['data'])
                if compression == 'plain':
                    outpt = data
                elif compression == 'zstd':
                    output = pyzstd.decompress(data)
                else:
                    print("Error: Unknown compression '"+compression+"' for file '"+fname+"'")
                    return False
            else:
                print("Error: Unknown encoding '"+file_def['encoding']+"' for file '"+fname+"'")
                return False
            f.write(output)
    except Exception as e:
        print("Error: Could not create file '"+fname+"': "+str(e))
        return False
    return True

def get_build_for_platform(build: dict) -> Optional[dict]:
    for k, v in build.items():
        if re.fullmatch(k,platform):
            return v
    return None

def build_plugin(filename: str, version: Optional[str] = None) -> bool:
    global config_vars
    # load build definition
    build_def = None
    with open(filename) as json_file:
        build_def = json.load(json_file)
        json_file.close()
    if build_def['type'] != 'VSPlugin':
        print("Error: Don't recognize type of "+build_def['name'])
        return False
    print("Start building "+build_def['name']+" for "+platform+"...")
    # get release to build
    build_rel = None
    if version == None:
        build_rel = build_def['releases'][0]
        version = build_rel['version']
    else:
        for r in build_def['releases']:
            if r['version'] == version:
                build_rel = r
                break
    if build_rel == None:
        print("Error: Version for "+build_def['name']+" not found")
        return False
    # check build tools for platform
    for k, v in build_rel['buildtools_dependencies'].items():
        if re.fullmatch(k,platform):
            for i in v:
                if check_version(i['name'], i['version'][1], i['version'][0]) == False:
                     return False
    # get build instructions for platform
    build_platf = get_build_for_platform(build_rel['build'])
    if build_platf == None:
        print("Error: No build instructions for "+build_def['name']+" on "+platform+" found")
        return False
    # create files 
    for f in build_platf.get('create_files', []):
        if create_file(f, build_def['file_definitions'][f]) == False:
            return False
    # get and build runtime dependencies
    for d in build_platf.get('dependencies', []):
        found = False
        for i in build_def['runtime_dependencies']:
            if d['name'] == i['name'] and d['version'] == i['version']:
                found = True
                build_dep_platf = get_build_for_platform(i['build'])
                if build_dep_platf == None:
                    print("Error: No build instructions for "+i['name']+" on "+platform+" found")
                    return False
                else:
                    if download_and_build(build_dep_platf['commands'],i['source'],i['hash'],i.get('filename', None)) == False:
                        print("Error: Failed to build "+i['name'])
                        return False
                break
        if found == False:
            print("Error: Dependency "+d['name']+" not found")
            return False
    # build plugin
    if download_and_build(build_platf['commands'],build_rel['source'],build_rel['hash'],build_rel.get('filename', None)) == False:
        print("Error: Failed to build "+build_def['name'])
        return False
    # collect output files
    output_files = None
    for k, v in build_rel["release_files"].items():
        if re.fullmatch(k, platform):
            output_files = [i.format_map(config_vars) for i in v]
            break
    if output_files == None:
        print("Error: No output files for platform "+platform+" defined")
        return False
    # check output files and calc hashes for output json
    output_dict = { "version": version, platform: { "files": {} } }
    for i in output_files:
        try:
            with open(i, 'rb') as fh:
                hashsum = hashlib.sha256(fh.read()).hexdigest()
                fname = os.path.split(i)[1]
                output_dict[platform]["files"][fname] = [fname, hashsum]
        except FileNotFoundError:
            print("Error: Could not find file that should have been build: '"+i+"'")
            return False
    # copy output files for testing to vs plugin dir
    if config_vars['TESTDIR'] != None:
        for i in output_files:
            if exec_command(['cp', i, config_vars['TESTDIR']]) != 0:
                print("Error: Could copy file '"+i+"' to plugin directory for testing")
                return False
    # set plugin filename for testing
    config_vars['PLUGIN_FILENAME'] = os.path.split(output_files[0])[1]
    # additional output files:
    additional_files = []
    for k, v in build_rel.get("additional_files",dict()).items():
        if re.fullmatch(k, platform):
            additional_files = [i.format_map(config_vars) for i in v]
            break
    for i in additional_files:
        if os.path.isfile(i):
            output_files.append(i)
        else:
            print("Error: Could not find file additional file to include: '"+i+"'")
            return False
    # zip output files
    zipfile = os.path.join(config_vars['OUTPUTDIR'],build_def['name']+"-"+version+"-"+platform+".zip")
    zipcmd = ['zip','-j','-9',zipfile]
    zipcmd.extend(output_files)
    if exec_command(zipcmd) != 0:
        print("Error: Could not create output zip file: '"+zipfile+"'")
        return False
    else:
        print("Finished creating output zip file: '"+zipfile+"'")

    with open(os.path.join(config_vars['OUTPUTDIR'], 'TAG'), 'w', encoding='utf-8') as f:
        f.write(build_def['identifier']+'/'+version+'/'+platform+'/'+datetime.utcnow().replace(microsecond=0).isoformat().replace(':','.')+'Z')

    # testing
    if config_vars['TESTDIR'] != None:
        for k, v in build_rel['tests'].items():
            if re.fullmatch(k,platform):
                for i in v:
                    found = False
                    for t in build_def.get('tests'):
                        if t['name'] == i:
                            found = True
                            for f in t.get('create_files', []):
                                if create_file(f, build_def['file_definitions'][f]) == False:
                                    return False
                            if process_commands(t['commands']) == False:
                                print("Error: Test '"+i+"' failed")
                                return False
            if found == False:
                print("Error: Test "+i+" not found")
                return False

    # update vs-repo json

    return True

def main() -> int:
    global config_vars, platform

    parser = argparse.ArgumentParser()
    parser.add_argument("-b", "--builddir", type=str, help="directory for downloading/building", default=os.path.join(os.path.dirname(os.path.realpath(__file__)),'build'))
    parser.add_argument("-w", "--workspacedir", type=str, help="directory for the workspace tree", default=os.path.join(os.path.dirname(os.path.realpath(__file__)),'workspace'))
    parser.add_argument("-o", "--outputdir", type=str, help="directory for the output zip files", default=os.path.join(os.path.dirname(os.path.realpath(__file__)),'output'))
    parser.add_argument("-t", "--testdir", type=str, help="directory for the tests", default=os.path.join(os.path.dirname(os.path.realpath(__file__)),'test'))
    parser.add_argument("--vspipe", type=str, help="command for vspipe", default='vspipe')
    parser.add_argument("--disable-tests", help="disable tests", default=False, action='store_true')
    parser.add_argument("-n", "--nproc", type=int, help="number of processors/cores to use for building", default=os.cpu_count())
    parser.add_argument("-p", "--platform", type=str, help="platform used to select build definition", default=get_platform())
    parser.add_argument("-v", "--version", type=str, help="build specific version of plugin", default=None)
    parser.add_argument("plugin", type=str, help="plugin to build")

    args = parser.parse_args()
    config_vars['BUILDDIR'] = args.builddir
    config_vars['WORKSPACEDIR'] = args.workspacedir
    config_vars['OUTPUTDIR'] = args.outputdir
    config_vars['VSPIPE'] = args.vspipe
    config_vars['NPROC'] = args.nproc
    platform = args.platform

    if platform == None:
        print("Error: No platform set and auto-detect of platform failed")
        return 1   

    os.makedirs(config_vars['BUILDDIR'], exist_ok=True)
    os.makedirs(config_vars['WORKSPACEDIR'], exist_ok=True)
    os.makedirs(config_vars['OUTPUTDIR'], exist_ok=True)

    if args.disable_tests != True:
        config_vars['TESTDIR'] = args.testdir
        os.makedirs(config_vars['TESTDIR'], exist_ok=True)

    if setup_environment() == False:
        return 1

    plugin_json = args.plugin
    if plugin_json.endswith('.json') is False:
        plugin_json = os.path.join(os.path.dirname(os.path.realpath(__file__)),"plugins",plugin_json+'.json')
    if build_plugin(plugin_json, args.version) is True:
        return 0
    return -1

if __name__ == '__main__':
    sys.exit(main())
