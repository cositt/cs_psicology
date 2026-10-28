from odoo.tests import tagged
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


@tagged('post_install', '-at_install')
class TestPsychologySequencesMultiCompany(TransactionCase):
    """Las secuencias son compartidas: numeran en cualquier compañía."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.other_company = cls.env['res.company'].create({'name': 'Compañía Secuencias Test'})
        cls.env.user.company_ids |= cls.other_company
        cls.resident = cls.env['cs.resident'].create({
            'name': 'Residente Otra Compañía',
            'dni': '66666666W',
            'fecha_nacimiento': '1980-01-01',
        })

    def test_sesion_en_otra_compania_recibe_secuencia(self):
        session = self.env['cs.psychology.session'].with_company(self.other_company).create({
            'resident_id': self.resident.id,
        })
        self.assertTrue(session.name.startswith('PSY/SES/'))

    def test_evaluacion_en_otra_compania_recibe_secuencia(self):
        assessment = self.env['cs.initial.assessment'].with_company(self.other_company).create({
            'resident_id': self.resident.id,
        })
        self.assertTrue(assessment.name.startswith('PSY/INI/'))

    def test_llamada_en_otra_compania_recibe_secuencia(self):
        call = self.env['cs.family.call'].with_company(self.other_company).create({
            'resident_id': self.resident.id,
            'contacted_name': 'Familiar Test',
        })
        self.assertTrue(call.name.startswith('PSY/FAM/'))
