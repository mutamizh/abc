from odoo import api, fields, models, _
from odoo.api import multi, onchange
from datetime import datetime
import xlwt
import os
import base64
from odoo import tools
from xlwt import Workbook
ADDONS_PATH=tools.config['addons_path'].split(",")[-1]

 
 
class LeadProduct(models.Model):
    
    _name ="lead.product.line"
    
    @api.depends('quantity','price')
    def _compute_total(self):
        for line in self:
            if line.quantity or line.price:
                line.sub_total = line.quantity * line.price 
    
    product_id =fields.Many2one("product.product", string ="product")
    
    quantity =fields.Float("Quantity")
    product_uom_id =fields.Many2one("product.uom",string ="Unit of Measure")
    price =fields.Float("Price")
    sub_total =fields.Float(compute='_compute_total' ,string ="Sub total")
    
    lead_id =fields.Many2one("crm.lead")
    procurement_ids = fields.One2many('procurement.order', 'sale_line_id', string='Procurements')
    invoice_status = fields.Selection([
       ('upselling', 'Upselling Opportunity'),
       ('invoiced', 'Fully Invoiced'),
       ('to invoice', 'To Invoice'),
       ('no', 'Nothing to Invoice')
       ], string='Invoice Status', compute='_compute_invoice_status', store=True, readonly=True, default='no')

    
    qty_to_invoice = fields.Float(
        compute='_get_to_invoice_qty', string='To Invoice', store=True, readonly=True)
    qty_delivered_updateable = fields.Boolean(string='Can Edit Delivered', readonly=True, default=True)
    
    qty_invoiced = fields.Float(string='Invoiced', store=True, readonly=True)


    @api.onchange('product_id')
    def onchange_product(self):
         
        if self.product_id:
             
            self.price= self.product_id.list_price
            
            

            

 
class CrmLead(models.Model):
    _inherit = 'crm.lead'
    
    
    quot_number =fields.Integer("number",compute='_get_Quotation')
    product_line_ids =fields.One2many("lead.product.line","lead_id", string = "Order line")
    link_id =fields.Many2one("res.company")
    
    
    
    
    @api.multi
    def excel_function(self):
        
        lead_report={}
    
      
        lead_report['name']=self.name
        lead_report['logo'] =self.link_id.logo
        
            
        book = xlwt.Workbook('images.xlsx')
        ws = book.add_sheet('A Excel  report')
        ws.set_column('A:A', 30)
        ws.write('A2', 'Insert an image in a cell:')
#         ws.insert_image('B2', 'logo.png')

#         # add new colour to palette and set RGB colour value
#         xlwt.add_palette_colour("custom_colour", 0x21)
#         book.set_colour_RGB(0x21, 251, 228, 228)
#          
#         # now you can use the colour in styles
#         style = xlwt.easyxf('pattern: pattern solid, fore_colour custom_colour')
#         ws.write(0, 0, 'Some text', style)
        
#         style = xlwt.XFStyle()
#         pattern = xlwt.Pattern()
#         pattern.pattern = xlwt.Pattern.SOLID_PATTERN
#         pattern.pattern_fore_colour = xlwt.Style.colour_map['Blue']
#         style.pattern = pattern
            
        style1 = xlwt.easyxf('pattern: pattern solid, fore_colour red;')
        
        ws.write(1,1,'name', xlwt.easyxf('font: name Times New Roman, color-index black, bold on'))
        ws.write(1, 3, lead_report['name'] , style1)
        
        
        date_now=datetime.now()
         
        date =date_now.strftime('%d-%m-%Y')
         
        filename=os.path.join(ADDONS_PATH,'lead Report'+'_'+ date +'.xls')
         
        book.save(filename)
         
        lead_view=open(filename,'rb')
         
        file_data=lead_view.read()
         
        out=base64.encodestring(file_data)
         
        attach_value={
             
            'lead_char':'Lead_Report' + '_' + date + '.xls',
            'lead_xl':out,
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
 
     
     

    
    
    @api.depends('quot_number')
    def _get_Quotation(self):
        for rec in self:
            self.quot_number = self.env['sale.order'].search_count([('opportunity_id' ,'=', rec.id)])

    @api.multi
    def sale_quotation(self):
        ctx = dict()
   
        tree_id = self.env.ref('sale.view_order_tree').id
        form_id = self.env.ref('sale.view_order_form').id
             
        search_id =self[0].id
         
        return{
              'name': _('opportunity'),
              'type':'ir.actions.act_window',
              'view_type':'form',
              'domain':[('opportunity_id','=',search_id)],
              'view_mode':'tree,form',
              'res_model':'sale.order',
              'views_id':False,
              'views': [(tree_id, 'tree'), (form_id, 'form')],
              'target':'current',
              'context':ctx,

            }
        
        
        
        
        
    @api.multi
    def new_quotation(self):
        ctx = dict()
        
        product_line =[]
        
        pro_line ={}
            
        for record in self.product_line_ids:
            pro_line.update({'product_id':record.product_id.id,
                             'name':record.product_id.name,
                             'product_uom_qty':record.quantity,
                             'product_uom':record.product_uom_id.id,
                             'invoice_status':'no',
                             'procurement_ids':record.procurement_ids.id,
                             'qty_to_invoice':record.qty_to_invoice,
                             'qty_delivered_updateable':record.qty_delivered_updateable,
                             'qty_invoiced':record.qty_invoiced,
                             'price_unit':record.price,
            })
            product_line.append((0, 0, pro_line))
        
        ctx.update({
              'default_opportunity_id':self.id,
              'default_partner_id':self.partner_id.id,
              'default_order_line' :product_line,
            })
         
        form_view = self.env.ref('sale.view_order_form').id
          
        return{
              'name': _('quotation'),
              'type':'ir.actions.act_window',
              'view_type':'form',
              'view_mode':'form',
              'res_model':'sale.order',
              'views_id':False,
              'views':[(form_view or False, 'form')],
              'target':'current',
              'context':ctx,
              }


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    
    
    @api.multi
    def order_quotation(self):
        ctx = dict()
        
        form_id= self.env.ref('crm.crm_case_form_view_oppor').id

        order_id =self.env['sale.order'].search([('id' ,'=',self[0].opportunity_id.id)]).id
        
        print order_id

        return{
              'name': _('List of Order'),
              'type':'ir.actions.act_window',
              'view_type':'form',
              'view_mode':'form',
              'res_model':'crm.lead',
              'res_id' :order_id,
              'views_id':False,
              'views': [(form_id, 'form')],
            }
        
        
class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
     
     
     
    unit_price =fields.Integer("Unit price")
    product =fields.Many2one("product.product", string ="product")

    
    
class ProcurementOrder(models.Model):
    
    _inherit = 'procurement.order'
    
    sale_line_id = fields.Many2one('sale.order.line', string='Sale Order Line')
    
    
    
class ExcelFormat(models.TransientModel):
     
    _name="lead.report"
     
     
    lead_xl=fields.Binary("Download Excel Report")
     
    lead_char=fields.Char("Excel File")
     
        


    


