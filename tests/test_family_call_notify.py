from odoo import Command
from odoo.tests import tagged
from odoo.tests.common import TransactionCase, new_test_user


@tagged('post_install', '-at_install', 'cs_psychology')
class TestFamilyCallNotifiesTherapist(TransactionCase):
    """Ronda Salud (Nacho, 18-11-2026): registering a family call creates an
    activity for the resident's therapist."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.therapist = new_test_user(cls.env, login='terapeuta_llamadas', name='Terapeuta Llamadas')
        cls.monitor = new_test_user(cls.env, login='monitora_llamadas', name='Monitora Llamadas')
        cls.resident = cls.env['cs.resident'].create({
            'name': 'Residente Aviso Llamadas',
            'dni': '77777778B',
            'fecha_nacimiento': '1980-01-01',
            'therapist_user_id': cls.therapist.id,
        })
        cls.todo = cls.env.ref('mail.mail_activity_data_todo')
        cls.psychology_group = cls.env.ref('cs_piai.group_cs_psychology', raise_if_not_found=False)

    def _register_call(self, resident=None, user=None):
        env = self.env(user=user or self.monitor)
        return env['cs.family.call'].create({
            'resident_id': (resident or self.resident).id,
            'contacted_name': 'Hermana del residente',
            'notes': 'Pregunta por la medicación',
        }).sudo()

    def _activities(self, call):
        return self.env['mail.activity'].search([
            ('res_model', '=', 'cs.family.call'), ('res_id', '=', call.id),
        ])

    def test_activity_for_reference_therapist(self):
        call = self._register_call()
        activity = self._activities(call)
        self.assertEqual(len(activity), 1)
        self.assertEqual(activity.user_id, self.therapist)
        self.assertEqual(activity.activity_type_id, self.todo)
        self.assertIn('Hermana del residente', activity.summary)
        self.assertIn('Residente Aviso Llamadas', activity.summary)

    def test_no_activity_when_therapist_registers_the_call(self):
        call = self._register_call(user=self.therapist)
        self.assertFalse(self._activities(call))

    def test_fallback_to_psychology_group(self):
        if not self.psychology_group:
            self.skipTest('cs_piai not installed')
        resident = self.resident.copy({'dni': '77777779N', 'therapist_user_id': False})
        self.psychology_group.user_ids = [Command.set(self.therapist.ids)]
        call = self._register_call(resident=resident)
        self.assertEqual(self._activities(call).user_id, self.therapist)

    def test_nobody_to_notify_leaves_a_note(self):
        resident = self.resident.copy({'dni': '77777770T', 'therapist_user_id': False})
        if self.psychology_group:
            self.psychology_group.user_ids = [Command.clear()]
        call = self._register_call(resident=resident)
        self.assertFalse(self._activities(call))
        self.assertIn('Terapeuta de referencia', call.message_ids[0].body)

    def test_therapist_field_only_internal_users(self):
        domain = self.env['cs.resident']._fields['therapist_user_id'].domain
        self.assertIn(('share', '=', False), domain)
