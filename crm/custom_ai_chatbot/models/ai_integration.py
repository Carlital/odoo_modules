from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import KNeighborsClassifier
from odoo import models, fields, api


class FAQ(models.Model):
    _name = 'crm.faq'
    _description = 'Preguntas Frecuentes'

    question = fields.Text(string="Pregunta", required=True)
    answer = fields.Text(string="Respuesta", required=True)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        self.env['crm.ai'].sudo()._train_model()
        return records

    def write(self, vals):
        res = super().write(vals)
        self.env['crm.ai'].sudo()._train_model()
        return res

    def unlink(self):
        res = super().unlink()
        self.env['crm.ai'].sudo()._train_model()
        return res

class AIKnowledge(models.Model):
    _name = 'crm.ai.knowledge'
    _description = 'Base de Conocimiento IA en CRM'

    question = fields.Text(string="Pregunta", required=True)
    answer = fields.Text(string="Respuesta", required=True)

class AIIntegration(models.Model):
    _name = 'crm.ai'
    _description = 'IA Entrenada con Datos del CRM'

    context_memory = {}  # Contexto por usuario

    def _train_model(self):
        """Entrena la IA con datos del CRM (Preguntas Frecuentes, Productos y Test Drives)."""

        faq_data = self.env['crm.faq'].search([])
        faq_entries = [(faq.question.lower(), faq.answer) for faq in faq_data]

        product_data = self.env['product.template'].search([])
        product_entries = []
        brands = set()
        models = {}
        model_colors = {}
        model_prices = {}

        for p in product_data:
            colors = [color for color in [p.color_1, p.color_2, p.color_3] if color]
            color_prices = {
                p.color_1: p.color_1_price,
                p.color_2: p.color_2_price,
                p.color_3: p.color_3_price
            }

            product_entries.append((
                f"{p.name.lower()} ({', '.join(colors)})",
                f"El modelo {p.name} está disponible en colores: {', '.join(colors)}. "
                f"Precios: {', '.join([f'{color}: ${price}' for color, price in color_prices.items() if color])}. "
                f"Promoción: {p.promotion or 'Sin promoción'}"
            ))

            brands.add(p.categ_id.name)
            models[p.name.lower()] = p.name
            model_colors[p.name.lower()] = colors
            model_prices[p.name.lower()] = color_prices

        all_entries = faq_entries + product_entries
        if not all_entries:
            return None, None, brands, models, model_colors, model_prices

        df = pd.DataFrame(all_entries, columns=['pregunta', 'respuesta'])

        vectorizer = TfidfVectorizer()
        X = vectorizer.fit_transform(df["pregunta"])
        y = df["respuesta"]

        model = KNeighborsClassifier(n_neighbors=1)
        model.fit(X, y)

        return vectorizer, model, brands, models, model_colors, model_prices

    @api.model
    def get_ai_response(self, user_id, user_question):
        """Genera respuestas usando IA basada en la base de datos del CRM y mantiene el contexto."""

        vectorizer, model, brands, models, model_colors, model_prices = self._train_model()
        if not vectorizer or not model:
            return "Lo siento, no tengo suficiente información para responder."

        question_lower = user_question.lower()
        user_context = self.context_memory.get(user_id, {})

        # Identificar modelo o marca en la pregunta y almacenarlo en contexto
        for model_name in models.keys():
            if model_name in question_lower:
                user_context['model'] = models[model_name]
                self.context_memory[user_id] = user_context

        for brand_name in brands:
            if brand_name.lower() in question_lower:
                user_context['brand'] = brand_name
                self.context_memory[user_id] = user_context

        # Pregunta sobre marcas
        if "marcas" in question_lower or "qué marcas" in question_lower:
            return f"Las marcas disponibles son: {', '.join(brands)}."

        # Pregunta sobre modelos de una marca
        if "modelos" in question_lower or "qué modelos" in question_lower:
            brand = user_context.get('brand')
            if brand:
                model_list = [m for m in models.values() if brand in m]
                return f"Los modelos de {brand} disponibles son: {', '.join(model_list)}."
            return f"Los modelos disponibles son: {', '.join(models.values())}."

        # Pregunta sobre colores de un modelo
        if "colores" in question_lower or "qué colores" in question_lower:
            model_name = user_context.get('model')
            if model_name and model_name.lower() in model_colors:
                return f"El modelo {model_name} está disponible en colores: {', '.join(model_colors[model_name.lower()])}."
            return "Cada modelo tiene diferentes colores disponibles. Pregunta por un modelo en específico."

        # Pregunta sobre precios
        if "precio" in question_lower or "cuánto cuesta" in question_lower:
            model_name = user_context.get('model')
            if model_name and model_name.lower() in model_prices:
                return f"Los precios del {model_name} son: {', '.join([f'{c}: ${p}' for c, p in model_prices[model_name.lower()].items() if p])}."
            return "Los precios varían según el modelo y el color. Pregunta por un modelo en específico."

        # Pregunta sobre formas de pago
        if "cómo puedo pagar" in question_lower or "métodos de pago" in question_lower:
            return "Puedes pagar en efectivo, tarjeta de crédito o financiamiento a 24, 36 o 48 meses."

        # Ajustar respuesta de FAQ si es necesario
        input_vec = vectorizer.transform([user_question])
        response = model.predict(input_vec)[0]

        # Si la respuesta es genérica, mejorarla con el contexto
        if "modelo x" in response.lower():
            model_name = user_context.get('model')
            if model_name:
                response = response.replace("modelo X", f"modelo {model_name}")

        return response

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        self.env['crm.ai'].sudo()._train_model()
        return records
    
    def write(self, vals):
        res = super().write(vals)
        self.env['crm.ai'].sudo()._train_model()
        return res

    def unlink(self):
        res = super().unlink()
        self.env['crm.ai'].sudo()._train_model()
        return res


class TestDriveConfiguration(models.Model):
    _inherit = 'test.drive.configuration'

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        self.env['crm.ai'].sudo()._train_model()
        return records
    
    def write(self, vals):
        res = super().write(vals)
        self.env['crm.ai'].sudo()._train_model()
        return res

    def unlink(self):
        res = super().unlink()
        self.env['crm.ai'].sudo()._train_model()
        return res
