#!/usr/bin/env python3

import os
import platform as pf
import sys
import subprocess

def exec_command(cmd: list) -> int:
    print(" ".join(cmd))
    if pf.uname().system.startswith('Windows'):
        return subprocess.call(cmd, shell=True, universal_newlines=True)
    else:
        return subprocess.call(cmd, shell=False, universal_newlines=True)

git_output = subprocess.check_output(['git', 'diff', '--name-only', 'HEAD', 'HEAD~1'])
plugin_list = git_output.decode("utf-8").strip().split("\n")
success_list = []
failed_list = []

platform = []
if len(sys.argv) > 2:
    platform = ["-p", sys.argv[2]]

for p in plugin_list:
    if p.startswith("plugins/") is False:
        continue
    p = os.path.splitext(os.path.basename(p))[0]
    print("Will build plugin "+p)
    if os.path.isdir('workspace'):
        exec_command(["cp", "-rp", "workspace", ".workspace-backup"])
    if pf.uname().system.startswith('Windows'):
        ret = exec_command(["python", "vsp-build.py"] + platform + [p])
    else:
        ret = exec_command(["./vsp-build.py"] + platform + [p])
    if ret == 0:
        try:
            with open('output/TAG', 'r') as file:
                tag = file.read().strip()
            if exec_command(["git", "tag", tag]) != 0:
                raise Exception("Could not create git tag") 
            if exec_command(["git", "push", "origin", "tag", tag]) != 0:
                raise Exception("Could not push git tag") 
            output_file = None
            for f in os.listdir("output"):
                if os.path.splitext(f)[1] == '.zip':
                    output_file = f
                    break
            if output_file == None:
                raise Exception("Could not find output file") 
            if exec_command(["gh", "release", "create", tag, "--repo", sys.argv[1], "--title", output_file, "--notes", '"Automatic build of '+p+'"', "--verify-tag"]) != 0:
                raise Exception("Could not create release") 
            if exec_command(["gh", "release", "upload", tag, "./output/"+output_file, "--repo", sys.argv[1]]) != 0:
                raise Exception("Could upload file to release")
            success_list.append(p)
        except Exception as err:
            print("Processing of plugin failed: "+str(err))
            failed_list.append(p + ": "+str(err))
    else:
        failed_list.append(p + ": "+str(ret))
    exec_command(["rm", "-rf", "build"])
    exec_command(["rm", "-rf", "workspace"])
    exec_command(["rm", "-rf", "output"])
    exec_command(["rm", "-rf", "test"])
    if os.path.isdir('.workspace-backup'):
        exec_command(["mv", ".workspace-backup", "workspace"])

with open('build.log', 'w') as file:
    file.write("Plugins build successfully:\n"+"\n".join(success_list)+"\n\n\nPlugin build failed:\n"+"\n".join(failed_list))
    file.close()
