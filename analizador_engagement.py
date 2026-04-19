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
    """
    Analizador avanzado de engagement para detectar anomalias y posibles fraudes
    en cuentas de Instagram mediante la relacion entre likes y comentarios.
    """
    def __init__(self, archivo_json):
        """
        Inicializa el analizador cargando y limpiando los datos.
        
        Args:
            archivo_json (str): Ruta al archivo JSON con los datos.
        """
        if not os.path.exists(archivo_json):
            print(f"Error: El archivo {archivo_json} no existe.")
            exit()
            
        with open(archivo_json, 'r', encoding='utf-8') as f:
            self.df = pd.DataFrame(json.load(f))
        
        # Limpieza de datos: asegurar que sean numericos
        self.df['likes'] = pd.to_numeric(self.df['likes'], errors='coerce').fillna(0)
        self.df['comments'] = pd.to_numeric(self.df['comments'], errors='coerce').fillna(0)
        
        # Filtramos posts sin interacciones para evitar division por cero o ratios infinitos
        self.df = self.df[self.df['likes'] > 0].copy()
        
        # Calculo del ratio individual por post (comentarios / likes)
        self.df['ratio'] = (self.df['comments'] / self.df['likes']) * 100

    def detectar_outliers(self):
        """
        Detecta puntos anomalos usando Z-Score sobre el ratio de engagement.
        
        Returns:
            pd.DataFrame: Subconjunto del DataFrame con los outliers detectados.
        """
        mean_ratio = self.df['ratio'].mean()
        std_ratio = self.df['ratio'].std()
        
        if std_ratio == 0:
            self.df['z_score'] = 0
        else:
            self.df['z_score'] = (self.df['ratio'] - mean_ratio) / std_ratio
            
        return self.df[np.abs(self.df['z_score']) > 2].copy()

    def graficar_resultados(self, mediana, corr, outliers, save_path="engagement_plot.png"):
        """
        Genera un grafico de dispersion (Scatter Plot) y lo guarda como imagen.
        
        Args:
            mediana (float): Mediana del ratio de engagement.
            corr (float): Coeficiente de correlacion de Pearson.
            outliers (pd.DataFrame): Datos de las anomalias detectadas.
            save_path (str): Ruta para guardar la imagen.
        """
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(12, 7))
        
        sns.scatterplot(data=self.df, x='likes', y='comments', 
                        alpha=0.5, s=80, color='#00d4ff', label='Posts Normales', ax=ax)
        
        sns.regplot(data=self.df, x='likes', y='comments', scatter=False, 
                    color='#ff0055', line_kws={'linewidth': 2, 'label': 'Tendencia de Cuenta'}, ax=ax)

        if not outliers.empty:
            sns.scatterplot(data=outliers, x='likes', y='comments', 
                            color='#ff4444', s=150, marker='X', label='ANOMALIAS (Outliers)', ax=ax)

        ax.set_title(f'Auditoria de Coherencia: Likes vs Comentarios\nPearson Correlation: {corr:.2f}', 
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
        print(f"Grafico guardado en: {save_path}")
        plt.close()

    def generar_veredicto_ia(self, user_name, ratio_mean, ratio_med, std, corr, outliers):
        """
        Genera un analisis forense utilizando la IA de Groq.
        
        Args:
            user_name (str): Nombre del perfil.
            ratio_mean (float): Ratio promedio.
            ratio_med (float): Ratio mediano.
            std (float): Desviacion estandar.
            corr (float): Correlacion de Pearson.
            outliers (pd.DataFrame): Outliers detectados.
            
        Returns:
            str: Texto del veredicto generado por la IA.
        """
        prompt = f"""
        Eres un analista forense de redes sociales especializado en deteccion de fraude.
        Analiza la cuenta: {user_name}
        
        DATOS DE LA CUENTA:
        - Ratio Promedio: {ratio_mean:.2f}%
        - Ratio Mediano: {ratio_med:.2f}%
        - Desviacion Estandar (Dispersion): {std:.2f}
        - Correlacion de Pearson: {corr:.2f}
        - Outliers detectados: {len(outliers)} de {len(self.df)} posts

        REGLAS TECNICAS DE INTERPRETACION:
        1. Ratio normal: 0.5% - 3%.
        2. Ratio < 0.1% -> Fuertes indicios de compra de likes.
        3. Alta desviacion estandar (>1.5 sobre la media) -> Comportamiento inestable/erratico.
        4. Correlacion < 0.4 -> Los likes y comentarios no crecen juntos (Interaccion Artificial).
        5. Muchos outliers -> Manipulacion quirurgica de publicaciones especificas.

        TAREAS:
        - Evalua la coherencia del engagement (Mediana vs Media).
        - Identifica anomalias especificas en el comportamiento de la cuenta.
        - Clasifica el riesgo de fraude: BAJO, MEDIO o ALTO.
        - Da un veredicto tecnico basado en los resultados.
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

    def ejecutar_analisis(self, user_name="Usuario"):
        """
        Orquesta el proceso completo de analisis de engagement.
        
        Args:
            user_name (str): Nombre del perfil analizado.
        """
        print(f"Iniciando analisis forense de engagement para {user_name}...")
        
        ratio_promedio = self.df['ratio'].mean()
        ratio_mediano = self.df['ratio'].median()
        dispersion = self.df['ratio'].std()
        correlacion = self.df['likes'].corr(self.df['comments'])
        
        outliers = self.detectar_outliers()
        
        # 1. Generar Imagen del grafico
        plot_path = "engagement_plot.png"
        self.graficar_resultados(ratio_mediano, correlacion, outliers, plot_path)
        
        # 2. Obtener Informe de IA
        print("Consultando a la IA para diagnostico final...")
        informe = self.generar_veredicto_ia(user_name, ratio_promedio, ratio_mediano, dispersion, correlacion, outliers)
        
        # 3. Generar PDF
        pdf_filename = f"Reporte_Engagement_{user_name}.pdf"
        generate_pdf_report(
            pdf_filename, 
            f"Auditoria de Engagement: {user_name}", 
            plot_path, 
            informe
        )
        
        # Limpieza
        if os.path.exists(plot_path):
            os.remove(plot_path)

if __name__ == "__main__":
    analizador = AnalizadorEngagementPro("instagram_data.json")
    analizador.ejecutar_analisis()
