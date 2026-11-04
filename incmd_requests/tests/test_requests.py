from odoo.tests import TransactionCase, tagged
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo import Command


@tagged('post_install', '-at_install')
class TestRequests(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.admin = cls.env.ref('base.user_admin')
        cls.company = cls.env.company
        U = cls.env['res.users'].with_user(cls.admin)
        def user(name, role='user'):
            return U.create({'name':name,'login':'incmd_test_'+name,
                'company_id':cls.company.id,'company_ids':[Command.set([cls.company.id])],
                'group_ids':[Command.set([cls.env.ref('base.group_user').id,cls.env.ref('incmd_requests.group_'+role).id])]})
        cls.owner = user('owner')
        cls.other = user('other')
        cls.agent = user('agent')
        cls.supervisor = user('supervisor','supervisor')
        units = cls.env['incmd.request.unit'].with_user(cls.admin)
        cls.store = units.create({'name':'Tienda A','kind':'store','receives':False,
            'supervisor_ids':[Command.set(cls.supervisor.ids)]})
        cls.store_b = units.create({'name':'Tienda B','kind':'store','receives':False})
        cls.area = units.create({'name':'Sistemas','member_ids':[Command.set(cls.agent.ids)]})
        for usr,unit in [(cls.owner,cls.store),(cls.other,cls.store_b),(cls.agent,cls.area),(cls.supervisor,cls.area),(cls.admin,cls.area)]:
            cls.env['incmd.request.assignment'].with_user(cls.admin).create({'user_id':usr.id,'unit_id':unit.id})
        cls.process = cls.env['incmd.request.process'].with_user(cls.admin).create({'name':'Reparación','unit_id':cls.area.id})
        S = cls.env['incmd.request.stage'].with_user(cls.admin)
        cls.new = S.create({'name':'Nueva','process_id':cls.process.id,'is_initial':True})
        cls.done = S.create({'name':'Resuelta','process_id':cls.process.id,'is_closed':True})
        cls.transition = cls.env['incmd.request.transition'].with_user(cls.admin).create({
            'name':'Resolver','process_id':cls.process.id,'from_stage_id':cls.new.id,'to_stage_id':cls.done.id})
        cls.process.action_publish()
        cls.reason = cls.env['incmd.request.reason'].with_user(cls.admin).create({
            'name':'Falla de equipo','unit_id':cls.area.id,'process_id':cls.process.id})

    def request(self, user=None):
        return self.env['incmd.request'].with_user(user or self.owner).create({
            'name':'Equipo no enciende','description':'Revisar equipo en caja.',
            'unit_id':self.area.id,'reason_id':self.reason.id})

    def test_supervisor_visibility_by_origin(self):
        a = self.request()
        b = self.request(self.other)
        a.action_submit(); b.action_submit()
        visible = self.env['incmd.request'].with_user(self.supervisor).search([])
        self.assertIn(a.id,visible.ids)
        self.assertNotIn(b.id,visible.ids)
        with self.assertRaises(AccessError):
            b.with_user(self.supervisor).read(['description'])

    def test_drafts_private_even_to_supervisor(self):
        r = self.request()
        self.assertNotIn(r.id,self.env['incmd.request'].with_user(self.supervisor).search([]).ids)
        self.assertNotIn(r.id,self.env['incmd.request'].with_user(self.agent).search([]).ids)

    def test_frozen_original_even_admin(self):
        r = self.request(); r.action_submit()
        for user in [self.owner,self.admin,self.agent]:
            with self.assertRaises(UserError):
                r.with_user(user).write({'description':'Modificada'})
        with self.assertRaises(AccessError): r.with_user(self.admin).unlink()

    def test_control_fields_cannot_be_forged(self):
        r = self.request()
        with self.assertRaises(AccessError): r.write({'stage_id':self.done.id})
        with self.assertRaises(AccessError): r.write({'origin_id':self.store_b.id})
        with self.assertRaises(AccessError):
            self.env['incmd.request'].with_user(self.owner).create({'name':'A','description':'B',
                'unit_id':self.area.id,'reason_id':self.reason.id,'state':'done'})

    def test_user_cannot_configure_or_escalate(self):
        with self.assertRaises(AccessError): self.area.with_user(self.owner).write({'name':'Otra'})
        with self.assertRaises(AccessError):
            self.env['incmd.request.assignment'].with_user(self.owner).create({'user_id':self.other.id,'unit_id':self.store.id,'role':'admin'})

    def test_only_authorized_actor_changes_stage(self):
        r = self.request(); r.action_submit()
        wiz = self.env['incmd.request.action'].with_user(self.owner).create({
            'request_id':r.id,'comment':'Intento','transition_id':self.transition.id})
        with self.assertRaises(AccessError): wiz.action_apply()
        wiz = self.env['incmd.request.action'].with_user(self.agent).create({
            'request_id':r.id,'comment':'Equipo reparado','transition_id':self.transition.id})
        wiz.action_apply()
        self.assertEqual(r.state,'done')
        self.assertTrue(r.closed_at)
        self.assertEqual(len(r.history_ids),2)

    def test_published_process_is_immutable(self):
        with self.assertRaises(UserError): self.new.write({'name':'Otra'})
        with self.assertRaises(UserError): self.transition.write({'name':'Otra'})
        with self.assertRaises(UserError): self.process.write({'name':'Otro'})
        with self.assertRaises(UserError): self.process.unlink()

    def test_version_remaps_stages_and_existing_requests_stay(self):
        r = self.request(); r.action_submit()
        result = self.process.action_new_version()
        new = self.env['incmd.request.process'].browse(result['res_id'])
        self.assertEqual(new.version,2)
        self.assertEqual(new.state,'draft')
        self.assertFalse(new.stage_ids & self.process.stage_ids)
        self.assertTrue(all(t.from_stage_id in new.stage_ids and t.to_stage_id in new.stage_ids for t in new.transition_ids))
        self.assertEqual(r.process_id,self.process)

    def test_original_attachment_cannot_be_replaced_or_deleted(self):
        r = self.request()
        a = self.env['ir.attachment'].with_user(self.owner).create({'name':'prueba.txt','datas':'SG9sYQ==','res_model':r._name,'res_id':r.id})
        r.write({'original_attachment_ids':[Command.set(a.ids)]})
        r.action_submit()
        with self.assertRaises(AccessError): a.with_user(self.admin).write({'datas':'Q2FtYmlv'})
        with self.assertRaises(AccessError): a.with_user(self.admin).unlink()

    def test_followup_appends_without_changing_original(self):
        r = self.request(); r.action_submit()
        w = self.env['incmd.request.action'].with_user(self.owner).create({'request_id':r.id,'comment':'Aclaración adicional'})
        w.action_apply()
        self.assertEqual(r.description,'Revisar equipo en caja.')
        self.assertEqual(r.stage_id,self.new)
        self.assertEqual(len(r.history_ids),2)
        with self.assertRaises(AccessError): r.history_ids.with_user(self.admin).write({'comment':'Cambio'})

    def test_unassigned_user_cannot_submit_request(self):
        self.env['incmd.request.assignment'].with_user(self.admin).search([('user_id','=',self.other.id)]).unlink()
        with self.assertRaises(UserError): self.request(self.other)

    def test_admin_can_assign_module_role(self):
        a = self.env['incmd.request.assignment'].with_user(self.admin).search([('user_id','=',self.other.id)])
        a.write({'role':'supervisor'})
        self.assertTrue(self.other.has_group('incmd_requests.group_supervisor'))
        self.assertFalse(self.other.has_group('base.group_system'))

    def test_employee_origin_from_department_and_store(self):
        self.env['incmd.request.assignment'].with_user(self.admin).search([('user_id','=',self.other.id)]).unlink()
        department = self.env['hr.department'].sudo().create({'name':'Departamento de prueba','company_id':self.company.id})
        self.store_b.with_user(self.admin).write({'department_id':department.id})
        employee = self.env['hr.employee'].sudo().create({'name':'Empleado de prueba','user_id':self.other.id,
            'company_id':self.company.id,'department_id':department.id})
        model = self.env['incmd.request'].with_user(self.other)
        self.assertEqual(model._default_origin(),self.store_b)
        employee.write({'request_unit_id':self.store.id})
        self.assertEqual(model._default_origin(),self.store)
        r = self.request(self.other); r.action_submit()
        employee.write({'request_unit_id':self.store_b.id})
        self.assertEqual(r.origin_id,self.store)

    def redirect_target(self):
        area = self.env['incmd.request.unit'].with_user(self.admin).create({
            'name':'Mantenimiento','member_ids':[Command.set(self.other.ids)]})
        process = self.env['incmd.request.process'].with_user(self.admin).create({'name':'Atención mantenimiento','unit_id':area.id})
        S = self.env['incmd.request.stage'].with_user(self.admin)
        initial = S.create({'name':'Recibida','process_id':process.id,'is_initial':True})
        final = S.create({'name':'Terminada','process_id':process.id,'is_closed':True})
        self.env['incmd.request.transition'].with_user(self.admin).create({
            'name':'Terminar','process_id':process.id,'from_stage_id':initial.id,'to_stage_id':final.id})
        process.action_publish()
        reason = self.env['incmd.request.reason'].with_user(self.admin).create({'name':'Reparación local','unit_id':area.id,'process_id':process.id})
        return area,reason,initial

    def test_redirect_preserves_original_and_changes_access(self):
        area,reason,initial = self.redirect_target()
        r = self.request(); r.action_submit()
        number = r.number
        r.with_user(self.agent)._apply_redirect(reason,'Corresponde a mantenimiento',self.other)
        r = r.with_user(self.admin)
        self.assertEqual(r.number,number)
        self.assertEqual(r.original_unit_id,self.area)
        self.assertEqual(r.original_reason_id,self.reason)
        self.assertEqual(r.unit_id,area)
        self.assertEqual(r.stage_id,initial)
        self.assertEqual(r.responsible_id,self.other)
        self.assertEqual(r.name,'Equipo no enciende')
        self.assertEqual(r.history_ids[0].action,'Solicitud redirigida')
        self.assertEqual(r.history_ids[0].user_id,self.agent)
        self.assertIn(r.id,self.env['incmd.request'].with_user(self.other).search([]).ids)
        self.assertNotIn(r.id,self.env['incmd.request'].with_user(self.agent).search([]).ids)
        self.assertIn(r.id,self.env['incmd.request'].with_user(self.supervisor).search([]).ids)

    def test_redirect_requires_handler_and_justification(self):
        area,reason,initial = self.redirect_target()
        r = self.request(); r.action_submit()
        with self.assertRaises(AccessError): r.with_user(self.owner)._apply_redirect(reason,'Traslado',self.other)
        with self.assertRaises(UserError): r.with_user(self.agent)._apply_redirect(reason,'  ',self.other)
        with self.assertRaises(ValidationError): r.with_user(self.agent)._apply_redirect(reason,'Traslado',self.agent)
        self.assertEqual(r.unit_id,self.area)

    def test_redirect_rejects_closed_and_direct_writes(self):
        area,reason,initial = self.redirect_target()
        r = self.request(); r.action_submit()
        with self.assertRaises(UserError): r.with_user(self.admin).write({'unit_id':area.id,'reason_id':reason.id})
        with self.assertRaises(AccessError): r.with_user(self.admin).write({'original_unit_id':area.id})
        r.with_user(self.agent)._apply_followup(self.transition,'Resuelta',self.env['ir.attachment'],self.env['res.users'])
        with self.assertRaises(AccessError): r.with_user(self.admin)._apply_redirect(reason,'Traslado',self.other)

    def test_audit_note_contains_stage_and_assignment(self):
        r = self.request(); r.action_submit()
        r.with_user(self.agent)._apply_followup(self.env['incmd.request.transition'],'Asignación',self.env['ir.attachment'],self.agent)
        event = r.with_user(self.admin).history_ids[0]
        self.assertIn('Responsable:',event.comment)
        self.assertEqual(event.message_id.subtype_id,self.env.ref('mail.mt_note'))
        self.assertIn('Nueva',str(event.message_id.body))
