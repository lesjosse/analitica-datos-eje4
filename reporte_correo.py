import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
import pandas as pd

def enviar_reporte_email(destinatario, remitente, password_app, titulo_dashboard, resumen_texto, df_filtrado):
    """Envía un correo HTML con resumen estadístico y el CSV filtrado adjunto."""
    msg = MIMEMultipart()
    msg["From"] = remitente
    msg["To"] = destinatario
    msg["Subject"] = f"Reporte Analítica de Datos - {titulo_dashboard} ({datetime.now().strftime('%Y-%m-%d %H:%M')})"

    cuerpo_html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #222;">
        <h2 style="color: #0f4c81;">Reporte Automático de Analítica de Datos</h2>
        <p><strong>Módulo analizado:</strong> {titulo_dashboard}</p>
        <p><strong>Fecha de generación:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
        <hr>
        <h3>Resumen Estadístico del Análisis:</h3>
        <pre style="background-color: #f4f6f8; padding: 12px; border-radius: 6px;">{resumen_texto}</pre>
        <p>Se adjunta el archivo CSV con los datos limpios y filtrados correspondientes a este análisis.</p>
      </body>
    </html>
    """
    msg.attach(MIMEText(cuerpo_html, "html"))

    # Adjuntar datos filtrados en CSV
    csv_bytes = df_filtrado.to_csv(index=False).encode("utf-8")
    adjunto = MIMEBase("application", "octet-stream")
    adjunto.set_payload(csv_bytes)
    encoders.encode_base64(adjunto)
    adjunto.add_header("Content-Disposition", 'attachment; filename="datos_reporte.csv"')
    msg.attach(adjunto)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(remitente, password_app)
        server.send_message(msg)

# tarea automática en  Linux (Cron)
if __name__ == "__main__":
    df = pd.read_csv("exportacionesdebienesyserviciosdelpib.csv", skiprows=3, encoding="latin1")
    col = df[df["Country Code"] == "COL"].melt(
        id_vars=["Country Name", "Country Code"],
        value_vars=[str(y) for y in range(1960, 2021)],
        var_name="Año",
        value_name="Valor"
    ).dropna()

    resumen = (
        f"País: Colombia (COL)\n"
        f"Indicador: Exportaciones de bienes y servicios (% del PIB)\n"
        f"Promedio histórico (1960-2020): {col['Valor'].mean():.2f}%\n"
        f"Valor máximo: {col['Valor'].max():.2f}% | Valor mínimo: {col['Valor'].min():.2f}%"
    )
    # 
    enviar_reporte_email(
        destinatario="user6@areandina.edu.co",
        remitente="user@gmail.com",
        password_app="********",
        titulo_dashboard="Reporte Programado - Exportaciones Colombia",
        resumen_texto=resumen,
        df_filtrado=col
    )
    print("Reporte programado enviado correctamente.")