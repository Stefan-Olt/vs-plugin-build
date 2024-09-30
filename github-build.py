#!/usr/bin/env python3

import os
import sys
import subprocess

git_output = subprocess.check_output(['git', 'diff', '--name-only', 'HEAD', 'HEAD~1'])
plugin_list = git_output.decode("utf-8").strip().split("\n")
success_list = []
failed_list = []

for p in plugin_list:
    if p.startswith("plugins/") is False:
        continue
    p = os.path.splitext(os.path.basename(p))[0]
    print("Will build plugin "+p)
    if os.path.isdir('workspace'):
        os.system("cp -rp workspace .workspace-backup")
    ret = os.system("./vsp-build.py "+p)
    if ret == 0:
        try:
            with open('output/TAG', 'r') as file:
                tag = file.read().strip()
            if os.system("git tag "+tag) != 0:
                raise Exception("Could not create git tag") 
            if os.system("git push origin tag "+tag) != 0:
                raise Exception("Could not push git tag") 
            output_file = None
            for f in os.listdir("output"):
                if os.path.splitext(f)[1] == '.zip':
                    output_file = f
                    break
            if output_file == None:
                raise Exception("Could not find output file") 
            if os.system("gh release create "+tag+" --repo "+sys.argv[1]+" --title "+output_file+' --notes "Automatic build of '+p+'" --verify-tag') != 0:
                raise Exception("Could not create release") 
            if os.system("gh release upload "+tag+" ./output/"+output_file+" --repo "+sys.argv[1]) != 0:
                raise Exception("Could upload file to release")
            success_list.append(p)
        except Exception as err:
            print("Processing of plugin failed: "+str(err))
            failed_list.append(p + ": "+str(err))
    else:
        failed_list.append(p + ": "+str(ret))
    os.system("rm -rf build")
    os.system("rm -rf workspace")
    os.system("rm -rf output")
    os.system("rm -rf test")
    if os.path.isdir('.workspace-backup'):
        os.system("mv .workspace-backup workspace")

with open('build.log', 'w') as file:
    file.write("Plugins build successfully:\n"+"\n".join(success_list)+"\n\n\nPlugin build failed:\n"+"\n".join(failed_list))
    file.close()
