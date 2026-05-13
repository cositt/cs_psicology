from datetime import timedelta

from odoo import api, fields, models

# Context keys evitan bucles de sincronización sesión ↔ calendario
CTX_SKIP_SESSION_SYNC = "cs_psych_calendar_skip_session_sync"
CTX_SKIP_CALENDAR_SYNC = "cs_psych_calendar_skip_calendar_sync"


class CalendarEvent(models.Model):
    _inherit = "calendar.event"

    cs_is_psychology_visit = fields.Boolean(
        string="Visita de psicología",
        default=False,
        index=True,
        help="Marca la cita para filtrarla en el gestor de psicología y mostrar campos del centro.",
    )
    cs_resident_id = fields.Many2one(
        "cs.resident",
        string="Residente",
        index=True,
        tracking=True,
    )
    cs_residence_id = fields.Many2one(
        "cs.residence",
        string="Residencia",
        tracking=True,
    )
    cs_room_id = fields.Many2one(
        "cs.room",
        string="Habitación",
        tracking=True,
        domain="[('residence_id', '=', cs_residence_id)]",
    )
    cs_psychologist_worker_id = fields.Many2one(
        "cs.worker",
        string="Psicólogo/a",
        domain=[("job_title", "=", "psicólogo")],
        tracking=True,
    )
    cs_visit_mode = fields.Selection(
        [
            ("individual", "Individual"),
            ("familiar", "Familiar"),
            ("grupal", "Grupal"),
            ("coordinacion", "Coordinación"),
            ("otro", "Otro"),
        ],
        string="Tipo de visita",
        default="individual",
    )
    cs_psychology_session_id = fields.Many2one(
        "cs.psychology.session",
        string="Sesión de psicología",
        ondelete="set null",
        copy=False,
        index=True,
    )

    @api.onchange("cs_resident_id")
    def _onchange_cs_resident_calendar(self):
        if self.cs_resident_id:
            self.cs_residence_id = self.cs_resident_id.residence_id
            self.cs_room_id = self.cs_resident_id.room_id
            if self.cs_resident_id.partner_id:
                self.partner_ids |= self.cs_resident_id.partner_id

    @api.onchange("cs_psychologist_worker_id")
    def _onchange_cs_psychologist_calendar(self):
        if self.cs_psychologist_worker_id and self.cs_psychologist_worker_id.partner_id:
            self.partner_ids |= self.cs_psychologist_worker_id.partner_id

    def write(self, vals):
        res = super().write(vals)
        if self.env.context.get(CTX_SKIP_CALENDAR_SYNC):
            return res
        watch = {"start", "stop", "duration"}
        if not watch & vals.keys():
            return res
        for event in self:
            sess = event.cs_psychology_session_id
            if not sess:
                continue
            upd = {}
            if event.start:
                upd["session_date"] = event.start
            if event.stop and event.start:
                mins = int((event.stop - event.start).total_seconds() // 60)
                if mins > 0:
                    upd["duration_minutes"] = mins
            if upd:
                sess.with_context(**{CTX_SKIP_SESSION_SYNC: True}).write(upd)
        return res
