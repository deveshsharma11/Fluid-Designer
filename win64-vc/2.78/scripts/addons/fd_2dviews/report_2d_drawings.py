import bpy
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import legal, inch, A4, landscape
from reportlab.platypus import Paragraph, Table, TableStyle, SimpleDocTemplate, Image, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import reportlab.lib.colors as colors

class OPERATOR_create_pdf(bpy.types.Operator):
    bl_idname = "2dviews.report_2d_drawings"
    bl_label = "Report 2D Drawing"
    bl_description = "This creates a 2D drawing pdf of all of the images"
    
#     image_name = bpy.props.StringProperty(name="Object Name",
#                                           description="This is the readable name of the object")

    def execute(self, context):
        pdf_images = []
        props = context.scene.mv
        width, height = landscape(legal)
        
        images = context.window_manager.mv.image_views
        for img in images:
            image = bpy.data.images[img.image_name]
            image.save_render(os.path.join(bpy.app.tempdir, image.name + ".jpg"))
            pdf_images.append(os.path.join(bpy.app.tempdir, image.name + ".jpg"))

        if bpy.data.filepath == "":
            file_path = bpy.app.tempdir
            room_name = "Unsaved"
        else:
            project_path = os.path.dirname(bpy.data.filepath)
            room_name, ext = os.path.splitext(os.path.basename(bpy.data.filepath))
            file_path = os.path.join(project_path,room_name)
            if not os.path.exists(file_path):
                os.makedirs(file_path)
                
        file_name = '2D Views.pdf'
        
        c = canvas.Canvas(os.path.join(file_path,file_name), pagesize=landscape(legal))
        logo = os.path.join(os.path.dirname(__file__),"logo.jpg")
        for img in pdf_images:
            #PICTURE
            c.drawImage(img,20,80,width=width-40, height=height-100, mask='auto',preserveAspectRatio=True)  
            #LOGO
            c.drawImage(logo,25,20,width=200, height=60, mask='auto',preserveAspectRatio=True) 
            #PICTURE BOX
            c.rect(20,80,width-40,height-100)
            #LOGO BOX
            c.rect(20,20,220,60)
            #COMMENT BOX
            c.setFont("Times-Roman",9)
            c.drawString(width-20-250+5, 67, "COMMENTS:")
            c.rect(width-20-248,20,248,60)
            #CLIENT
            c.drawString(245, 67, "CLIENT: " + props.client_name)
            c.rect(240,60,250,20)
            #PHONE
            c.drawString(245, 47, "PHONE: " + props.client_phone)
            c.rect(240,40,250,20)
            #EMAIL
            c.drawString(245, 27, "EMAIL: " + props.client_email)
            c.rect(240,20,250,20)                  
            #JOBNAME
            c.drawString(495, 67, "JOB NAME: " + props.job_name)
            c.rect(490,60,250,20)
            #JOBNAME
            c.drawString(495, 47, "ROOM: " + room_name)
            c.rect(490,40,250,20)
            #DRAWN BY
            c.drawString(495, 27, "DRAWN BY: " + props.designer_name)
            c.rect(490,20,250,20)
            c.showPage()
            
        c.save()
        
        #FIX FILE PATH To remove all double backslashes 
        fixed_file_path = os.path.normpath(file_path)

        if os.path.exists(os.path.join(fixed_file_path,file_name)):
            os.system('start "Title" /D "'+fixed_file_path+'" "' + file_name + '"')
        else:
            print('Cannot Find ' + os.path.join(fixed_file_path,file_name))
            
        return {'FINISHED'}
    
def menu_draw(self, context):
    self.layout.operator("2dviews.report_2d_drawings")    
    
def register():
    bpy.utils.register_class(OPERATOR_create_pdf)
    bpy.types.MENU_2dview_reports.append(menu_draw)
    
def unregister():
    bpy.utils.unregister_class(OPERATOR_create_pdf)
    