import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from dotenv import load_dotenv
from groq import Groq
import os
from utils_report import generate_pdf_report

# Cargar variables de entorno
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

class AnalizadorEngagementPro:
    def __init__(self, archivo_json):
        if not os.path.exists(archivo_json):
            print(f"❌ Error: El archivo {archivo_json} no existe.")
            exit()
            
        with open(archivo_json, 'r', encoding='utf-8') as f:
            self.df = pd.DataFrame(json.load(f))
        
        # Limpieza de datos
        self.df['likes'] = pd.to_numeric(self.df['likes'], errors='coerce').fillna(0)
        self.df['comments'] = pd.to_numeric(self.df['comments'], errors='coerce').fillna(0)
        
        # Filtramos posts sin interacciones para no falsear ratios
        self.df = self.df[self.df['likes'] > 0].copy()
        
        # Cálculo del ratio individual por post
        self.df['ratio'] = (self.df['comments'] / self.df['likes']) * 100

    def detectar_outliers(self):
        """Detecta puntos anomalos usando Z-Score sobre el ratio de engagement."""
        mean_ratio = self.df['ratio'].mean()
        std_ratio = self.df['ratio'].std()
        
        if std_ratio == 0:
            self.df['z_score'] = 0
        else:
            self.df['z_score'] = (self.df['ratio'] - mean_ratio) / std_ratio
            
        return self.df[np.abs(self.df['z_score']) > 2].copy()

    def graficar_resultados(self, mediana, corr, outliers, save_path="engagement_plot.png"):
        """Genera el Scatter Plot y lo guarda como imagen."""
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(12, 7))
        
        sns.scatterplot(data=self.df, x='likes', y='comments', 
                        alpha=0.5, s=80, color='#00d4ff', label='Posts Normales', ax=ax)
        
        sns.regplot(data=self.df, x='likes', y='comments', scatter=False, 
                    color='#ff0055', line_kws={'linewidth': 2, 'label': 'Tendencia de Cuenta'}, ax=ax)

        if not outliers.empty:
            sns.scatterplot(data=outliers, x='likes', y='comments', 
                            color='#ff4444', s=150, marker='X', label='ANOMALÍAS (Outliers)', ax=ax)

        ax.set_title(f'Auditoría de Coherencia: Likes vs Comentarios\nPearson Correlation: {corr:.2f}', 
                     fontsize=15, fontweight='bold', pad=20)
        
        textstr = '\n'.join((
            f'Ratio Mediano: {mediana:.2f}%',
            f'Posts Analizados: {len(self.df)}',
            f'Outliers: {len(outliers)}',
            f'Coef. Pearson: {corr:.2f}'
        ))
        props = dict(boxstyle='round', facecolor='black', alpha=0.8, edgecolor='#ff0055')
        ax.text(0.05, 0.95, textstr, transform=ax.transAxes, fontsize=11,
                verticalalignment='top', bbox=props)

        plt.tight_layout()
        plt.savefig(save_path)
        print(f"📉 Gráfico guardado en: {save_path}")
        plt.close()

    def generar_veredicto_ia(self, ratio_mean, ratio_med, std, corr, outliers):
        """Prompt optimizado para diagnóstico forense."""
        prompt = f"""
        Eres un analista forense de redes sociales especializado en detección de fraude.
        
        DATOS DE LA CUENTA:
        - Ratio Promedio: {ratio_mean:.2f}%
        - Ratio Mediano: {ratio_med:.2f}%
        - Desviación Estándar (Dispersión): {std:.2f}
        - Correlación de Pearson: {corr:.2f}
        - Outliers detectados: {len(outliers)} de {len(self.df)} posts

        REGLAS TÉCNICAS DE INTERPRETACIÓN:
        1. Ratio normal: 0.5% – 3%.
        2. Ratio < 0.1% → Fuertes indicios de compra de likes.
        3. Alta desviación estándar (>1.5 sobre la media) → Comportamiento inestable/errático.
        4. Correlación < 0.4 → Los likes y comentarios no crecen juntos (Interacción Artificial).
        5. Muchos outliers → Manipulación quirúrgica de publicaciones específicas.

        TAREAS:
        - Evalúa la coherencia del engagement (Mediana vs Media).
        - Identifica anomalías específicas en el comportamiento de la cuenta.
        - Clasifica el riesgo de fraude: BAJO, MEDIO o ALTO.
        - Da un veredicto técnico basado en los resultados.
        """
        
        try:
            resp = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1 
            )
            return resp.choices[0].message.content
        except Exception as e:
            return f"Error en API Groq: {e}"

    def ejecutar_analisis(self):
        print("🧪 Iniciando análisis forense de engagement...")
        
        ratio_promedio = self.df['ratio'].mean()
        ratio_mediano = self.df['ratio'].median()
        dispersion = self.df['ratio'].std()
        correlacion = self.df['likes'].corr(self.df['comments'])
        
        outliers = self.detectar_outliers()
        
        # 1. Generar Imagen del gráfico
        plot_path = "engagement_plot.png"
        self.graficar_resultados(ratio_mediano, correlacion, outliers, plot_path)
        
        # 2. Obtener Informe de IA
        print("🤖 Consultando a la IA para diagnóstico final...")
        informe = self.generar_veredicto_ia(ratio_promedio, ratio_mediano, dispersion, correlacion, outliers)
        
        # 3. Generar PDF
        pdf_filename = "Reporte_Engagement.pdf"
        generate_pdf_report(
            pdf_filename, 
            "Auditoría de Engagement de Instagram", 
            plot_path, 
            informe
        )
        
        # Limpieza
        if os.path.exists(plot_path):
            os.remove(plot_path)

if __name__ == "__main__":
    analizador = AnalizadorEngagementPro("instagram_data.json")
    analizador.ejecutar_analisis()
