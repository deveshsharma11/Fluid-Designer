# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    "name": "2D Views",
    "author": "Ryan Montes",
    "version": (1, 0, 0),
    "blender": (2, 7, 0),
    "location": "Tools Shelf",
    "description": "This add-on creates a UI to generate 2D Views",
    "warning": "",
    "wiki_url": "",
    "category": "Fluid Designer"
}

import bpy
from mv import utils, fd_types, unit, opengl_dim
from . import report_2d_drawings
import math
import os
import time

class PANEL_2d_views(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_context = "objectmode"
    bl_label = "2D Views"
    bl_category = "Fluid Designer"
    bl_options = {'DEFAULT_CLOSED'}    
    
    @classmethod
    def poll(cls, context):
        return True
    
    def draw_header(self, context):
        layout = self.layout
        layout.label('',icon='ALIGN')
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        panel_box = layout.box()
        
        row = panel_box.row(align=True)
        row.scale_y = 1.3
        
        elv_scenes = []
        for scene in bpy.data.scenes:
            if scene.mv.elevation_scene:
                elv_scenes.append(scene)
                
        if len(elv_scenes) < 1:
            row.operator("fd_2d_views.genereate_2d_views",text="Prepare 2D Views",icon='RENDERLAYERS')
        else:
            row.operator("fd_2d_views.genereate_2d_views",text="",icon='FILE_REFRESH')
            row.operator("fd_2d_views.create_new_view",text="",icon='ZOOMIN')
            row.operator("2dviews.render_2d_views",text="Render Selected Scenes",icon='RENDER_REGION')
            row.menu('MENU_elevation_scene_options',text="",icon='DOWNARROW_HLT')
            panel_box.template_list("LIST_scenes", 
                                    " ", 
                                    bpy.data, 
                                    "scenes", 
                                    bpy.context.window_manager.mv, 
                                    "elevation_scene_index")
            
        image_views = context.window_manager.mv.image_views
        
        if len(image_views) > 0:
            panel_box.label("Image Views",icon='RENDERLAYERS')
            row = panel_box.row()
            row.template_list("LIST_2d_images"," ",context.window_manager.mv,"image_views",context.window_manager.mv,"image_view_index")
            col = row.column(align=True)
            col.operator('fd_2d_views.move_2d_image_item', text="", icon='TRIA_UP').direction = 'UP'
            col.operator('fd_2d_views.move_2d_image_item', text="", icon='TRIA_DOWN').direction = 'DOWN'
            panel_box.menu('MENU_2dview_reports',icon='FILE_BLANK')
#             panel_box.operator('2dviews.create_pdf',text="Create PDF",icon='FILE_BLANK')
      
      
class MENU_2dview_reports(bpy.types.Menu):
    bl_label = "2D Reports"
    
    """
    Report Templates are added to this menu
    """
    
    def draw(self, context):
        layout = self.layout
      
      
class MENU_elevation_scene_options(bpy.types.Menu):
    bl_label = "Elevation Scene Options"

    def draw(self, context):
        layout = self.layout
        layout.operator("fd_general.select_all_elevation_scenes",text="Select All",icon='CHECKBOX_HLT').select_all = True
        layout.operator("fd_general.select_all_elevation_scenes",text="Deselect All",icon='CHECKBOX_DEHLT').select_all = False
        layout.separator()
        layout.operator('fd_general.project_info',text="View Project Info",icon='INFO')
        layout.operator("2dviews.create_snap_shot",text="Create Snap Shot",icon='SCENE')
        layout.operator("fd_2d_views.append_to_view", text="Append to View", icon='ZOOMIN')
        layout.separator()
        layout.operator("fd_scene.clear_2d_views",text="Clear All 2D Views",icon='X')


class LIST_scenes(bpy.types.UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        
        if item.mv.plan_view_scene or item.mv.elevation_scene:
            layout.label(item.mv.name_scene,icon='RENDER_REGION')
            layout.prop(item.mv, 'render_type_2d_view', text="")
            layout.prop(item.mv, 'elevation_selected', text="")
        else:
            layout.label(item.name,icon='SCENE_DATA')


class LIST_2d_images(bpy.types.UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        
        layout.label(item.name,icon='RENDER_RESULT')
        layout.operator('2dviews.view_image',text="",icon='RESTRICT_VIEW_OFF',emboss=False).image_name = item.name
        layout.operator('2dviews.delete_image',text="",icon='X',emboss=False).image_name = item.name
        
class OPERATOR_move_image_list_item(bpy.types.Operator):
    bl_idname = "fd_2d_views.move_2d_image_item"
    bl_label = "Move an item in the 2D image list"

    direction = bpy.props.EnumProperty(items=(('UP', 'Up', "Move Item Up"),
                                              ('DOWN', 'Down', "Move Item Down")))

    @classmethod
    def poll(self, context):
        return len(bpy.context.window_manager.mv.image_views) > 0

    def execute(self, context):
        wm = context.window_manager.mv
        img_list = wm.image_views
        crt_index = wm.image_view_index
        list_length = len(wm.image_views) - 1
        move_to_index = crt_index - 1 if self.direction == 'UP' else crt_index + 1
        
        if self.direction == 'UP' and crt_index == 0 or self.direction == 'DOWN' and crt_index == list_length:
            return {'FINISHED'}
        else:
            img_list.move(crt_index, move_to_index)
            wm.image_view_index = move_to_index

        return{'FINISHED'}

        
class OPERATOR_create_new_view(bpy.types.Operator):
    bl_idname = "fd_2d_views.create_new_view"    
    bl_label = "Create New 2d View"
    bl_description = "Create New 2d View"
    bl_options = {'UNDO'}
    
    view_name = bpy.props.StringProperty(name="View Name",
                                         description="Name for New View",
                                         default="")
    
    view_products = []
    
    def invoke(self, context, event):
        wm = context.window_manager
        self.view_products.clear()
        
        #For now only products are selected, could include walls or other objects
        for obj in context.selected_objects:
            product_bp = utils.get_bp(obj,'PRODUCT')
            
            if product_bp and product_bp not in self.view_products:
                self.view_products.append(product_bp)
        
        return wm.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.prop(self, 'view_name', text="View Name")
        box.label("Selected Products:")
        prod_box = box.box()  
         
        if len(self.view_products) > 0:
            for obj in self.view_products:
                row = prod_box.row()
                row.label(obj.mv.name_object, icon='OUTLINER_OB_LATTICE')
        
        else:
            row = prod_box.row()
            row.label("No Products Selected!", icon='ERROR')
            warn_box = box.box()
            row = warn_box.row()
            row.label("Create Empty View?", icon='QUESTION')
    
    def execute(self, context):
        packed_bps = [{"name": obj_bp.name, "obj_name": obj_bp.mv.name_object} for obj_bp in self.view_products]
        bpy.ops.fd_2d_views.genereate_2d_views('INVOKE_DEFAULT',
                                               use_single_scene=True,
                                               single_scene_name=self.view_name,
                                               single_scene_objs=packed_bps)
        return {'FINISHED'}
    
class OPERATOR_append_to_view_OLD(bpy.types.Operator):
    bl_idname = "fd_2d_views.append_to_view"    
    bl_label = "Append Product to 2d View"
    bl_description = "Append Product to 2d View"
    bl_options = {'UNDO'}
    
    products = []
    
    def invoke(self, context, event):
        wm = context.window_manager
        self.products.clear()
        
        #For now only products are selected, could include walls or other objects
        for obj in context.selected_objects:
            product_bp = utils.get_bp(obj,'PRODUCT')
            
            if product_bp and product_bp not in self.products:
                self.products.append(product_bp)
        
        return wm.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.label("Selected Products:")
        prod_box = box.box()  
         
        if len(self.products) > 0:
            for obj in self.products:
                row = prod_box.row()
                row.label(obj.mv.name_object, icon='OUTLINER_OB_LATTICE')
        
        else:
            row = prod_box.row()
            row.label("No Products Selected!", icon='ERROR')
            warn_box = box.box()
            row = warn_box.row()
            row.label("Nothing to Append.", icon='ERROR')
            
    def link_dims_to_scene(self, scene, obj_bp):
        for child in obj_bp.children:
            if child not in self.ignore_obj_list:
                if child.mv.type in ('VISDIM_A','VISDIM_B'):
                    scene.objects.link(child)
                if len(child.children) > 0:
                    self.link_dims_to_scene(scene, child)
                    
    def group_children(self, grp, obj):
        if obj.mv.type != 'CAGE':
            grp.objects.link(obj)
        for child in obj.children:
            if len(child.children) > 0:
                if child.mv.type == 'OBSTACLE':
                    for cc in child.children:
                        if cc.mv.type == 'CAGE':
                            cc.hide_render = False
                            grp.objects.link(cc)
                else:
                    self.group_children(grp,child)
            else:
                if not child.mv.is_wall_mesh:
                    if child.mv.type != 'CAGE':
                        grp.objects.link(child)  
        return grp
    
    def execute(self, context):
        if len(self.products) < 1:
            return {'FINISHED'}
        
        for scene in bpy.data.scenes:
            if scene.mv.elevation_selected:
                grp = bpy.data.groups[scene.name]
                for prod in self.products:
                    self.group_children(grp, prod)
        
        return {'FINISHED'}    

class single_scene_objs(bpy.types.PropertyGroup):
    obj_name = bpy.props.StringProperty(name="Object Name")
    
bpy.utils.register_class(single_scene_objs)
    
class OPERATOR_append_to_view(bpy.types.Operator):
    bl_idname = "fd_2d_views.append_to_view"    
    bl_label = "Append Product to 2d View"
    bl_description = "Append Product to 2d View"
    bl_options = {'UNDO'}
    
    products = []
    
    objects = []
    
    scenes = bpy.props.CollectionProperty(type=single_scene_objs,
                                                     name="Objects for Single Scene",
                                                     description="Objects to Include When Creating a Single View")    
    
    scene_index = bpy.props.IntProperty(name="Scene Index")
    
    def invoke(self, context, event):
        wm = context.window_manager
        self.products.clear()
        self.objects.clear()
        
        for i in self.scenes:
            self.scenes.remove(0)
        
        for scene in bpy.data.scenes:
            scene_col = self.scenes.add()
            scene_col.name = scene.name

        for obj in context.selected_objects:
            product_bp = utils.get_bp(obj,'PRODUCT')
            
            if product_bp and product_bp not in self.products:
                self.products.append(product_bp)
        
        if len(self.products) == 0:
            for obj in context.selected_objects:
                self.objects.append(obj)
        
        return wm.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.label("Selected View to Append To:")
        box.template_list("LIST_2d_images"," ",self,"scenes",self,"scene_index")

        if len(self.products) > 0:
            box.label("Selected Products:")
            prod_box = box.box()              
            for obj in self.products:
                row = prod_box.row()
                row.label(obj.mv.name_object, icon='OUTLINER_OB_LATTICE')
        else:
            if len(self.objects) > 0:
                box.label("Selected Objects:")
                prod_box = box.box()                           
                for obj in self.objects:
                    row = prod_box.row()
                    row.label(obj.name, icon='OBJECT_DATA')
            else:
                warn_box = box.box()
                row = warn_box.row()
                row.label("Nothing to Append.", icon='ERROR')
            
    def link_children_to_scene(self,scene,obj_bp):
        scene.objects.link(obj_bp)
        for child in obj_bp.children:
            self.link_children_to_scene(scene, child)
    
    def execute(self, context):
        scene = bpy.data.scenes[self.scene_index]
        
        for product in self.products:
            self.link_children_to_scene(scene, product)
            
        print("OBJS",self.objects)
            
        for obj in self.objects:
            print('LINK',obj,scene)
            self.link_children_to_scene(scene, obj)

        return {'FINISHED'}
    

class OPERATOR_genereate_2d_views(bpy.types.Operator):
    bl_idname = "fd_2d_views.genereate_2d_views"    
    bl_label = "Generate 2d Views"
    bl_description = "Generates 2D Views"
    bl_options = {'UNDO'}
    
    VISIBLE_LINESET_NAME = "Visible Lines"
    HIDDEN_LINESET_NAME = "Hidden Lines"
    ENV_2D_NAME = "2D Environment"
    HIDDEN_LINE_DASH_PX = 5
    HIDDEN_LINE_GAP_PX = 5
    

    ev_pad = bpy.props.FloatProperty(name="Elevation View Padding",
                                     default=0.75)
    
    pv_pad = bpy.props.FloatProperty(name="Plan View Padding",
                                     default=1.5)
        
    main_scene = None
    
    ignore_obj_list = []
    
    use_single_scene = bpy.props.BoolProperty(name="Use for Creating Single View",
                                              default=False)
    
    single_scene_name = bpy.props.StringProperty(name="Single Scene Name")
    
    single_scene_objs = bpy.props.CollectionProperty(type=single_scene_objs,
                                                     name="Objects for Single Scene",
                                                     description="Objects to Include When Creating a Single View")
    
#     orphan_products = []

    def get_world(self):
        if self.ENV_2D_NAME in bpy.data.worlds:
            return bpy.data.worlds[self.ENV_2D_NAME]
        else:
            world = bpy.data.worlds.new(self.ENV_2D_NAME)
            world.horizon_color = (1.0, 1.0, 1.0) 
            return world
    
    def create_linestyles(self):
        linestyles = bpy.data.linestyles
        linestyles.new(self.VISIBLE_LINESET_NAME)
        
        hidden_linestyle = linestyles.new(self.HIDDEN_LINESET_NAME)
        hidden_linestyle.use_dashed_line = True
        hidden_linestyle.dash1 = self.HIDDEN_LINE_DASH_PX
        hidden_linestyle.dash2 = self.HIDDEN_LINE_DASH_PX
        hidden_linestyle.dash3 = self.HIDDEN_LINE_DASH_PX
        hidden_linestyle.gap1 = self.HIDDEN_LINE_GAP_PX
        hidden_linestyle.gap2 = self.HIDDEN_LINE_GAP_PX
        hidden_linestyle.gap3 = self.HIDDEN_LINE_GAP_PX
        
    def create_linesets(self, scene):
        f_settings = scene.render.layers[0].freestyle_settings
        linestyles = bpy.data.linestyles
        
        f_settings.linesets.new(self.VISIBLE_LINESET_NAME).linestyle = linestyles[self.VISIBLE_LINESET_NAME]
        
        hidden_lineset = f_settings.linesets.new(self.HIDDEN_LINESET_NAME)
        hidden_lineset.linestyle = linestyles[self.HIDDEN_LINESET_NAME]
        
        hidden_lineset.select_by_visibility = True
        hidden_lineset.visibility = 'HIDDEN'
        hidden_lineset.select_by_edge_types = True
        hidden_lineset.select_by_face_marks = False
        hidden_lineset.select_by_group = False
        hidden_lineset.select_by_image_border = False
        
        hidden_lineset.select_silhouette = False
        hidden_lineset.select_border = False
        hidden_lineset.select_contour = False
        hidden_lineset.select_suggestive_contour = False
        hidden_lineset.select_ridge_valley = False
        hidden_lineset.select_crease = False
        hidden_lineset.select_edge_mark = True
        hidden_lineset.select_external_contour = False
        hidden_lineset.select_material_boundary = False
    
    def clear_unused_linestyles(self):
        for linestyle in bpy.data.linestyles:
            if linestyle.users == 0:
                bpy.data.linestyles.remove(linestyle)
    
    def create_camera(self, scene):
        camera_data = bpy.data.cameras.new(scene.name)
        camera_obj = bpy.data.objects.new(name=scene.name,object_data=camera_data)
        scene.objects.link(camera_obj)
        scene.camera = camera_obj                        
        camera_obj.data.type = 'ORTHO'
        scene.render.resolution_y = 1280
        scene.mv.ui.render_type_tabs = 'NPR'
        scene.world = self.get_world()
        scene.render.display_mode = 'NONE'
        scene.render.use_lock_interface = True        
        scene.render.image_settings.file_format = 'JPEG'
        
        return camera_obj
    
    def link_dims_to_scene(self, scene, obj_bp):
        for child in obj_bp.children:
            if child not in self.ignore_obj_list:
                if child.mv.type in ('VISDIM_A','VISDIM_B'):
                    scene.objects.link(child)
                if len(child.children) > 0:
                    self.link_dims_to_scene(scene, child)     
    
    def group_children(self, grp, obj):
        if obj.mv.type != 'CAGE' and obj not in self.ignore_obj_list:
            grp.objects.link(obj)
        for child in obj.children:
            if len(child.children) > 0:
                if child.mv.type == 'OBSTACLE':
                    for cc in child.children:
                        if cc.mv.type == 'CAGE':
                            cc.hide_render = False
                            grp.objects.link(cc)
                else:
                    self.group_children(grp,child)
            else:
#                 if not child.mv.is_wall_mesh:
                if child.mv.type != 'CAGE' and obj not in self.ignore_obj_list:
                    grp.objects.link(child)  
        return grp
    
    def create_new_scene(self, context, grp, obj_bp):
        bpy.ops.scene.new('INVOKE_DEFAULT',type='EMPTY')
        new_scene = context.scene
        new_scene.name = grp.name
        new_scene.mv.name_scene = "Product - " + obj_bp.mv.name_object if obj_bp.mv.type == 'BPASSEMBLY' else obj_bp.mv.name_object
        new_scene.mv.elevation_img_name = obj_bp.name
        new_scene.mv.plan_view_scene = False
        new_scene.mv.elevation_scene = True
        self.create_linesets(new_scene)
        
        return new_scene
    
    def add_text(self, context, assembly):
        bpy.ops.object.text_add()
        text = context.active_object
        text.parent = assembly.obj_bp
        text.location.x = unit.inch(-2)
        text.location.z = unit.inch(-10)
        text.rotation_euler.x = math.radians(90)
        text.data.size = .1
        text.data.body = assembly.obj_bp.mv.name_object
        text.data.align_x = 'RIGHT'
        text.data.font = self.font        
        
    def create_plan_view_scene(self,context):
        bpy.ops.scene.new('INVOKE_DEFAULT',type='EMPTY')   
        pv_scene = context.scene
        pv_scene.name = "Plan View"
        pv_scene.mv.name_scene = "Plan View"
        pv_scene.mv.plan_view_scene = True
        self.create_linesets(pv_scene)
        
        grp = bpy.data.groups.new("Plan View")
        
        for obj in self.main_scene.objects:
            #Add Floor and Ceiling Obstacles to Plan View
            if obj.mv.type == 'OBSTACLE':
                pv_scene.objects.link(obj)
                for child in obj.children:
                    child.hide_render = False
                    pv_scene.objects.link(child)
                                        
            if obj.mv.type == 'BPWALL':
                pv_scene.objects.link(obj)
                #Only link all of the wall meshes
                for child in obj.children:
                    if child.mv.is_wall_mesh:
                        child.select = True
                        pv_scene.objects.link(child)
                        grp.objects.link(child)
                        
                wall = fd_types.Wall(obj_bp = obj)
                if wall.obj_bp and wall.obj_x and wall.obj_y and wall.obj_z:
                
                    dim = fd_types.Dimension()
                    dim.parent(wall.obj_bp)
                    dim.start_y(value = unit.inch(4) + wall.obj_y.location.y)
                    dim.start_z(value = wall.obj_z.location.z + unit.inch(8))
                    dim.end_x(value = wall.obj_x.location.x)  
                    
                    self.ignore_obj_list.append(dim.anchor)
                    self.ignore_obj_list.append(dim.end_point)
      
                    bpy.ops.object.text_add()
                    text = context.active_object
                    text.parent = wall.obj_bp
                    text.location = (wall.obj_x.location.x/2,unit.inch(1.5),wall.obj_z.location.z)
                    text.data.size = .1
                    text.data.body = wall.obj_bp.mv.name_object
                    text.data.align_x = 'CENTER'
                    text.data.font = self.font
                     
                    self.ignore_obj_list.append(dim.anchor)
                    self.ignore_obj_list.append(dim.end_point)
                     
                    obj_bps = wall.get_wall_groups()
                    #Create Cubes for all products
                    for obj_bp in obj_bps:
                        if obj_bp.mv.plan_draw_id != "":
                            eval('bpy.ops.' + obj_bp.mv.plan_draw_id + '(object_name=obj_bp.name)')
                        else:
                            assembly = fd_types.Assembly(obj_bp)
                            assembly_mesh = utils.create_cube_mesh(assembly.obj_bp.mv.name_object,
                                                                (assembly.obj_x.location.x,
                                                                 assembly.obj_y.location.y,
                                                                 assembly.obj_z.location.z))
                            assembly_mesh.parent = wall.obj_bp
                            assembly_mesh.location = assembly.obj_bp.location
                            assembly_mesh.rotation_euler = assembly.obj_bp.rotation_euler
                            assembly_mesh.mv.type = 'CAGE'
                            distance = unit.inch(14)
                            distance += wall.obj_y.location.y
                            
                            dim = fd_types.Dimension()
                            dim.parent(assembly_mesh)
                            dim.start_y(value = distance)
                            dim.start_z(value = 0)
                            dim.end_x(value = assembly.obj_x.location.x)
                            
                            self.ignore_obj_list.append(dim.anchor)
                            self.ignore_obj_list.append(dim.end_point)
                            
                    if wall and wall.get_wall_mesh():
                        wall.get_wall_mesh().select = True
                
        camera = self.create_camera(pv_scene)
        camera.rotation_euler.z = math.radians(-90.0)
        bpy.ops.object.select_all(action="SELECT")
        bpy.ops.view3d.camera_to_view_selected()
        camera.data.ortho_scale += self.pv_pad
    
    def create_elv_view_scene(self, context, assembly):
        if assembly.obj_bp and assembly.obj_x and assembly.obj_y and assembly.obj_z:
            grp = bpy.data.groups.new(assembly.obj_bp.mv.name_object)
            new_scene = self.create_new_scene(context, grp, assembly.obj_bp)
            
            self.group_children(grp, assembly.obj_bp)                    
#             wall_mesh = utils.create_cube_mesh(assembly.obj_bp.mv.name_object,
#                                                (assembly.obj_x.location.x,
#                                                 assembly.obj_y.location.y,
#                                                 assembly.obj_z.location.z))
#             
#             wall_mesh.parent = assembly.obj_bp
#             grp.objects.link(wall_mesh)
            
            instance = bpy.data.objects.new(assembly.obj_bp.mv.name_object + " "  + "Instance" , None)
            new_scene.objects.link(instance)
            instance.dupli_type = 'GROUP'
            instance.dupli_group = grp
            
            new_scene.world = self.main_scene.world
            self.link_dims_to_scene(new_scene, assembly.obj_bp)
            self.add_text(context, assembly)
            
            camera = self.create_camera(new_scene)
            camera.rotation_euler.x = math.radians(90.0)
            camera.rotation_euler.z = assembly.obj_bp.rotation_euler.z   
            bpy.ops.object.select_all(action='SELECT')
#             bpy.ops.object.select_all(action='DESELECT')
#             wall_mesh.select = True
            bpy.ops.view3d.camera_to_view_selected()
            camera.data.ortho_scale += self.pv_pad
            
    def create_single_elv_view(self, context):
        grp = bpy.data.groups.new(self.single_scene_name)
        
        bpy.ops.scene.new('INVOKE_DEFAULT',type='EMPTY')
        new_scene = context.scene
        new_scene.name = grp.name
        new_scene.mv.name_scene = self.single_scene_name
        new_scene.mv.elevation_img_name = self.single_scene_name
        new_scene.mv.plan_view_scene = False
        new_scene.mv.elevation_scene = True
        self.create_linesets(new_scene)
        
        for item in self.single_scene_objs:
            obj = bpy.data.objects[item.name]
            self.group_children(grp, obj)
            self.link_dims_to_scene(new_scene, obj)
        
        instance = bpy.data.objects.new(self.single_scene_name + " "  + "Instance" , None)
        new_scene.objects.link(instance)
        instance.dupli_type = 'GROUP'
        instance.dupli_group = grp
        
        new_scene.world = self.main_scene.world
        #----------------------------------------------------------------------------------------        
        
        #self.link_dims_to_scene(new_scene, assembly.obj_bp)
        
        #Skip for now
        #self.add_text(context, assembly)
        
        camera = self.create_camera(new_scene)
        camera.rotation_euler.x = math.radians(90.0)
        #camera.rotation_euler.z = assembly.obj_bp.rotation_euler.z   
        bpy.ops.object.select_all(action='SELECT')
        #wall_mesh.select = True
        bpy.ops.view3d.camera_to_view_selected()
        camera.data.ortho_scale += self.pv_pad            

    def execute(self, context):
        context.window_manager.mv.use_opengl_dimensions = True
        self.font = opengl_dim.get_custom_font()
        self.create_linestyles()
        self.main_scene = context.scene
        context.scene.name = "_Main"
        
        if self.use_single_scene:
            self.create_single_elv_view(context)
            
        else:
            bpy.ops.fd_scene.clear_2d_views()
            
            self.create_plan_view_scene(context)
            
            for obj in self.main_scene.objects:
                if obj.mv.type == 'BPWALL':
                    wall = fd_types.Wall(obj_bp = obj)
                    if len(wall.get_wall_groups()) > 0:
                        self.create_elv_view_scene(context, wall)
                        
        self.clear_unused_linestyles()
        bpy.context.screen.scene = self.main_scene
        wm = context.window_manager.mv
        wm.elevation_scene_index = 0
        return {'FINISHED'}


class OPERATOR_render_2d_views(bpy.types.Operator):
    bl_idname = "2dviews.render_2d_views"
    bl_label = "Render 2D Views"
    bl_description = "Renders 2d Scenes"
    
    r = 0
    g = 0
    b = 0
    a = 0
    
    def save_dim_color(self,color):
        self.r = color[0]
        self.g = color[1]
        self.b = color[2]
        self.a = color[3]
    
    def reset_dim_color(self,context):
        context.scene.mv.opengl_dim.gl_default_color[0] = self.r
        context.scene.mv.opengl_dim.gl_default_color[1] = self.g
        context.scene.mv.opengl_dim.gl_default_color[2] = self.b
        context.scene.mv.opengl_dim.gl_default_color[3] = self.a
    
    def render_scene(self,context,scene):
        context.screen.scene = scene
        
        self.save_dim_color(scene.mv.opengl_dim.gl_default_color)
        
        scene.mv.opengl_dim.gl_default_color = (0.1, 0.1, 0.1, 1.0)
        rd = scene.render
        rl = rd.layers.active
        freestyle_settings = rl.freestyle_settings
        
        rd.use_freestyle = True
        rd.image_settings.file_format = 'JPEG'
        rd.line_thickness = 0.75
        rd.resolution_percentage = 100
        rl.use_pass_combined = False
        rl.use_pass_z = False
        freestyle_settings.crease_angle = 2.617994
        
#         file_format = scene.render.image_settings.file_format.lower()
        
        if scene.mv.render_type_2d_view == 'GREYSCALE':
            rd.engine = 'BLENDER_RENDER'
        else:
            rd.engine = 'CYCLES'           
        
        bpy.ops.render.render('INVOKE_DEFAULT', write_still=True)

        while not os.path.exists(bpy.path.abspath(scene.render.filepath) + ".jpg"):
            time.sleep(0.1)
        
        img_result = opengl_dim.render_opengl(self,context)
        
        image_view = context.window_manager.mv.image_views.add()
        image_view.name = img_result.name
        image_view.image_name = img_result.name
        if scene.mv.plan_view_scene:
            image_view.is_plan_view = True
        
        if scene.mv.elevation_scene:
            image_view.is_elv_view = True
            
        self.reset_dim_color(context)

    def execute(self, context):
        file_path = bpy.app.tempdir if bpy.data.filepath == "" else os.path.dirname(bpy.data.filepath)
        
        # HACK: YOU HAVE TO SET THE CURRENT SCENE TO RENDER JPEG BECAUSE
        # OF REPORTS LAB AND BLENDER LIMITATIONS. :(
        rd = context.scene.render
        rd.image_settings.file_format = 'JPEG'
        
        current_scene = context.screen.scene
        
        for scene in bpy.data.scenes:
            if scene.mv.elevation_selected:
                self.render_scene(context,scene)
        
        context.screen.scene = current_scene
        
        return {'FINISHED'}


class OPERATOR_view_image(bpy.types.Operator):
    bl_idname = "2dviews.view_image"
    bl_label = "View Image"
    bl_description = "Opens the image editor to view the 2D view."
    
    image_name = bpy.props.StringProperty(name="Object Name",
                                          description="This is the readable name of the object")
    
    def execute(self, context):
        bpy.ops.fd_general.open_new_window(space_type = 'IMAGE_EDITOR')
        
        image_view = context.window_manager.mv.image_views[self.image_name]
        
        print(image_view.name,image_view.image_name)
        
        areas = context.screen.areas
        
        for area in areas:
            for space in area.spaces:
                if space.type == 'IMAGE_EDITOR':
                    for image in bpy.data.images:
                        if image.name == image_view.image_name:
                            space.image = image
                    # This causing blender to crash :(
                    # TODO: Figure out how to view the entire image automatically
#                     override = {'area':area}
#                     bpy.ops.image.view_all(override,fit_view=True)

        return {'FINISHED'}
    

class OPERATOR_delete_image(bpy.types.Operator):
    bl_idname = "2dviews.delete_image"
    bl_label = "View Image"
    bl_description = "Delete the Image"
    
    image_name = bpy.props.StringProperty(name="Object Name",
                                          description="This is the readable name of the object")
    
    def execute(self, context):
        for index, iv in enumerate(context.window_manager.mv.image_views):
            if iv.name == self.image_name:
                context.window_manager.mv.image_views.remove(index)
        
        for image in bpy.data.images:
            if image.name == self.image_name:
                bpy.data.images.remove(image)
                break

        return {'FINISHED'}


class OPERATOR_create_snap_shot(bpy.types.Operator):
    bl_idname = "2dviews.create_snap_shot"
    bl_label = "Create New View"
    bl_description = "Renders 2d Scenes"

    def execute(self, context):
        bpy.ops.view3d.toolshelf()
        context.area.header_text_set(text="Position view then LEFT CLICK to take screen shot. ESC to Cancel.")
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
        
    def get_file_path(self):
        counter = 1
        while os.path.exists(os.path.join(bpy.app.tempdir,"View " + str(counter) + ".png")):
            counter += 1
        return os.path.join(bpy.app.tempdir,"View " + str(counter) + ".png")
        
    def modal(self, context, event):
        context.area.tag_redraw()
        
        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            return {'PASS_THROUGH'}
            
        if event.type in {'ESC', 'RIGHTMOUSE'}:
            context.area.header_text_set()
            bpy.ops.view3d.toolshelf()
            return {'FINISHED'}
            
        if event.type in {'LEFTMOUSE'}:
            context.area.header_text_set(" ")
            file_path = self.get_file_path()
            # The PDF writter can only use JPEG images
            context.scene.render.image_settings.file_format = 'JPEG'
            bpy.ops.screen.screenshot(filepath=file_path,full=False) 
            bpy.ops.view3d.toolshelf()
            context.area.header_text_set()
            image = bpy.data.images.load(file_path)
            image_view = context.window_manager.mv.image_views.add()
            image_view.name = os.path.splitext(image.name)[0]
            image_view.image_name = image.name
            
            return {'FINISHED'}
            
        return {'RUNNING_MODAL'}

def register():
    bpy.utils.register_class(PANEL_2d_views)
    bpy.utils.register_class(LIST_scenes)
    bpy.utils.register_class(LIST_2d_images)
    bpy.utils.register_class(MENU_2dview_reports)
    bpy.utils.register_class(MENU_elevation_scene_options)
    bpy.utils.register_class(OPERATOR_genereate_2d_views)
    bpy.utils.register_class(OPERATOR_render_2d_views)
    bpy.utils.register_class(OPERATOR_view_image)
    bpy.utils.register_class(OPERATOR_delete_image)
    bpy.utils.register_class(OPERATOR_create_new_view)
    bpy.utils.register_class(OPERATOR_append_to_view)
    bpy.utils.register_class(OPERATOR_create_snap_shot)
    
    bpy.utils.register_class(OPERATOR_move_image_list_item)
    
    report_2d_drawings.register()

def unregister():
    bpy.utils.unregister_class(PANEL_2d_views)
    bpy.utils.unregister_class(LIST_scenes)
    bpy.utils.unregister_class(LIST_2d_images)
    bpy.utils.unregister_class(MENU_2dview_reports)
    bpy.utils.unregister_class(MENU_elevation_scene_options)
    bpy.utils.unregister_class(OPERATOR_genereate_2d_views)
    bpy.utils.unregister_class(OPERATOR_render_2d_views)
    bpy.utils.unregister_class(OPERATOR_view_image)
    bpy.utils.unregister_class(OPERATOR_delete_image)
    bpy.utils.unregister_class(OPERATOR_create_new_view)
    bpy.utils.unregister_class(OPERATOR_append_to_view)
    bpy.utils.unregister_class(OPERATOR_create_snap_shot)
    
    bpy.utils.unregister_class(OPERATOR_move_image_list_item)

    report_2d_drawings.unregister()

if __name__ == "__main__":
    register()
