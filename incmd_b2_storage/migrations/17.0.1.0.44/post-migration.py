from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    # One-time replay: remote objects remain excluded by the batch domain.
    rules = env['incmd.b2.rule'].with_context(active_test=False).search([])
    rules.write({'allow_extensionless': True, 'cursor_id': 0})
    # Correct the known MP3 alias without changing the user's other filters.
    for rule in rules:
        tokens = [t.strip() for t in (rule.mime_types or '').split(',')]
        if 'video/mp3' in tokens:
            rule.mime_types = ','.join(dict.fromkeys('audio/mpeg' if t == 'video/mp3' else t for t in tokens))
