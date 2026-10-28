from odoo.tests.common import TransactionCase


class TestPsychologySequences(TransactionCase):
    """Sin 'name' en vals, create debe asignar el número de secuencia."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.resident = cls.env['cs.resident'].create({
            'name': 'Residente Secuencias Psicología',
            'dni': '77777777X',
            'fecha_nacimiento': '1980-01-01',
        })

    def test_sesion_sin_nombre_recibe_secuencia(self):
        session = self.env['cs.psychology.session'].create({'resident_id': self.resident.id})
        self.assertNotEqual(session.name, 'Nueva sesión')
        self.assertRegex(session.name, r'\d')

    def test_evaluacion_inicial_sin_nombre_recibe_secuencia(self):
        assessment = self.env['cs.initial.assessment'].create({'resident_id': self.resident.id})
        self.assertNotEqual(assessment.name, 'Nueva evaluación')
        self.assertRegex(assessment.name, r'\d')

    def test_llamada_familiar_sin_nombre_recibe_secuencia(self):
        call = self.env['cs.family.call'].create({
            'resident_id': self.resident.id,
            'contacted_name': 'Familiar Test',
        })
        self.assertNotEqual(call.name, 'Nuevo contacto')
        self.assertRegex(call.name, r'\d')

    def test_nombre_explicito_se_respeta(self):
        session = self.env['cs.psychology.session'].create({
            'resident_id': self.resident.id,
            'name': 'REF-MANUAL',
        })
        self.assertEqual(session.name, 'REF-MANUAL')

    def test_contador_de_sesiones_del_residente(self):
        Session = self.env['cs.psychology.session']
        Session.create({'resident_id': self.resident.id})
        Session.create({'resident_id': self.resident.id})
        self.resident.invalidate_recordset(['psychology_session_count'])
        self.assertEqual(self.resident.psychology_session_count, 2)
