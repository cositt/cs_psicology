from odoo import _, api, fields, models


class InitialPsychAssessment(models.Model):
    _name = "cs.initial.assessment"
    _description = "Evaluación psicológica inicial"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "assessment_date desc, id desc"

    name = fields.Char(string="Referencia", required=True, copy=False, default=lambda self: _("Nueva evaluación"))
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
    assessment_date = fields.Date(
        string="Fecha",
        required=True,
        default=fields.Date.context_today,
        tracking=True,
    )
    state = fields.Selection(
        [
            ("draft", "Borrador"),
            ("done", "Cerrada"),
        ],
        string="Estado",
        default="draft",
        tracking=True,
    )
    reason_for_referral = fields.Text(string="Motivo de derivación / demanda")
    background_summary = fields.Text(string="Antecedentes relevantes")
    initial_hypothesis = fields.Text(string="Hipótesis / impresión inicial")
    risk_notes = fields.Text(string="Riesgo / alertas")
    recommendations = fields.Text(string="Recomendaciones / plan inicial")

    assessment_template_id = fields.Many2one(
        "cs.followup.template",
        string="Plantilla",
        domain=[("state", "=", "published")],
    )
    assessment_id = fields.Many2one(
        "cs.followup.assessment",
        string="Evaluación (formulario)",
        domain="[('patient_id', '=', partner_id)]",
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
        help="PDF, informes, capturas u otros archivos vinculados a la evaluación.",
    )

    def action_mark_done(self):
        self.write({"state": "done"})

    def action_set_draft(self):
        self.write({"state": "draft"})

    @api.onchange('assessment_template_id')
    def _onchange_assessment_template_id(self):
        if self.assessment_template_id and not self.assessment_id:
            assessment = self.env['cs.followup.assessment'].create({
                'template_id': self.assessment_template_id.id,
                'patient_id': self.partner_id.id,
                'clinician_id': self.env.user.id,
                'assessment_date': self.assessment_date or fields.Date.context_today(self),
            })
            self.assessment_id = assessment.id

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("name") or vals["name"] == _("Nueva evaluación"):
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("cs.initial.assessment") or _("Nueva evaluación")
                )
        records = super().create(vals_list)
        admission_id = self.env.context.get('default_admission_id')
        if admission_id and records:
            self.env['cs.admission.process'].browse(admission_id).initial_assessment_id = records[0]
        return records
