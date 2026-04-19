import json
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from collections import Counter
from dotenv import load_dotenv
from groq import Groq
from utils_report import generate_pdf_report

# Cargar variables de entorno desde el archivo .env
load_dotenv()

class AuditorInstagram:
    """
    Clase para realizar auditorias forenses digitales en perfiles de Instagram
    utilizando la Ley de Benford sobre la distribucion de los primeros digitos.
    """
    def __init__(self, archivo_json):
        """
        Inicializa el auditor cargando los datos desde un archivo JSON.
        
        Args:
            archivo_json (str): Ruta al archivo JSON con los datos de Instagram.
        """
        try:
            with open(archivo_json, 'r', encoding='utf-8') as f:
                self.df = pd.DataFrame(json.load(f))
        except FileNotFoundError:
            print(f"Error: No se encontro el archivo {archivo_json}")
            exit()

        # Inicializacion del cliente de IA Groq
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        # Calculo de la distribucion teorica segun la Ley de Benford
        self.benford_teorico = {d: np.log10(1 + 1/d) * 100 for d in range(1, 10)}
        self.umbral_minimo = 40 

    def obtener_distribucion(self, serie):
        """
        Calcula la frecuencia del primer digito y la metrica MAD (Mean Absolute Deviation).
        
        Args:
            serie (pd.Series): Serie de datos numericos (likes o views).
            
        Returns:
            tuple: (Distribucion real, total de muestras, valor MAD)
        """
        datos = serie.dropna()
        datos = datos[datos > 0].astype(int)
        total_muestras = len(datos)
        
        if total_muestras < 1:
            return None, 0, 0

        primeros_digitos = datos.apply(lambda x: int(str(x)[0]))
        conteo = Counter(primeros_digitos)
        
        dist_real = {d: (conteo.get(d, 0) / total_muestras) * 100 for d in range(1, 10)}
        
        # Calculo de la desviacion absoluta media respecto a Benford
        sumatoria_error = sum(abs(dist_real[d] - self.benford_teorico[d]) for d in range(1, 10))
        mad = sumatoria_error / 9

        return dist_real, total_muestras, mad

    def graficar_dashboards(self, res_likes, res_views, save_path="benford_plot.png"):
        """
        Genera visualizaciones de la distribucion de Benford y las guarda como imagen.
        
        Args:
            res_likes (dict): Resultados procesados de likes.
            res_views (dict): Resultados procesados de views.
            save_path (str): Ruta donde se guardara el grafico generado.
        """
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
                ax.legend()
            else:
                ax.text(0.5, 0.5, f'Datos insuficientes\n({n}/{self.umbral_minimo})', ha='center', va='center')

        dibujar_metrica(axes[0], res_likes['dist'], res_likes['n'], "Distribucion de Likes", '#3498DB')
        dibujar_metrica(axes[1], res_views['dist'], res_views['n'], "Distribucion de Views", '#27AE60')

        plt.tight_layout()
        plt.savefig(save_path)
        print(f"Grafico guardado en: {save_path}")
        plt.close()

    def pedir_veredicto_groq(self, prompt):
        """
        Envia un prompt a la API de Groq para obtener un analisis experto.
        
        Args:
            prompt (str): Texto con los datos y reglas para la IA.
            
        Returns:
            str: Respuesta generada por el modelo.
        """
        try:
            completion = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            return completion.choices[0].message.content
        except Exception as e:
            return f"Error en API Groq: {e}"

    def ejecutar_auditoria(self, user_name="Usuario"):
        """
        Orquesta el proceso completo de auditoria Benford.
        
        Args:
            user_name (str): Nombre del perfil analizado para el reporte.
        """
        print(f"Iniciando procesamiento de auditoria Benford para {user_name}...")
        
        dist_l, n_l, mad_l = self.obtener_distribucion(self.df['likes'])
        reels_data = self.df[self.df['type'] == 'reel']
        dist_v, n_v, mad_v = self.obtener_distribucion(reels_data['views'])

        # 1. Generar Imagen
        plot_path = "benford_plot.png"
        self.graficar_dashboards({'dist': dist_l, 'n': n_l}, {'dist': dist_v, 'n': n_v}, plot_path)

        # 2. Consultar IA
        if n_l >= 10:
            print("Consultando a Groq para diagnostico final...")
            resumen_ia = {
                "likes": {"mad": round(mad_l, 4), "n": n_l, "dist": dist_l},
                "views": {"mad": round(mad_v, 4), "n": n_v, "dist": dist_v}
            }
            
            prompt_auditoria = f"""
            Analiza estos datos de Instagram del usuario {user_name} usando la Ley de Benford y el Mean Absolute Deviation (MAD).
            
            DATOS OBTENIDOS:
            {json.dumps(resumen_ia, indent=2)}

            REGLAS DE INTERPRETACION MAD:
            - MAD < 0.6 -> Comportamiento NATURAL.
            - MAD 0.6-1.2 -> Leve desviacion.
            - MAD 1.2-2.0 -> SOSPECHOSO.
            - MAD > 2.0 -> PROBABLE MANIPULACION.

            TAREAS:
            1. Analiza likes y views por separado basandote en su MAD.
            2. Identifica inconsistencias.
            3. Determina indicios de bots.
            4. Veredicto final: RIESGO BAJO, MEDIO o ALTO.
            """
            
            veredicto = self.pedir_veredicto_groq(prompt_auditoria)
            
            # 3. Generar PDF
            pdf_filename = f"Reporte_Benford_{user_name}.pdf"
            generate_pdf_report(
                pdf_filename,
                f"Auditoria Forense Benford: {user_name}",
                plot_path,
                veredicto
            )
        else:
            print("Datos insuficientes para auditoria IA.")

        # Limpieza
        if os.path.exists(plot_path):
            os.remove(plot_path)

if __name__ == "__main__":
    auditor = AuditorInstagram("instagram_data.json")
    auditor.ejecutar_auditoria()
