import json
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from collections import Counter
from dotenv import load_dotenv
from groq import Groq

# Cargar variables de entorno
load_dotenv()

class AuditorInstagram:
    def __init__(self, archivo_json):
        try:
            with open(archivo_json, 'r', encoding='utf-8') as f:
                self.df = pd.DataFrame(json.load(f))
        except FileNotFoundError:
            print(f"❌ Error: No se encontró el archivo {archivo_json}")
            exit()

        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.benford_teorico = {d: np.log10(1 + 1/d) * 100 for d in range(1, 10)}
        self.umbral_minimo = 40 

    def obtener_distribucion(self, serie):
        """Calcula frecuencia de primer dígito y métrica MAD."""
        datos = serie.dropna()
        datos = datos[datos > 0].astype(int)
        total_muestras = len(datos)
        
        if total_muestras < 1:
            return None, 0, 0

        primeros_digitos = datos.apply(lambda x: int(str(x)[0]))
        conteo = Counter(primeros_digitos)
        
        # Distribución Real
        dist_real = {d: (conteo.get(d, 0) / total_muestras) * 100 for d in range(1, 10)}
        
        # CÁLCULO DEL MAD (Mean Absolute Deviation)
        sumatoria_error = sum(abs(dist_real[d] - self.benford_teorico[d]) for d in range(1, 10))
        mad = sumatoria_error / 9

        return dist_real, total_muestras, mad

    def graficar_dashboards(self, res_likes, res_views):
        """Genera visualizaciones. Se quitó emojis para evitar errores de fuente."""
        plt.style.use('ggplot')
        fig, axes = plt.subplots(1, 2, figsize=(15, 7))
        fig.suptitle('Auditoria Forense Digital: Ley de Benford', 
                     fontsize=18, fontweight='bold', color='#2C3E50')

        def dibujar_metrica(ax, dist, n, titulo, color_principal):
            if dist:
                x = list(dist.keys())
                y = list(dist.values())
                y_benf = [self.benford_teorico[d] for d in x]

                bars = ax.bar(x, y, color=color_principal, alpha=0.6, edgecolor='black')
                ax.plot(x, y_benf, color='#E74C3C', marker='s', markersize=8, linewidth=2, label='Benford Ideal')

                for bar in bars:
                    h = bar.get_height()
                    ax.annotate(f'{h:.1f}%', xy=(bar.get_x() + bar.get_width()/2, h),
                                xytext=(0, 5), textcoords="offset points", ha='center', fontsize=9, fontweight='bold')

                ax.set_title(titulo, fontsize=14, fontweight='bold')
                ax.set_xticks(range(1, 10))
                ax.set_ylim(0, max(max(y), 45))
                ax.legend()
            else:
                ax.text(0.5, 0.5, f'Datos insuficientes\n({n}/{self.umbral_minimo})', ha='center', va='center')

        dibujar_metrica(axes[0], res_likes['dist'], res_likes['n'], "Distribucion de Likes", '#3498DB')
        dibujar_metrica(axes[1], res_views['dist'], res_views['n'], "Distribucion de Views", '#27AE60')

        plt.tight_layout()
        # block=False permite que el script siga corriendo mientras el gráfico está abierto
        plt.show(block=False)
        print("📊 Gráfico generado. (No es necesario cerrarlo para ver el análisis de la IA)")

    def pedir_veredicto_groq(self, prompt):
        """Conexión centralizada con Groq."""
        try:
            completion = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            return completion.choices[0].message.content
        except Exception as e:
            return f"Error en API Groq: {e}"

    def ejecutar_auditoria(self):
        print("🚀 Iniciando procesamiento...")
        
        # 1. Procesar Datos
        dist_l, n_l, mad_l = self.obtener_distribucion(self.df['likes'])
        reels_data = self.df[self.df['type'] == 'reel']
        dist_v, n_v, mad_v = self.obtener_distribucion(reels_data['views'])

        # 2. Mostrar Dashboard
        self.graficar_dashboards({'dist': dist_l, 'n': n_l}, {'dist': dist_v, 'n': n_v})

        # 3. Preparar Reporte MAD
        resumen_ia = {
            "likes": {"mad": round(mad_l, 4), "n": n_l, "dist": dist_l},
            "views": {"mad": round(mad_v, 4), "n": n_v, "dist": dist_v}
        }

        # 4. Consultar IA
        if n_l >= 10: # Umbral mínimo técnico para que la IA tenga qué leer
            print("🤖 Consultando a Groq con métricas MAD...")
            
            prompt_auditoria = f"""
            Analiza estos datos de Instagram usando la Ley de Benford y el Mean Absolute Deviation (MAD).
            
            DATOS OBTENIDOS:
            {json.dumps(resumen_ia, indent=2)}

            REGLAS DE INTERPRETACIÓN MAD:
            - MAD < 0.6 → Comportamiento NATURAL.
            - MAD 0.6–1.2 → Leve desviación.
            - MAD 1.2–2.0 → SOSPECHOSO.
            - MAD > 2.0 → PROBABLE MANIPULACIÓN.

            TAREAS:
            1. Analiza likes y views por separado basándote en su MAD.
            2. Identifica inconsistencias (ej: Views naturales pero Likes manipulados).
            3. Determina indicios de bots.
            4. Veredicto final: RIESGO BAJO, MEDIO o ALTO.
            
            Sé técnico pero claro.
            """
            
            veredicto = self.pedir_veredicto_groq(prompt_auditoria)
            print("\n" + "="*60)
            print("📜 INFORME DE AUDITORÍA FORENSE (MAD)")
            print("="*60)
            print(veredicto)
            print("="*60)
            
            # Mantener el gráfico abierto al final del script
            print("\nCierra la ventana del gráfico para terminar el programa.")
            plt.show() 
        else:
            print("⚠️ Datos insuficientes para auditoría IA.")

if __name__ == "__main__":
    auditor = AuditorInstagram("instagram_data.json")
    auditor.ejecutar_auditoria()