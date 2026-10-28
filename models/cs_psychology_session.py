from datetime import timedelta

from markupsafe import Markup

from odoo import _, api, fields, models
from odoo.tools import html_escape

from .calendar_event import CTX_SKIP_CALENDAR_SYNC, CTX_SKIP_SESSION_SYNC


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

    calendar_event_id = fields.Many2one(
        "calendar.event",
        string="Cita en calendario",
        copy=False,
        ondelete="set null",
    )

    def action_mark_done(self):
        self.write({"state": "done"})

    def action_mark_cancelled(self):
        self.write({"state": "cancelled"})

    def action_set_planned(self):
        self.write({"state": "planned"})

    def action_open_calendar_event(self):
        self.ensure_one()
        if not self.calendar_event_id:
            return {"type": "ir.actions.act_window_close"}
        return {
            "type": "ir.actions.act_window",
            "name": _("Cita en calendario"),
            "res_model": "calendar.event",
            "view_mode": "form",
            "res_id": self.calendar_event_id.id,
            "target": "current",
        }

    def _calendar_organizer_user(self):
        self.ensure_one()
        if self.psychologist_id and self.psychologist_id.partner_id:
            user = self.env["res.users"].sudo().search(
                [("partner_id", "=", self.psychologist_id.partner_id.id)],
                limit=1,
            )
            if user:
                return user
        return self.env.user

    def _calendar_location_text(self):
        self.ensure_one()
        parts = []
        if self.resident_id.residence_id:
            parts.append(self.resident_id.residence_id.name)
        if self.resident_id.room_id:
            parts.append(_("Hab. %s") % self.resident_id.room_id.name)
        return ", ".join(parts)

    def _calendar_description_html(self):
        self.ensure_one()
        chunks = []
        if self.summary:
            chunks.append(
                "<p><strong>Resumen</strong><br/>%s</p>" % html_escape(self.summary)
            )
        if self.notes:
            chunks.append(
                "<p><strong>Notas</strong><br/>%s</p>" % html_escape(self.notes)
            )
        return Markup("".join(chunks)) if chunks else False

    def _calendar_event_subject(self):
        self.ensure_one()
        labels = dict(self._fields["session_type"].selection)
        st = labels.get(self.session_type, "")
        return _("Psicología — %(name)s (%(type)s)") % {
            "name": self.resident_id.name,
            "type": st,
        }

    def _calendar_partner_commands(self, event=None):
        self.ensure_one()
        resident_p = self.resident_id.partner_id
        psych_p = (
            self.psychologist_id.partner_id
            if self.psychologist_id
            else self.env["res.partner"]
        )
        mandatory = resident_p | psych_p
        if event:
            extra = event.partner_ids - mandatory
            merged = mandatory | extra
        else:
            merged = mandatory
        return [(6, 0, merged.ids)]

    def _sync_calendar_event(self):
        CalendarEvent = self.env["calendar.event"]
        for session in self:
            ev = session.calendar_event_id
            if session.state == "cancelled":
                if ev:
                    ev.with_context(**{CTX_SKIP_CALENDAR_SYNC: True}).write(
                        {"active": False}
                    )
                continue
            stop_dt = session.session_date + timedelta(
                minutes=session.duration_minutes or 50
            )
            org_user = session._calendar_organizer_user()
            loc = session._calendar_location_text()
            desc = session._calendar_description_html()
            vals = {
                "name": session._calendar_event_subject(),
                "start": session.session_date,
                "stop": stop_dt,
                "user_id": org_user.id,
                "partner_ids": session._calendar_partner_commands(ev),
                "location": loc or False,
                "description": desc,
                "privacy": "confidential",
                "show_as": "busy",
                "allday": False,
                "active": True,
                "cs_is_psychology_visit": True,
                "cs_resident_id": session.resident_id.id,
                "cs_residence_id": session.resident_id.residence_id.id
                if session.resident_id.residence_id
                else False,
                "cs_room_id": session.resident_id.room_id.id
                if session.resident_id.room_id
                else False,
                "cs_psychologist_worker_id": session.psychologist_id.id
                if session.psychologist_id
                else False,
                "cs_visit_mode": session.session_type,
                "cs_psychology_session_id": session.id,
                "res_model": "cs.psychology.session",
                "res_id": session.id,
            }
            ctx_cal = {CTX_SKIP_CALENDAR_SYNC: True}
            if ev:
                CalendarEvent.browse(ev.id).with_context(**ctx_cal).write(vals)
            else:
                new_ev = CalendarEvent.with_context(**ctx_cal).create(vals)
                super(
                    PsychologySession,
                    session.with_context(**{CTX_SKIP_SESSION_SYNC: True}),
                ).write({"calendar_event_id": new_ev.id})

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("name") or vals["name"] == _("Nueva sesión"):
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("cs.psychology.session")
                    or _("Nueva sesión")
                )
        records = super().create(vals_list)
        records._sync_calendar_event()
        return records

    def write(self, vals):
        res = super().write(vals)
        if self.env.context.get(CTX_SKIP_SESSION_SYNC):
            return res
        self._sync_calendar_event()
        return res

    def unlink(self):
        events = self.mapped("calendar_event_id")
        events.unlink()
        return super().unlink()
