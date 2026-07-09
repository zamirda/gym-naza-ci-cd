import json
import requests
import re
from datetime import date, datetime
from gimnasio.models import Usuario

class MotorRecomendacionGym:
    def __init__(self):
        self.ollama_url = "http://localhost:11434/api/generate"
        self.modelo = "llama3"

    def calcular_edad(self, fecha_nacimiento):
        if isinstance(fecha_nacimiento, str):
            try:
                fecha_nacimiento = datetime.strptime(fecha_nacimiento, "%Y-%m-%d").date()
            except ValueError:
                return 30
        hoy = date.today()
        return hoy.year - fecha_nacimiento.year - ((hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day))

    def generar_recomendaciones(self, usuario_id):
        imc = 0.0 
        try:
            print(f"\n EJECUTANDO IA {usuario_id} EN GPU...")
            usuario = Usuario.objects.get(id=usuario_id)
            edad = self.calcular_edad(usuario.fecha_nacimiento)
            
            # Altura (cm a 2.00 m)
            altura = float(usuario.altura_usuario)
            if altura > 3:  
                altura = altura / 100.0
                
            peso = float(usuario.peso_usuario)
            
            if altura <= 0 or peso <= 0:
                imc = 0.0
                tmb = 2000
            else:
                imc = peso / (altura ** 2)
                tmb = 10 * peso + 6.25 * (altura * 100) - 5 * edad + (5 if usuario.genero_usuario == 'M' else -161)

            prompt = f"""
            Eres un entrenador personal de inteligencia artificial de élite.
            Genera 2 opciones de planes de entrenamiento y nutrición ÚNICAS Y DIFERENTES cada vez que se te consulte, adaptadas estrictamente a estos datos del cliente:
            - Edad: {edad} años
            - IMC: {imc:.1f}
            - Peso: {peso} kg
            - Calorías de Mantenimiento (aprox): {int(tmb * 1.3)} kcal

            Responde ÚNICAMENTE con un objeto JSON válido que cumpla esta estructura exacta (sin texto fuera del JSON):
            {{
                "opcion_1": {{
                    "titulo": "Inventa un título creativo (ej. Salud Activa)",
                    "enfoque_rutina": "FUNCIONAL",
                    "rutina_ejemplo": "Describe una rutina única",
                    "nutricion_objetivo": "Meta calórica",
                    "macros_sugeridos": "Porcentajes C/P/G"
                }},
                "opcion_2": {{
                    "titulo": "Inventa un título creativo (ej. Fuerza Bruta)",
                    "enfoque_rutina": "FUERZA",
                    "rutina_ejemplo": "Describe una rutina pesada/hipertrofia",
                    "nutricion_objetivo": "Meta calórica de superávit",
                    "macros_sugeridos": "Porcentajes C/P/G diferentes"
                }}
            }}
            """

            # ======  RENDIMIENTO Y GPU ======
            response = requests.post(self.ollama_url, json={
                "model": self.modelo,
                "prompt": prompt,
                "format": "json",
                "stream": False,
        
                "keep_alive": "15m", 
                "options": {
                    "temperature": 0.8,
                    "num_predict": 400,
                    "num_gpu": 99 
                }
            }, timeout=60) 
            
            respuesta_texto = response.json().get('response', '')
            
            match = re.search(r'\{.*\}', respuesta_texto, re.DOTALL)
            if match:
                respuesta_texto = match.group(0)
                
            data = json.loads(respuesta_texto)
            
            # MAPEO ESTRICTO
            op1 = data.get("opcion_1", {})
            op2 = data.get("opcion_2", {})
            
            return {
                "metricas": {"imc": round(imc, 1), "asistencia_proyectada": 4},
                "opcion_1": {
                    "titulo": op1.get("titulo", op1.get("title", "Conservadora/Salud")),
                    "enfoque_rutina": op1.get("enfoque_rutina", op1.get("enfoque", "FUNCIONAL")),
                    "rutina_ejemplo": op1.get("rutina_ejemplo", op1.get("rutina", "Circuito cuerpo completo.")),
                    "nutricion_objetivo": op1.get("nutricion_objetivo", op1.get("meta_diaria", "Dieta base.")),
                    "macros_sugeridos": op1.get("macros_sugeridos", op1.get("macros", "50% C, 30% P, 20% G"))
                },
                "opcion_2": {
                    "titulo": op2.get("titulo", op2.get("title", "Agresiva/Hipertrofia")),
                    "enfoque_rutina": op2.get("enfoque_rutina", op2.get("enfoque", "FUERZA")),
                    "rutina_ejemplo": op2.get("rutina_ejemplo", op2.get("rutina", "Rutina pesada 4x10.")),
                    "nutricion_objetivo": op2.get("nutricion_objetivo", op2.get("meta_diaria", "Superávit.")),
                    "macros_sugeridos": op2.get("macros_sugeridos", op2.get("macros", "40% C, 40% P, 20% G"))
                },
                "Advertencia": " Las imágenes y calorías son referenciales. Consulta a un profesional."
            }
            
        except Exception as e:
            print(f"Alerta IA: {e} - Retornando plan de respaldo.")
            return self._plan_respaldo(imc)

    def _plan_respaldo(self, imc):
        return {
            "metricas": {"imc": round(imc, 1), "asistencia_proyectada": 4},
            "opcion_1": {
                "titulo": "Salud Integral (Respaldo)",
                "enfoque_rutina": "FUNCIONAL",
                "rutina_ejemplo": "Entrenamiento Full Body (Cuerpo Completo). 3 series de 12 a 15 repeticiones por grupo.",
                "nutricion_objetivo": "Dieta Normocalórica (Mantenimiento de peso actual).",
                "macros_sugeridos": "50% Carbohidratos | 30% Proteínas | 20% Grasas"
            },
            "opcion_2": {
                "titulo": "Hipertrofia Clásica (Respaldo)",
                "enfoque_rutina": "FUERZA",
                "rutina_ejemplo": "División Push/Pull/Legs (Empuje, Tirón, Pierna). 4 series de 8 a 10 repeticiones pesadas.",
                "nutricion_objetivo": "Superávit Calórico (+300 a 500 kcal para ganancia muscular).",
                "macros_sugeridos": "40% Carbohidratos | 40% Proteínas | 20% Grasas"
            },
            "Advertencia": " Mostrando plan de respaldo. (El motor IA tardó en procesar)."
        }