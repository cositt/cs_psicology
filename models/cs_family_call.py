from odoo import _, api, fields, models


class FamilyCall(models.Model):
    _name = "cs.family.call"
    _description = "Llamada / contacto con familia"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "call_datetime desc, id desc"

    name = fields.Char(string="Referencia", required=True, copy=False, default=lambda self: _("Nuevo contacto"))
    resident_id = fields.Many2one(
        "cs.resident",
        string="Residente",
        required=True,
        index=True,
        tracking=True,
    )
    partner_id = fields.Many2one(
        related="resident_id.partner_id",
        comodel_name="res.partner",
        string="Paciente (contacto)",
        store=True,
        readonly=True,
    )
    call_datetime = fields.Datetime(
        string="Fecha y hora",
        required=True,
        default=fields.Datetime.now,
        tracking=True,
    )
    contacted_name = fields.Char(string="Persona contactada", required=True)
    relationship = fields.Char(string="Relación con el residente")
    duration_minutes = fields.Integer(string="Duración (min)")
    channel = fields.Selection(
        [
            ("phone", "Teléfono"),
            ("video", "Videollamada"),
            ("in_person", "Presencial"),
            ("other", "Otro"),
        ],
        string="Canal",
        default="phone",
    )
    outcome = fields.Selection(
        [
            ("info", "Información"),
            ("coordination", "Coordinación"),
            ("complaint", "Incidencia"),
            ("support", "Apoyo emocional"),
            ("other", "Otro"),
        ],
        string="Resultado",
        default="info",
    )
    notes = fields.Text(string="Notas")

    staff_id = fields.Many2one(
        "cs.worker",
        string="Profesional",
        tracking=True,
        help="Persona del centro que realizó el contacto",
    )

    company_id = fields.Many2one(
        "res.company",
        string="Compañía",
        required=True,
        default=lambda self: self.env.company,
    )

    attachment_ids = fields.Many2many(
        "ir.attachment",
        string="Documentos e imágenes",
        help="PDF, notas escaneadas, capturas de pantalla u otros archivos del contacto.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name") in (False, _("Nuevo contacto")):
                vals["name"] = self.env["ir.sequence"].next_by_code("cs.family.call") or _("Nuevo contacto")
        return super().create(vals_list)
