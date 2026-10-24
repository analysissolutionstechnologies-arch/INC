from odoo import http
from odoo.http import request

class MotivoController(http.Controller):
    @http.route('/tickets/filtrar_motivos', type='json', auth='public', website=True)
    def get_motivos_filtrados(self, parent_id=None, equipo_id=None):
        """
        Retorna registros de x_catalogo_motivos filtrados por padre y equipo
        Si parent_id es None, retorna solo los registros padre (categorías)
        """
        try:
            domain = [('x_active', '=', True)]
            if equipo_id:
                domain.append(('x_studio_equipo', '=', int(equipo_id)))
            if parent_id:
                domain.append(('x_studio_motivo_padre', '=', int(parent_id)))
            else:
                domain.append(('x_studio_motivo_padre', '=', False))
            motivos = request.env['x_catalogo_motivos'].sudo().search_read(
                domain,
                ['id', 'x_name']
            )
            return motivos
        except Exception as e:
            return {'error': str(e)}