"""
This script will separate all of the objects from this blend file into separate files

output_path = The path to the save all of the blend files to

"""

import bpy
import os
import subprocess

output_path = ""

if os.path.exists(bpy.data.filepath):
        
    for obj in bpy.data.objects:
        script = os.path.join(bpy.app.tempdir,'saving.py')
        script_file = open(script,'w')
        script_file.write("import bpy\n")
        script_file.write("from mv import utils\n")
        script_file.write("with bpy.data.libraries.load(r'" + bpy.data.filepath + "', False, False) as (data_from, data_to):\n")
        script_file.write("    data_to.objects = ['" + obj.name + "']\n")
        script_file.write("for obj in data_to.objects:\n")
        script_file.write("    utils.link_objects_to_scene(obj,bpy.context.scene)\n")
        script_file.write("bpy.ops.wm.save_as_mainfile(filepath=r'" + os.path.normpath(os.path.join(output_path,obj.name))  + ".blend')\n")
        script_file.close()
        subprocess.call(bpy.app.binary_path + ' -b --python "' + script + '"')