from odoo import http
from odoo.http import request, Response
import json

class AIWebhook(http.Controller):

    @http.route('/ai/webhook', type='json', auth='public', methods=['POST'], csrf=False)
    def ai_webhook(self):
        """Procesa preguntas enviadas por WhatsApp y responde con la IA."""
        try:
            user_question = request.jsonrequest.get('message', '')
            if not user_question:
                return Response(json.dumps({"error": "No se proporcionó mensaje"}), content_type="application/json", status=400)

            ai_model = request.env['crm.ai'].sudo()
            response_text = ai_model.get_ai_response(user_question)

            return Response(json.dumps({"response": response_text}), content_type="application/json", status=200)
        except Exception as e:
            return Response(json.dumps({"error": str(e)}), content_type="application/json", status=500)
