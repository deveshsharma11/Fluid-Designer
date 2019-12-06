import bpy
import math
import os
from mv import unit, utils, fd_types
from bpy.types import Operator

def get_export_prompts(obj_bp):
    """ Used in create_fluid_project_xml
        this collects all of the needed product prompts for the 121 product match
    """
    
    prompts = {}
    
    def add_prompt(prompt):
        if prompt.Type == 'NUMBER':
            prompts[prompt.name] = str(prompt.NumberValue)
        if prompt.Type == 'QUANTITY':
            prompts[prompt.name] = str(prompt.QuantityValue)
        if prompt.Type == 'COMBOBOX':
            prompts[prompt.name] = str(prompt.COL_EnumItem[prompt.EnumIndex].name)
        if prompt.Type == 'CHECKBOX':
            prompts[prompt.name] = str(prompt.CheckBoxValue)
        if prompt.Type == 'TEXT':
            prompts[prompt.name] = str(prompt.TextValue)
        if prompt.Type == 'DISTANCE':
            prompts[prompt.name] = str(round(unit.meter_to_active_unit(prompt.DistanceValue),4))
        if prompt.Type == 'ANGLE':
            prompts[prompt.name] = str(prompt.AngleValue)
        if prompt.Type == 'PERCENTAGE':
            prompts[prompt.name] = str(prompt.PercentageValue)
        if prompt.Type == 'PRICE':
            prompts[prompt.name] = str(prompt.PriceValue)
    
    def add_child_prompts(obj):
        for child in obj.children:
            if child.mv.type == 'BPASSEMBLY':
                add_prompts(child)
            if len(child.children) > 0:
                add_child_prompts(child)
        
    def add_prompts(obj):
        for prompt in obj.mv.PromptPage.COL_Prompt:
            if prompt.export:
                add_prompt(prompt)
                
    add_prompts(obj_bp)
    add_child_prompts(obj_bp)

    return prompts

class OPS_export_mvfd(Operator):
    bl_idname = "cabinetlib.export_mvfd"
    bl_label = "Export MVFD File"
    bl_description = "This will export a mvfd file. The file must be saved first."
    
    walls = []
    products = []
    buyout_products = []
    
    buyout_materials = []
    edgeband_materials = {}
    solid_stock_materials = {}
    
    xml = None
    
    @classmethod
    def poll(cls, context):
        if bpy.data.filepath != "":
            return True
        else:
            return False

    def distance(self,distance):
        return str(math.fabs(round(unit.meter_to_active_unit(distance),4)))
    
    def location(self,location):
        return str(round(unit.meter_to_active_unit(location),4))
    
    def angle(self,angle):
        return str(round(math.degrees(angle),4))
    
    def clear_and_collect_data(self,context):
        for product in self.products:
            self.products.remove(product)
        
        for wall in self.walls:
            self.walls.remove(wall)

        bpy.ops.fd_material.get_materials()
        for scene in bpy.data.scenes:
            if not scene.mv.plan_view_scene and not scene.mv.elevation_scene:
                for obj in scene.objects:
                    if not obj.mv.dont_export:
                        if obj.mv.type == 'BPWALL':
                            self.walls.append(obj)
                        if obj.mv.type == 'BPASSEMBLY':
                            if obj.mv.type_group == 'PRODUCT':
                                self.products.append(obj)
    
    def write_properties(self,project_node):
        elm_properties = self.xml.add_element(project_node,'Properties')
        for scene in bpy.data.scenes:
            for prop in scene.mv.project_properties:
                elm_prop = self.xml.add_element(elm_properties,'Property',prop.name)
                self.xml.add_element_with_text(elm_prop,'Value',prop.value)
                self.xml.add_element_with_text(elm_prop,'GlobalVariableName',prop.global_variable_name)
                self.xml.add_element_with_text(elm_prop,'ProjectWizardVariableName',prop.project_wizard_variable_name)
                self.xml.add_element_with_text(elm_prop,'SpecificationGroupName',prop.specification_group_name)
    
    def write_locations(self,project_node):
        elm_locations = self.xml.add_element(project_node,'Locations')
        for scene in bpy.data.scenes:
            if not scene.mv.plan_view_scene and not scene.mv.elevation_scene:
                self.xml.add_element(elm_locations,'Location',scene.name)
    
    def write_walls(self,project_node):
        elm_walls = self.xml.add_element(project_node,"Walls")
        
        for obj_wall in self.walls:
            wall = fd_types.Wall(obj_wall)
            wall_name = wall.obj_bp.mv.name_object if wall.obj_bp.mv.name_object != "" else wall.name
            elm_wall = self.xml.add_element(elm_walls,'Wall',wall_name)
            self.xml.add_element_with_text(elm_wall,'LinkID',obj_wall.name)
            self.xml.add_element_with_text(elm_wall,'LinkIDLocation',obj_wall.users_scene[0].name)
            self.xml.add_element_with_text(elm_wall,'Width',self.distance(wall.obj_x.location.x))
            self.xml.add_element_with_text(elm_wall,'Height',self.distance(wall.obj_z.location.z))
            self.xml.add_element_with_text(elm_wall,'Depth',self.distance(wall.obj_y.location.y))
            self.xml.add_element_with_text(elm_wall,'XOrigin',self.location(obj_wall.matrix_world[0][3]))
            self.xml.add_element_with_text(elm_wall,'YOrigin',self.location(obj_wall.matrix_world[1][3]))
            self.xml.add_element_with_text(elm_wall,'ZOrigin',self.location(obj_wall.matrix_world[2][3]))
            self.xml.add_element_with_text(elm_wall,'Angle',self.angle(obj_wall.rotation_euler.z))

    def write_products(self,project_node):
        specgroups = bpy.context.scene.mv.spec_groups
        elm_products = self.xml.add_element(project_node,"Products")
        item_number = 1
        for obj_product in self.products:
            spec_group = specgroups[obj_product.cabinetlib.spec_group_index]
            product = fd_types.Assembly(obj_product)
            product_name = product.obj_bp.mv.name_object if product.obj_bp.mv.name_object != "" else product.obj_bp.name
            elm_product = self.xml.add_element(elm_products,'Product',product_name)
            self.xml.add_element_with_text(elm_product,'LinkID',obj_product.name)
            self.xml.add_element_with_text(elm_product,'LinkIDWall',obj_product.parent.name if obj_product.parent else 'None')
            self.xml.add_element_with_text(elm_product,'IsBuyout','False')
            self.xml.add_element_with_text(elm_product,'IsCorner','False')
            self.xml.add_element_with_text(elm_product,'LinkIDLocation',obj_product.users_scene[0].name)
            self.xml.add_element_with_text(elm_product,'LinkIDSpecificationGroup',spec_group.name)
            if obj_product.mv.item_number == 0:
                self.xml.add_element_with_text(elm_product,'ItemNumber',str(item_number))
                item_number += 1
            else:
                self.xml.add_element_with_text(elm_product,'ItemNumber',str(obj_product.mv.item_number))
            self.xml.add_element_with_text(elm_product,'LinkIDLibrary',obj_product.mv.library_name)
            self.xml.add_element_with_text(elm_product,'Width',self.distance(product.obj_x.location.x))
            self.xml.add_element_with_text(elm_product,'Height',self.distance(product.obj_z.location.z))
            self.xml.add_element_with_text(elm_product,'Depth',self.distance(product.obj_y.location.y))
            self.xml.add_element_with_text(elm_product,'XOrigin',self.location(obj_product.matrix_world[0][3]))
            self.xml.add_element_with_text(elm_product,'YOrigin',self.location(obj_product.matrix_world[1][3]))
            self.xml.add_element_with_text(elm_product,'ZOrigin',self.location(self.get_product_z_location(product)))
            self.xml.add_element_with_text(elm_product,'Comment',obj_product.mv.comment)
            self.xml.add_element_with_text(elm_product,'Angle',self.angle(obj_product.parent.rotation_euler.z + obj_product.rotation_euler.z) if obj_product.parent else self.angle(obj_product.rotation_euler.z))
            
            #PRODUCTS MARKED TO EXPORT SUBASSEMBLIES WILL EXPORT A STRUCTURE
            #NESTED ONLY THREE LEVELS DEEP
            #PRODUCTS NOT MARKED WILL EXPORT A FLAT STRUCTURE ONE LEVEL DEEP
            if product.obj_bp.mv.export_product_subassemblies:
                use_recursive = False
            else:
                use_recursive = True
            
            elm_prompts = self.xml.add_element(elm_product,"Prompts")
            self.write_prompts_for_assembly(elm_prompts, product)
            
            elm_parts = self.xml.add_element(elm_product,"Parts")
            self.write_parts_for_product(elm_parts,obj_product,spec_group,recursive=use_recursive)
            
            elm_hardware = self.xml.add_element(elm_product,"Hardware")
            self.write_hardware_for_assembly(elm_hardware,obj_product,recursive=use_recursive)
            
            if not use_recursive:
                elm_subassemblies = self.xml.add_element(elm_product,"Subassemblies")
                self.write_subassemblies_for_product(elm_subassemblies,obj_product,spec_group)
            
    def write_parts_for_product(self,elm_parts,obj_bp,spec_group,recursive=False):
        for child in obj_bp.children:
            for nchild in child.children:
                if nchild.cabinetlib.type_mesh in {'CUTPART','SOLIDSTOCK','BUYOUT'}:
                    if not nchild.hide:
                        self.write_part_node(elm_parts, nchild, spec_group,recursive=recursive)
            if recursive:
                self.write_parts_for_product(elm_parts, child, spec_group,recursive=recursive)
            
    def write_subassemblies_for_product(self,elm_subassembly,obj_bp,spec_group):
        for child in obj_bp.children:
            if child.mv.export_as_subassembly:
                assembly = fd_types.Assembly(child)
                hide = assembly.get_prompt("Hide")
                if hide:
                    if hide.value():
                        continue #SKIP HIDDEN SUBASSEMBLIES
                comment = ""
                for achild in assembly.obj_bp.children:
                    if achild.mv.comment != "":
                        comment = achild.mv.comment
                        break
                sub_name = assembly.obj_bp.mv.name_object if assembly.obj_bp.mv.name_object != "" else assembly.obj_bp.name
                elm_item = self.xml.add_element(elm_subassembly,'Subassembly',sub_name)
                self.xml.add_element_with_text(elm_item,'LinkID',assembly.obj_bp.name)
                self.xml.add_element_with_text(elm_item,'IsBuyout','False')
                self.xml.add_element_with_text(elm_item,'XLocation',self.location(assembly.obj_bp.location.x))
                self.xml.add_element_with_text(elm_item,'YLocation',self.location(assembly.obj_bp.location.y))
                self.xml.add_element_with_text(elm_item,'ZLocation',self.location(assembly.obj_bp.location.z))
                self.xml.add_element_with_text(elm_item,'XDimension',self.distance(assembly.obj_x.location.x))
                self.xml.add_element_with_text(elm_item,'YDimension',self.distance(assembly.obj_y.location.y))
                self.xml.add_element_with_text(elm_item,'ZDimension',self.distance(assembly.obj_z.location.z))                
                self.xml.add_element_with_text(elm_item,'Comment',comment)
                
                elm_prompts = self.xml.add_element(elm_subassembly,"Prompts")
                self.write_prompts_for_assembly(elm_prompts, assembly)                
                
                elm_parts = self.xml.add_element(elm_item,"Parts")
                self.write_parts_for_subassembly(elm_parts,assembly.obj_bp,spec_group)
                
                elm_hardware = self.xml.add_element(elm_item,"Hardware")
                self.write_hardware_for_assembly(elm_hardware,assembly.obj_bp)                
                
                elm_subassemblies = self.xml.add_element(elm_item,"Subassemblies")
                self.write_nested_subassemblies(elm_subassemblies, assembly.obj_bp, spec_group)
            
    def write_nested_subassemblies(self,elm_subassembly,obj_bp,spec_group):
        for child in obj_bp.children:
            if child.mv.export_as_subassembly:
                assembly = fd_types.Assembly(child)
                hide = assembly.get_prompt("Hide")
                if hide:
                    if hide.value():
                        continue #SKIP HIDDEN SUBASSEMBLIES
                comment = ""
                for achild in assembly.obj_bp.children:
                    if achild.mv.comment != "":
                        comment = achild.mv.comment
                        break
                sub_name = assembly.obj_bp.mv.name_object if assembly.obj_bp.mv.name_object != "" else assembly.obj_bp.name
                elm_item = self.xml.add_element(elm_subassembly,'Subassembly',sub_name)
                self.xml.add_element_with_text(elm_item,'LinkID',assembly.obj_bp.name)
                self.xml.add_element_with_text(elm_item,'IsBuyout','False')
                self.xml.add_element_with_text(elm_item,'XLocation',self.location(assembly.obj_bp.location.x))
                self.xml.add_element_with_text(elm_item,'YLocation',self.location(assembly.obj_bp.location.y))
                self.xml.add_element_with_text(elm_item,'ZLocation',self.location(assembly.obj_bp.location.z))
                self.xml.add_element_with_text(elm_item,'XDimension',self.distance(assembly.obj_x.location.x))
                self.xml.add_element_with_text(elm_item,'YDimension',self.distance(assembly.obj_y.location.y))
                self.xml.add_element_with_text(elm_item,'ZDimension',self.distance(assembly.obj_z.location.z))
                self.xml.add_element_with_text(elm_item,'Comment',comment)
                
                elm_prompts = self.xml.add_element(elm_item,"Prompts")
                self.write_prompts_for_assembly(elm_prompts, assembly)
                
                elm_parts = self.xml.add_element(elm_item,"Parts")
                self.write_parts_for_subassembly(elm_parts,assembly.obj_bp,spec_group)
                
                elm_hardware = self.xml.add_element(elm_item,"Hardware")
                self.write_hardware_for_assembly(elm_hardware,assembly.obj_bp)                
            
    def write_parts_for_subassembly(self,elm_parts,obj_bp,spec_group):
        for child in obj_bp.children:
            for nchild in child.children:
                if nchild.cabinetlib.type_mesh in {'CUTPART','SOLIDSTOCK','BUYOUT'}:
                    if not nchild.hide:
                        self.write_part_node(elm_parts, nchild, spec_group)
            
    def write_hardware_for_assembly(self,elm_hardware,obj_bp,recursive=False):
        for child in obj_bp.children:
            if child.cabinetlib.type_mesh == 'HARDWARE':
                if not child.hide:
                    hardware_name = child.mv.name_object if child.mv.name_object != "" else child.name
                    elm_item = self.xml.add_element(elm_hardware,'Hardware',hardware_name)
                    
                    if child.mv.hardware_x_dim != 0:
                        self.xml.add_element_with_text(elm_item,'XDimension',self.distance(child.mv.hardware_x_dim))
                    else:
                        self.xml.add_element_with_text(elm_item,'XDimension',self.distance(child.dimensions.x))
                        
                    if child.mv.hardware_y_dim != 0:
                        self.xml.add_element_with_text(elm_item,'YDimension',self.distance(child.mv.hardware_y_dim))
                    else:
                        self.xml.add_element_with_text(elm_item,'YDimension',self.distance(child.dimensions.y))
                        
                    if child.mv.hardware_z_dim != 0:
                        self.xml.add_element_with_text(elm_item,'ZDimension',self.distance(child.mv.hardware_z_dim))
                    else:
                        self.xml.add_element_with_text(elm_item,'ZDimension',self.distance(child.dimensions.z))
                        
                    if recursive:
                        product_bp = utils.get_bp(child,'PRODUCT')
                        loc_pos = product_bp.matrix_world.inverted() * child.matrix_world
                        x_loc = self.location(loc_pos[0][3])
                        y_loc = self.location(loc_pos[1][3])
                        z_loc = self.location(loc_pos[2][3])                                     
                        self.xml.add_element_with_text(elm_item,'XOrigin',x_loc)
                        self.xml.add_element_with_text(elm_item,'YOrigin',y_loc)
                        self.xml.add_element_with_text(elm_item,'ZOrigin',z_loc)   
                    else:
                        loc_pos = child.parent.matrix_world.inverted() * child.matrix_world
                        x_loc = self.location(loc_pos[0][3])
                        y_loc = self.location(loc_pos[1][3])
                        z_loc = self.location(loc_pos[2][3])
                        self.xml.add_element_with_text(elm_item,'XOrigin',x_loc)
                        self.xml.add_element_with_text(elm_item,'YOrigin',y_loc)
                        self.xml.add_element_with_text(elm_item,'ZOrigin',z_loc)
                        
                    self.xml.add_element_with_text(elm_item,'Comment',child.mv.comment)
                    self.write_machine_tokens(elm_item,child)
                    
                    self.xml.add_element_with_text(elm_item,'AssociativeHardwareRotation',str(child.mv.associative_rotation))
                    
            if recursive:
                self.write_hardware_for_assembly(elm_hardware, child, recursive=recursive)

    def write_parts_for_nested_subassembly(self,elm_parts,obj_bp,spec_group):
        for child in obj_bp.children:
            if child.cabinetlib.type_mesh in {'CUTPART','SOLIDSTOCK','BUYOUT'}:
                if not child.hide:
                    self.write_part_node(elm_parts, child, spec_group)
    
    def write_prompts_for_assembly(self,elm_prompts,assembly):
        prompts_dict = get_export_prompts(assembly.obj_bp)
        for prompt in prompts_dict:
            elm_prompt = self.xml.add_element(elm_prompts,'Prompt',prompt)
            prompt_value = prompts_dict[prompt]
            if prompt_value == 'True':
                prompt_value = str(1)
            if prompt_value == 'False':
                prompt_value = str(0)
            self.xml.add_element_with_text(elm_prompt,'Value',prompt_value)

        #HEIGHT ABOVE FLOOR FOR PRODUCT IS OVERRIDDEN BY THE Z ORIGIN
        if assembly.obj_bp.mv.type_group == 'PRODUCT':
            if assembly.obj_bp.location.z > 0:
                elm_prompt = self.xml.add_element(elm_prompts,'Prompt',"HeightAboveFloor")
                self.xml.add_element_with_text(elm_prompt,'Value',"0")    
    
    def get_edgebanding_name(self,obj,edge,spec_group):
        if obj.mv.edgeband_material_name != "" and edge != "":
            thickness = utils.get_edgebanding_thickness_from_pointer_name(edge,spec_group)
            edge_mat_name = obj.mv.edgeband_material_name
            if edge_mat_name not in self.edgeband_materials and edge_mat_name != "":
                self.edgeband_materials[edge_mat_name] = thickness
            return edge_mat_name
        else:
            thickness = utils.get_edgebanding_thickness_from_pointer_name(edge,spec_group)
            edge_mat_name = utils.get_edgebanding_name_from_pointer_name(edge,spec_group)
            if edge_mat_name not in self.edgeband_materials and edge_mat_name != "":
                self.edgeband_materials[edge_mat_name] = thickness                
            return edge_mat_name
    
    def write_part_node(self,node,obj,spec_group,recursive=False):
        if obj.mv.type == 'BPASSEMBLY':
            assembly = fd_types.Assembly(obj)
        else:
            assembly = fd_types.Assembly(obj.parent)
        if assembly.obj_bp.mv.type_group != "PRODUCT":
            if obj.type == 'CURVE':
                curve_name = obj.mv.name_object if obj.mv.name_object != "" else obj.name
                elm_part = self.xml.add_element(node,'Part',curve_name)
            else:
                obj_name = assembly.obj_bp.mv.name_object if assembly.obj_bp.mv.name_object != "" else assembly.obj_bp.name
                elm_part = self.xml.add_element(node,'Part',obj_name)
            
            if obj.cabinetlib.type_mesh == 'CUTPART':
                self.xml.add_element_with_text(elm_part,'PartType',"2")
    
            if obj.cabinetlib.type_mesh == 'BUYOUT':
                self.xml.add_element_with_text(elm_part,'PartType',"4")
                if utils.get_material_name(obj) not in self.buyout_materials:
                    self.buyout_materials.append(utils.get_material_name(obj))
                    
            if obj.cabinetlib.type_mesh == 'SOLIDSTOCK':
                self.xml.add_element_with_text(elm_part,'PartType',"3")
                if utils.get_material_name(obj) not in self.solid_stock_materials:
                    self.solid_stock_materials[utils.get_material_name(obj)] = utils.get_part_thickness(obj)

            self.xml.add_element_with_text(elm_part,'LinkID',assembly.obj_bp.name)
            self.xml.add_element_with_text(elm_part,'Qty',self.get_part_qty(assembly))
            self.xml.add_element_with_text(elm_part,'MaterialName',utils.get_material_name(obj))
            self.xml.add_element_with_text(elm_part,'Thickness',self.distance(utils.get_part_thickness(obj)))
            self.xml.add_element_with_text(elm_part,'UseSMA','True' if obj.mv.use_sma else 'False')
            self.xml.add_element_with_text(elm_part,'LinkIDProduct',utils.get_bp(obj,'PRODUCT').name)
            self.xml.add_element_with_text(elm_part,'LinkIDParent',assembly.obj_bp.parent.name)
            self.xml.add_element_with_text(elm_part,'PartLength',self.get_part_length(assembly))
            self.xml.add_element_with_text(elm_part,'PartWidth',self.get_part_width(assembly))
            self.xml.add_element_with_text(elm_part,'Comment',self.get_part_comment(assembly.obj_bp))
            if recursive:
                self.xml.add_element_with_text(elm_part,'XOrigin',self.get_part_x_location(assembly.obj_bp,assembly.obj_bp.location.x))
                self.xml.add_element_with_text(elm_part,'YOrigin',self.get_part_y_location(assembly.obj_bp,assembly.obj_bp.location.y))
                self.xml.add_element_with_text(elm_part,'ZOrigin',self.get_part_z_location(assembly.obj_bp,assembly.obj_bp.location.z))
            else:
                loc_pos = assembly.obj_bp.parent.matrix_world.inverted() * assembly.obj_bp.matrix_world
                x_loc = self.location(loc_pos[0][3])
                y_loc = self.location(loc_pos[1][3])
                z_loc = self.location(loc_pos[2][3])
                self.xml.add_element_with_text(elm_part,'XOrigin',x_loc)
                self.xml.add_element_with_text(elm_part,'YOrigin',y_loc)
                self.xml.add_element_with_text(elm_part,'ZOrigin',z_loc)
            self.xml.add_element_with_text(elm_part,'XRotation',self.angle(assembly.obj_bp.rotation_euler.x))
            self.xml.add_element_with_text(elm_part,'YRotation',self.angle(assembly.obj_bp.rotation_euler.y))
            self.xml.add_element_with_text(elm_part,'ZRotation',self.angle(assembly.obj_bp.rotation_euler.z))
            
            self.xml.add_element_with_text(elm_part,'EdgeWidth1',self.get_edgebanding_name(obj, obj.mv.edge_w1, spec_group))
            self.xml.add_element_with_text(elm_part,'EdgeWidth2',self.get_edgebanding_name(obj, obj.mv.edge_w2, spec_group))
            self.xml.add_element_with_text(elm_part,'EdgeLength1',self.get_edgebanding_name(obj, obj.mv.edge_l1, spec_group))
            self.xml.add_element_with_text(elm_part,'EdgeLength2',self.get_edgebanding_name(obj, obj.mv.edge_l2, spec_group))
            
            self.xml.add_element_with_text(elm_part,'DrawToken3D',"DRAW3DBOX CABINET")
            self.xml.add_element_with_text(elm_part,'ElvToken2D',"DRAW2DBOX CABINET")
            self.xml.add_element_with_text(elm_part,'BasePoint',self.get_part_base_point(assembly))
            self.xml.add_element_with_text(elm_part,'MachinePoint',"1")
            self.xml.add_element_with_text(elm_part,'Par1',"")
            self.xml.add_element_with_text(elm_part,'Par2',"")
            self.xml.add_element_with_text(elm_part,'Par3',"")
            
            self.write_machine_tokens(elm_part, obj)
    
    def write_materials(self,project_node):
        elm_materials = self.xml.add_element(project_node,"Materials")
        for material in bpy.context.scene.cabinetlib.sheets:
            material_name = material.name if material.name != "" else "Unnamed"
            elm_material = self.xml.add_element(elm_materials,'Material',material_name)
            self.xml.add_element_with_text(elm_material,'Type',"2")
            self.xml.add_element_with_text(elm_material,'Thickness',self.distance(material.thickness))
            self.xml.add_element_with_text(elm_material,'LinkIDCoreRendering',material.core_material)
            self.xml.add_element_with_text(elm_material,'LinkIDTopFaceRendering',material.top_material)
            self.xml.add_element_with_text(elm_material,'LinkIDBottomFaceRendering',material.bottom_material)
            elm_sheets = self.xml.add_element(elm_material,"Sheets")
            for sheet in material.sizes:
                elm_sheet = self.xml.add_element(elm_sheets,'Sheet',self.distance(sheet.width) + " X " + self.distance(sheet.length))
                self.xml.add_element_with_text(elm_sheet,'Width',self.distance(sheet.width))
                self.xml.add_element_with_text(elm_sheet,'Length',self.distance(sheet.length))
                self.xml.add_element_with_text(elm_sheet,'LeadingLengthTrim',self.distance(sheet.leading_length_trim))
                self.xml.add_element_with_text(elm_sheet,'TrailingLengthTrim',self.distance(sheet.trailing_length_trim))
                self.xml.add_element_with_text(elm_sheet,'LeadingWidthTrim',self.distance(sheet.leading_width_trim))
                self.xml.add_element_with_text(elm_sheet,'TrailingWidthTrim',self.distance(sheet.trailing_width_trim))

    def write_edgebanding(self,project_node):
        elm_edgebanding = self.xml.add_element(project_node,"Edgebanding")
        for edgeband in self.edgeband_materials:
            elm_edge = self.xml.add_element(elm_edgebanding,'Edgeband',edgeband)
            self.xml.add_element_with_text(elm_edge,'Type',"3")
            self.xml.add_element_with_text(elm_edge,'Thickness',str(self.edgeband_materials[edgeband]))

    def write_buyout_materials(self,project_node):
        elm_buyouts = self.xml.add_element(project_node,"Buyouts")
        for buyout in self.buyout_materials:
            buyout_name = buyout if buyout != "" else "Unnamed"
            self.xml.add_element(elm_buyouts,'Buyout',buyout_name)
    
    def write_solid_stock_material(self,project_node):
        elm_solid_stocks = self.xml.add_element(project_node,"SolidStocks")
        for solid_stock in self.solid_stock_materials:
            solid_stock_name = solid_stock if solid_stock != "" else "Unnamed"
            elm_solid_stock = self.xml.add_element(elm_solid_stocks,'SolidStock',solid_stock_name)
            self.xml.add_element_with_text(elm_solid_stock,'Thickness',str(unit.meter_to_active_unit(self.solid_stock_materials[solid_stock])))
        
    def write_spec_groups(self,project_node):
        #Currently not being used but we might need to export spec groups at some point
        elm_spec_groups = self.xml.add_element(project_node,"SpecGroups")
        
        for spec_group in bpy.context.scene.mv.spec_groups:
            spec_group_name = spec_group.name if spec_group.name != "" else "Unnamed"
            elm_spec_group = self.xml.add_element(elm_spec_groups,'SpecGroup',spec_group_name)
            elm_cutparts = self.xml.add_element(elm_spec_group,'CutParts')
            for cutpart in spec_group.cutparts:
                elm_cutpart_name = cutpart.mv_pointer_name if cutpart.mv_pointer_name != "" else "Unnamed"
                elm_cutpart = self.xml.add_element(elm_cutparts,'PointerName',elm_cutpart_name)
                mat_name = utils.get_material_name_from_pointer(cutpart,spec_group)
                material_name = mat_name if mat_name != "" else "Unnamed"
                self.xml.add_element_with_text(elm_cutpart,'MaterialName',material_name)
                 
            elm_edgeparts = self.xml.add_element(elm_spec_group,'EdgeParts')
            for edgepart in spec_group.edgeparts:
                elm_edgepart_name = edgepart.mv_pointer_name if edgepart.mv_pointer_name != "" else "Unnamed"
                elm_edgepart = self.xml.add_element(elm_edgeparts,'PointerName',elm_edgepart_name)
                mat_name = utils.get_edgebanding_name_from_pointer_name(edgepart.name,spec_group)
                edge_material_name = mat_name if mat_name != "" else "Unnamed"
                self.xml.add_element_with_text(elm_edgepart,'MaterialName',edge_material_name)
                    
    def get_product_z_location(self,product):
        #Height Above Floor
        if product.obj_bp.location.z > 0:
            return product.obj_bp.location.z - math.fabs(product.obj_z.location.z)
        else:
            return product.obj_bp.location.z
    
    def get_part_qty(self,assembly):
        qty = 1
        z_quantity = assembly.get_prompt("Z Quantity")
        x_quantity = assembly.get_prompt("X Quantity")
        if z_quantity:
            qty += z_quantity.value() - 1
        
        if x_quantity:
            qty += x_quantity.value() - 1
            
        return str(qty)
        
    def get_part_width(self,assembly):
        width = math.fabs(assembly.obj_y.location.y)
        oversize_width = assembly.get_prompt("Oversize Width")
        if oversize_width:
            width += oversize_width.value()
        return self.distance(width)
    
    def get_part_length(self,assembly):
        length = math.fabs(assembly.obj_x.location.x)
        oversize_length = assembly.get_prompt("Oversize Length")
        if oversize_length:
            length += oversize_length.value()
        return self.distance(length)
        
    def get_part_x_location(self,obj,value):
        if obj.parent is None or obj.parent.mv.type_group == 'PRODUCT':
            return self.location(value)
        value += obj.parent.location.x
        return self.get_part_x_location(obj.parent,value)

    def get_part_y_location(self,obj,value):
        if obj.parent is None or obj.parent.mv.type_group == 'PRODUCT':
            return self.location(value)
        value += obj.parent.location.y
        return self.get_part_y_location(obj.parent,value)

    def get_part_z_location(self,obj,value):
        if obj.parent is None or obj.parent.mv.type_group == 'PRODUCT':
            return self.location(value)
        value += obj.parent.location.z
        return self.get_part_z_location(obj.parent,value)

    def get_part_comment(self,obj):
        return obj.mv.comment + "|" + obj.mv.comment_2 + "|" + obj.mv.comment_3 

    def get_part_base_point(self,assembly):
        mx = False
        my = False
        mz = False
        
        if assembly.obj_x.location.x < 0:
            mx = True
        if assembly.obj_y.location.y < 0:
            my = True
        if assembly.obj_z.location.z < 0:
            mz = True
            
        if (mx == False) and (my == False) and (mz == False):
            return "1"
        if (mx == False) and (my == False) and (mz == True):
            return "2"        
        if (mx == False) and (my == True) and (mz == False):
            return "3"
        if (mx == False) and (my == True) and (mz == True):
            return "4"
        if (mx == True) and (my == True) and (mz == False):
            return "5"
        if (mx == True) and (my == True) and (mz == True):
            return "6"        
        if (mx == True) and (my == False) and (mz == False):
            return "7"
        if (mx == True) and (my == False) and (mz == True):
            return "8"   
             
        return "1"

    def write_machine_tokens(self,elm_part,obj_part):
        elm_tokens = self.xml.add_element(elm_part,"MachineTokens")
        for token in obj_part.mv.mp.machine_tokens:
            if not token.is_disabled:
                token_name = token.name if token.name != "" else "Unnamed"
                elm_token = self.xml.add_element(elm_tokens,'MachineToken',token_name)
                param_dict = token.create_parameter_dictionary()
                if token.type_token in {'CORNERNOTCH','CHAMFER','3SIDEDNOTCH'}:
                    instructions = token.type_token + token.face + " " + token.edge
                elif token.type_token == 'SLIDE':
                    instructions = token.type_token
                else:
                    instructions = token.type_token + token.face
                self.xml.add_element_with_text(elm_token,'Instruction',instructions)
                self.xml.add_element_with_text(elm_token,'Par1',param_dict['Par1'])
                self.xml.add_element_with_text(elm_token,'Par2',param_dict['Par2'])
                self.xml.add_element_with_text(elm_token,'Par3',param_dict['Par3'])
                self.xml.add_element_with_text(elm_token,'Par4',param_dict['Par4'])
                self.xml.add_element_with_text(elm_token,'Par5',param_dict['Par5'])
                self.xml.add_element_with_text(elm_token,'Par6',param_dict['Par6'])
                self.xml.add_element_with_text(elm_token,'Par7',param_dict['Par7'])
                self.xml.add_element_with_text(elm_token,'Par8',param_dict['Par8'])
                self.xml.add_element_with_text(elm_token,'Par9',param_dict['Par9'])
 
    def execute(self, context):
        project_name, ext = os.path.splitext(os.path.basename(bpy.data.filepath))
        
        self.clear_and_collect_data(context)

        self.xml = fd_types.MV_XML()
        root = self.xml.create_tree()
        elm_project = self.xml.add_element(root,'Project',project_name)
        self.write_properties(elm_project)
        self.write_locations(elm_project)
        self.write_walls(elm_project)
        self.write_products(elm_project)
        self.write_materials(elm_project)
        self.write_edgebanding(elm_project)
        self.write_buyout_materials(elm_project)
        self.write_solid_stock_material(elm_project)

        path = os.path.join(os.path.dirname(bpy.data.filepath),"MV.xml")
        self.xml.write(path)
        return {'FINISHED'}
    
def register():
    bpy.utils.register_class(OPS_export_mvfd)

def unregister():
    bpy.utils.unregister_class(OPS_export_mvfd)    
    