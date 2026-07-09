import json
import requests
import re
import traceback
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
            print("\n" + "="*50)
            print(f"🚀 INICIANDO MOTOR IA PARA USUARIO ID: {usuario_id}")
            
            usuario = Usuario.objects.get(id=usuario_id)
            
            # --- DEBUG DATOS FÍSICOS ---
            print(f"📊 DATOS CRUDOS BD -> Peso: '{usuario.peso_usuario}' | Altura: '{usuario.altura_usuario}' | Fecha Nac: '{usuario.fecha_nacimiento}'")
            
            edad = self.calcular_edad(usuario.fecha_nacimiento)
            
            # Forzamos conversión a float asegurando que si es None no falle silenciosamente
            altura_str = str(usuario.altura_usuario).strip() if usuario.altura_usuario else "0"
            peso_str = str(usuario.peso_usuario).strip() if usuario.peso_usuario else "0"
            
            altura = float(altura_str)
            peso = float(peso_str)
            
            if altura > 3:  
                altura = altura / 100.0
                
            print(f"📐 DATOS CALCULADOS -> Edad: {edad} | Peso: {peso}kg | Altura: {altura}m")
            
            if altura <= 0 or peso <= 0:
                print("⚠️ ADVERTENCIA: Altura o peso son 0. Calculando IMC como 0.")
                imc = 0.0
                tmb = 2000
            else:
                imc = peso / (altura ** 2)
                tmb = 10 * peso + 6.25 * (altura * 100) - 5 * edad + (5 if usuario.genero_usuario == 'M' else -161)
                print(f"✅ IMC FINAL: {imc:.2f} | Mantenimiento: {int(tmb * 1.3)} kcal")

            prompt = f"""
            Responde ÚNICAMENTE con un JSON válido en ESPAÑOL. Usa EXACTAMENTE estas llaves:
            {{
                "opcion_1": {{
                    "titulo": "Conservadora/Salud",
                    "enfoque_rutina": "FUNCIONAL",
                    "rutina_ejemplo": "Ejemplo breve de rutina",
                    "nutricion_objetivo": "Meta calórica",
                    "macros_sugeridos": "Porcentaje de macros"
                }},
                "opcion_2": {{
                    "titulo": "Agresiva/Hipertrofia",
                    "enfoque_rutina": "FUERZA",
                    "rutina_ejemplo": "Ejemplo breve de rutina",
                    "nutricion_objetivo": "Meta calórica",
                    "macros_sugeridos": "Porcentaje de macros"
                }}
            }}
            """

            print("\n⏳ ENVIANDO PETICIÓN A OLLAMA...")
            response = requests.post(self.ollama_url, json={
                "model": self.modelo,
                "prompt": prompt,
                "format": "json",
                "stream": False,
                "keep_alive": 0,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 400
                }
            }, timeout=45)
            
            respuesta_texto = response.json().get('response', '')
            
            print("\n🤖 RESPUESTA CRUDA DE OLLAMA:")
            print(respuesta_texto)
            print("-" * 50)
            
            match = re.search(r'\{.*\}', respuesta_texto, re.DOTALL)
            if match:
                respuesta_texto = match.group(0)
                
            data = json.loads(respuesta_texto)
            print("\n📦 JSON PARSEADO CORRECTAMENTE:")
            print(json.dumps(data, indent=2))
            
            op1 = data.get("opcion_1", {})
            op2 = data.get("opcion_2", {})
            
            # Extracción a prueba de balas buscando en inglés y español
            return {
                "metricas": {"imc": round(imc, 1), "asistencia_proyectada": 4},
                "opcion_1": {
                    "titulo": op1.get("titulo", op1.get("title", "Conservadora")),
                    "enfoque_rutina": op1.get("enfoque_rutina", op1.get("routine_focus", "FUNCIONAL")),
                    "rutina_ejemplo": op1.get("rutina_ejemplo", op1.get("routine_example", op1.get("routine", "Sin datos"))),
                    "nutricion_objetivo": op1.get("nutricion_objetivo", op1.get("nutrition_goal", op1.get("daily_goal", "Sin datos"))),
                    "macros_sugeridos": op1.get("macros_sugeridos", op1.get("suggested_macros", op1.get("macros", "Sin datos")))
                },
                "opcion_2": {
                    "titulo": op2.get("titulo", op2.get("title", "Hipertrofia")),
                    "enfoque_rutina": op2.get("enfoque_rutina", op2.get("routine_focus", "FUERZA")),
                    "rutina_ejemplo": op2.get("rutina_ejemplo", op2.get("routine_example", op2.get("routine", "Sin datos"))),
                    "nutricion_objetivo": op2.get("nutricion_objetivo", op2.get("nutrition_goal", op2.get("daily_goal", "Sin datos"))),
                    "macros_sugeridos": op2.get("macros_sugeridos", op2.get("suggested_macros", op2.get("macros", "Sin datos")))
                },
                "disclaimer": "⚠️ Las imágenes y calorías son referenciales. Consulta a un profesional."
            }
            
        except Exception as e:
            print(f"\n❌ ERROR CRÍTICO EN IA: {e}")
            traceback.print_exc() # Imprime la línea exacta del error en consola
            return self._plan_respaldo(imc)

    def _plan_respaldo(self, imc):
        return {
            "metricas": {"imc": round(imc, 1), "asistencia_proyectada": 4},
            "opcion_1": {
                "titulo": "Conservadora/Salud (Respaldo)",
                "enfoque_rutina": "FUNCIONAL",
                "rutina_ejemplo": "Entrenamiento Full Body. 3 series de 12 repeticiones.",
                "nutricion_objetivo": "Dieta Normocalórica.",
                "macros_sugeridos": "50% Carbs | 30% Prot | 20% Grasas"
            },
            "opcion_2": {
                "titulo": "Hipertrofia (Respaldo)",
                "enfoque_rutina": "FUERZA",
                "rutina_ejemplo": "División Push/Pull/Legs. 4 series de 8 reps.",
                "nutricion_objetivo": "Superávit Calórico.",
                "macros_sugeridos": "40% Carbs | 40% Prot | 20% Grasas"
            },
            "disclaimer": "⚠️ Mostrando plan de respaldo."
        }