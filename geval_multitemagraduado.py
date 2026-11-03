import os
import glob
import time
import pandas as pd
import json
import re
from langchain_ollama import ChatOllama
from deepeval.models import DeepEvalBaseLLM
from deepeval.test_case import LLMTestCase
from deepeval.metrics import BaseMetric
from geval_utils import ejecutar_menu

# 1. Configurar Ollama como motor para DeepEval
class OllamaLocal(DeepEvalBaseLLM):
    def __init__(self, model_name="qwen2.5-coder:3b"):
        self.model = ChatOllama(
            model=model_name,
            temperature=0.0,
            num_ctx=4096 # Vital para no saturar la VRAM
        )

    def load_model(self):
        return self.model

    def generate(self, prompt: str) -> str:
        return self.model.invoke(prompt).content

    async def a_generate(self, prompt: str) -> str:
        res = await self.model.ainvoke(prompt)
        return res.content

    def get_model_name(self):
        return "Ollama Local"

# 2. Definir la Métrica Personalizada (Multitema + Puntaje Graduado)
class SDDClassificationMetric(BaseMetric):
    def __init__(self, model: DeepEvalBaseLLM):
        self.model = model
        self.evaluation_result = [] 
        self.score = 0.0
        self.success = False

    def measure(self, test_case: LLMTestCase):
        prompt = f"""
        Actúa como un juez experto en Ingeniería de Software evaluando herramientas de Spec-Driven Development (SDD) como OpenSpec, Tessl, SpecKit, Kiro y el Método BMAD.
        
        Identifica hasta TRES (3) temáticas predominantes en el documento. Usa EXCLUSIVAMENTE esta taxonomía estricta ordenada por el SDLC:
            - Planning: Epics & Scope / User Stories / Project Roadmaps
            - Analysis: Functional Reqs / Non-Functional Reqs / Use Case Flows
            - Design: System Architecture / Data Modeling / API Contracts & Component Specs
            - Implementation: Code Scaffolding / Algorithms & Logic / UI Layout & Environment
            - Testing & Integration: Unit Tests / Edge Cases / CI-CD Workflows
        
        REGLA CRÍTICA: Ignora el caso de estudio (ej. Tetris, Calculadora, Banco). Concéntrate en la sintaxis y propósito técnico.
        
        Para cada temática identificada, asigna un "puntaje_alineacion" del 1 al 10 basándote estrictamente en esta rúbrica:
        - 9 a 10: Dedicación total. El documento gira casi por completo en torno a esta temática.
        - 7 a 8: Presencia mayoritaria. Secciones extensas y detalladas sobre el tema.
        - 4 a 6: Presencia secundaria. Hay bloques de código o tablas claras, pero comparte protagonismo con otras áreas.
        - 1 a 3: Mención menor. Se toca el tema superficialmente o con un solo bloque pequeño.
        
        DOCUMENTO:
        {test_case.input}
        
        Devuelve ÚNICAMENTE un JSON válido con un arreglo llamado "clasificaciones". Ordena el arreglo de mayor a menor puntaje. No incluyas texto adicional.
        Ejemplo de estructura exacta:
        {{
          "clasificaciones": [
            {{"fase": "Design", "tematica": "API Contracts & Component Specs", "puntaje_alineacion": 9}},
            {{"fase": "Analysis", "tematica": "Functional Reqs", "puntaje_alineacion": 5}}
          ]
        }}
        """
        
        response = self.model.generate(prompt)
        
        try:
            match = re.search(r'\{.*\}', response, re.DOTALL)
            texto_json = match.group(0) if match else response
            parsed = json.loads(texto_json)
            
            clasificaciones = parsed.get("clasificaciones", [])
            # Asegurar que el puntaje sea un entero numérico
            for c in clasificaciones:
                try:
                    c['puntaje_alineacion'] = int(c.get('puntaje_alineacion', 0))
                except ValueError:
                    c['puntaje_alineacion'] = 0
                    
            self.evaluation_result = clasificaciones
            self.score = 1.0 
            self.success = True
        except Exception as e:
            self.evaluation_result = [{"fase": "Error", "tematica": f"Fallo: {str(e)}", "puntaje_alineacion": 0}]
            self.score = 0.0
            self.success = False
            
        return self.score

    def is_successful(self):
        return self.success

    @property
    def name(self):
        return "SDD Lifecycle Scored Classification"

# 3. Ejecutar el Pipeline de Evaluación
def ejecutar_analisis(modelo, tiempo_limite_minutos):
        local_llm = OllamaLocal(model_name=modelo)
        sdd_metric = SDDClassificationMetric(model=local_llm)

        carpetas_herramientas = ["kiro", "speckit", "openspec", "tessl", "bmad method"]
        archivos_markdown = [
            (carpeta, file_path)
            for carpeta in carpetas_herramientas
            for file_path in glob.glob(os.path.join("testing_files", carpeta, "**", "*.md"), recursive=True)
        ]
    
        tiempo_limite_segundos = tiempo_limite_minutos * 60
        inicio_ejecucion = time.monotonic()
        resultados = []

        try:
            for herramienta, file_path in archivos_markdown:
                if time.monotonic() - inicio_ejecucion >= tiempo_limite_segundos:
                    print(f"\nSe alcanzó el límite de {tiempo_limite_minutos:g} minutos. Se guardarán los resultados parciales.")
                    break

                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()[:8000]

                if not content.strip():
                    continue

                test_case = LLMTestCase(input=content, actual_output="N/A")

                print(f"Evaluando {os.path.basename(file_path)}")
                sdd_metric.measure(test_case)
            
                for clasificacion in sdd_metric.evaluation_result:
                    resultados.append({
                        "Archivo": os.path.basename(file_path),
                        "Herramienta": herramienta,
                        "Fase_Predominante": clasificacion.get("fase", "Error"),
                        "Tematica_Predominante": clasificacion.get("tematica", "Error"),
                        "Puntaje_Alineacion": clasificacion.get("puntaje_alineacion", 0)
                    })
                
        except KeyboardInterrupt:
            print("\nEjecución interrumpida manualmente. Se guardarán los resultados acumulados.")
        finally:
            if resultados:
                df = pd.DataFrame(resultados)
            
                # Guardar el registro detallado fila por fila
                nombre_csv_detallado = "resultados_evaluacion_sdd.csv"
                df.to_csv(nombre_csv_detallado, index=False, encoding='utf-8-sig')
            
                # ==========================================
                # ANÁLISIS MASIVO PONDERADO
                # ==========================================
                print("\nGenerando resumen ponderado de temáticas predominantes...")
            
                # Agrupar por herramienta y temática, SUMANDO los puntajes
                resumen = df.groupby(['Herramienta', 'Fase_Predominante', 'Tematica_Predominante'])['Puntaje_Alineacion'].sum().reset_index(name='Puntaje_Total')
            
                # Calcular el peso relativo (porcentaje) dentro de cada herramienta
                total_por_herramienta = resumen.groupby('Herramienta')['Puntaje_Total'].transform('sum')
                resumen['Peso_Relativo_%'] = (resumen['Puntaje_Total'] / total_por_herramienta * 100).round(2)
            
                # Ordenar de mayor a menor peso por herramienta
                resumen = resumen.sort_values(['Herramienta', 'Puntaje_Total'], ascending=[True, False])
            
                nombre_resumen = "resumen_predominancia_ponderada_sdd.csv"
                resumen.to_csv(nombre_resumen, index=False, encoding='utf-8-sig')
            
                print(f"Evaluaciones detalladas guardadas en: {nombre_csv_detallado}")
                print(f"Resumen ponderado guardado en: {nombre_resumen}")
            
                # Imprimir el Top 1 ponderado por herramienta en consola
                print("\n--- TOP TEMÁTICA POR PESO (PONDERADO) ---")
                top_tematicas = resumen.groupby('Herramienta').first().reset_index()
                for _, row in top_tematicas.iterrows():
                    print(f"[{row['Herramienta']}] -> {row['Fase_Predominante']}: {row['Tematica_Predominante']} (Peso: {row['Peso_Relativo_%']}%)")
            else:
                print("\nNo se encontraron evaluaciones para exportar.")


ejecutar_menu(ejecutar_analisis, "ponderado", "resultados_evaluacion_sdd.csv")
