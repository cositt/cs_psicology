# -*- coding: utf-8 -*-
from odoo import _, api, fields, models


class ResidentPsychologyExtend(models.Model):
    _inherit = 'cs.resident'

    family_call_ids = fields.One2many(
        'cs.family.call',
        'resident_id',
        string='Llamadas / contactos familiares',
    )

    psychology_session_count = fields.Integer(
        compute='_compute_psychology_session_count',
        string='Sesiones Psicología',
    )

    def _compute_psychology_session_count(self):
        groups = self.env['cs.psychology.session']._read_group(
            domain=[('resident_id', 'in', self.ids)],
            groupby=['resident_id'],
            aggregates=['__count'],
        )
        counts = {resident.id: count for resident, count in groups}
        for rec in self:
            rec.psychology_session_count = counts.get(rec.id, 0)

    def action_open_psychology_sessions(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Sesiones de Psicología — %s') % self.name,
            'res_model': 'cs.psychology.session',
            'view_mode': 'list,form',
            'domain': [('resident_id', '=', self.id)],
            'context': {'default_resident_id': self.id},
        }
