from odoo import _, api, fields, models


class PsychologySession(models.Model):
    _name = "cs.psychology.session"
    _description = "Sesión de psicología"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "session_date desc, id desc"

    name = fields.Char(string="Referencia", required=True, copy=False, default=lambda self: _("Nueva sesión"))
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
    psychologist_id = fields.Many2one(
        "cs.worker",
        string="Psicólogo/a",
        tracking=True,
        domain=[("job_title", "=", "psicólogo")],
    )
    session_date = fields.Datetime(
        string="Fecha y hora",
        required=True,
        default=fields.Datetime.now,
        tracking=True,
    )
    duration_minutes = fields.Integer(string="Duración (min)", default=50)
    session_type = fields.Selection(
        [
            ("individual", "Individual"),
            ("familiar", "Familiar"),
            ("grupal", "Grupal"),
            ("coordinacion", "Coordinación"),
        ],
        string="Tipo de sesión",
        default="individual",
        tracking=True,
    )
    state = fields.Selection(
        [
            ("planned", "Planificada"),
            ("done", "Realizada"),
            ("cancelled", "Cancelada"),
        ],
        string="Estado",
        default="planned",
        tracking=True,
    )
    summary = fields.Text(string="Resumen / objetivos")
    notes = fields.Text(string="Notas clínicas")

    assessment_template_id = fields.Many2one(
        "cs.followup.template",
        string="Plantilla de evaluación",
        domain=[("state", "=", "published")],
        tracking=True,
    )
    assessment_id = fields.Many2one(
        "cs.followup.assessment",
        string="Evaluación vinculada",
        domain="[('patient_id', '=', partner_id)]",
        tracking=True,
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
        help="PDF, informes escaneados, imágenes u otros archivos vinculados a la sesión.",
    )

    def action_mark_done(self):
        self.write({"state": "done"})

    def action_mark_cancelled(self):
        self.write({"state": "cancelled"})

    def action_set_planned(self):
        self.write({"state": "planned"})

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name") in (False, _("Nueva sesión")):
                vals["name"] = self.env["ir.sequence"].next_by_code("cs.psychology.session") or _("Nueva sesión")
        return super().create(vals_list)
