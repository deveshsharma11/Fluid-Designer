"""
Microvellum 
Carcass
Stores the construction logic for the different types of carcasses that are available
in the frameless and face frame library
"""

from mv import unit, fd_types

EXPOSED_CABINET_MATERIAL = ("Plastics","Melamine","White Melamine")
UNEXPOSED_CABINET_MATERIAL = ("Wood","Wood Core","PB")
SEMI_EXPOSED_CABINET_MATERIAL = ("Plastics","Melamine","White Melamine")
DOOR_BOX_MATERIAL = ("Plastics","Melamine","White Melamine")
DOOR_MATERIAL = ("Plastics","Melamine","White Melamine")
GLASS_MATERIAL = ("Glass","Glass","Glass")
METAL = ("Metals","Metals","Stainless Steel")
DRAWER_BOX_MATERIAL = ("Plastics","Melamine","White Melamine")
COUNTER_TOP_MATERIAL = ("Stone","Marble","Basalt Slate")

class Material_Pointers():
    
    Exposed_Exterior_Surface = fd_types.Material_Pointer(EXPOSED_CABINET_MATERIAL)

    Exposed_Interior_Surface = fd_types.Material_Pointer(EXPOSED_CABINET_MATERIAL)

    Semi_Exposed_Surface = fd_types.Material_Pointer(SEMI_EXPOSED_CABINET_MATERIAL)
    
    Exposed_Exterior_Edge = fd_types.Material_Pointer(EXPOSED_CABINET_MATERIAL)

    Exposed_Interior_Edge = fd_types.Material_Pointer(EXPOSED_CABINET_MATERIAL)

    Semi_Exposed_Edge = fd_types.Material_Pointer(EXPOSED_CABINET_MATERIAL)

    Concealed_Surface = fd_types.Material_Pointer(UNEXPOSED_CABINET_MATERIAL)

    Concealed_Edge = fd_types.Material_Pointer(UNEXPOSED_CABINET_MATERIAL)

    Door_Surface = fd_types.Material_Pointer(DOOR_MATERIAL)
    
    Door_Edge = fd_types.Material_Pointer(DOOR_MATERIAL)

    Glass = fd_types.Material_Pointer(GLASS_MATERIAL)

    Cabinet_Pull_Finish = fd_types.Material_Pointer(METAL)
    
    Drawer_Box_Surface = fd_types.Material_Pointer(DRAWER_BOX_MATERIAL)

    Countertop_Surface = fd_types.Material_Pointer(COUNTER_TOP_MATERIAL)

    Cabinet_Moldings = fd_types.Material_Pointer(EXPOSED_CABINET_MATERIAL)