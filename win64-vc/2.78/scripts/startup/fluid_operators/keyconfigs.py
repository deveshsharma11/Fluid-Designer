import bpy

def register():
    
    wm = bpy.context.window_manager
    if wm.keyconfigs.addon:
    
        obj_km = wm.keyconfigs.addon.keymaps.new(name='Object Mode', space_type='EMPTY')
    
        kmi = obj_km.keymap_items.new('wm.console_toggle', 'HOME', 'PRESS', shift=True)
        
        kmi = obj_km.keymap_items.new('fd_general.properties', 'RIGHTMOUSE', 'PRESS')
        
        kmi = obj_km.keymap_items.new('wm.call_menu', 'A', 'PRESS', shift=True)
        kmi.properties.name = 'INFO_MT_fluidaddobject'
        
        edit_km = wm.keyconfigs.addon.keymaps.new(name='Mesh', space_type='EMPTY')
        
        kmi = edit_km.keymap_items.new('wm.call_menu', 'RIGHTMOUSE', 'PRESS')
        kmi.properties.name = 'MENU_right_click_menu_edit_mesh'
        
        edit_curve_km = wm.keyconfigs.addon.keymaps.new(name='Curve', space_type='EMPTY')
        
        kmi = edit_curve_km.keymap_items.new('wm.call_menu', 'RIGHTMOUSE', 'PRESS')
        kmi.properties.name = 'MENU_right_click_menu_edit_curve'    