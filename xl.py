import xlwt
import os
import base64
from odoo import tools
from xlwt import Workbook
ADDONS_PATH=tools.config['addons_path'].split(",")[-1]

@api.multi
    def get_xml(self):
        lead_report={}
        lead_xl=[]
        
        lead_report['visit_seq']=self.visit_seqno
        lead_report['visitor_name']=self.visit_name
        lead_report['visit_date']=self.visit_date
        
        for line in self.product_ids:
            product={}
            product['name']=line.name.name,
            product['price']=line.price,
            product['quantity']=line.qty,
            product['total']=line.total,
            lead_xl.append(product)
        lead_report['products']=lead_xl    
        
        style0 = xlwt.easyxf('font: name Times New Roman, color-index black, bold on')
        style1 = xlwt.easyxf(num_format_str='D-MMM-YY')

        wb = xlwt.Workbook()
        ws = wb.add_sheet('A Excel  report')
        
        ws.write(1, 2, 'Sequence No',  style0)
        ws.write(1, 3, lead_report['visit_seq'] , style0)
        ws.write(2, 2, 'Visitor Name',  style0)
        ws.write(2, 3, lead_report['visitor_name'] , style0)
        ws.write(3, 2, 'Visit Date',  style0)
        ws.write(3, 3, lead_report['visit_date'] , style1)
        
        ws.write(7, 0, 'Product Name',  style0)
        ws.write(7, 1, 'Price',  style0)
        ws.write(7, 2, 'Quantity',  style0)
        ws.write(7, 3, 'Total',  style0)
         
#         n=8
#         for product in lead_report['products']:
#             ws.write(n, 0, product['name'] , style0)
#             ws.write(n, 1, product['price'] , style0)
#             ws.write(n, 2, product['quantity'] , style0)
#             ws.write(n, 3, product['total'] , style0)
#          
#             n+=1
        
        vis_time=datetime.now()
        date =vis_time.strftime('%d-%m-%Y')
        filename=os.path.join(ADDONS_PATH,'lead Report'+'_' + date + '.xls')
        wb.save(filename)
        lead_view=open(filename,'rb')
        file_data=lead_view.read()
        out=base64.encodestring(file_data)
        attach_value={
            'lead_char':'Lead Report' + '_' + date + '.xls',
            'lead_xml':out,
            }
        
        act_id=self.env['lead.report'].create(attach_value)
        lead_view.close()
        return{
            'type':'ir.actions.act_window',
            'view_type':'form',
            'view_mode':'form',
            'res_model':'lead.report',
            'res_id':act_id.id,
            'target':'new',
            }

class excelwizard(models.TransientModel):
    _name="lead.report"
    
    
    lead_xml=fields.Binary("Download Excel Report")
    lead_char=fields.Char("Excel File")
    
