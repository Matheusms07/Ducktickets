import boto3
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from jinja2 import Template
from typing import List, Optional
from ...config import settings

class SESMailer:
    def __init__(self):
        self.ses_client = boto3.client('ses', region_name=settings.aws_region)
    
    def send_confirmation_email(
        self, 
        to_email: str, 
        attendee_name: str, 
        event_name: str,
        qr_code_data: bytes,
        order_id: int
    ):
        """Send ticket confirmation email with QR code"""
        
        # Email template
        html_template = Template("""
        <html>
        <body>
            <h2>Confirmação de Inscrição - {{ event_name }}</h2>
            <p>Olá {{ attendee_name }},</p>
            <p>Sua inscrição foi confirmada com sucesso!</p>
            <p><strong>Evento:</strong> {{ event_name }}</p>
            <p><strong>Pedido:</strong> #{{ order_id }}</p>
            <p>Seu ingresso está em anexo. Apresente o QR Code na entrada do evento.</p>
            <p>Obrigado!</p>
        </body>
        </html>
        """)
        
        text_template = Template("""
        Confirmação de Inscrição - {{ event_name }}
        
        Olá {{ attendee_name }},
        
        Sua inscrição foi confirmada com sucesso!
        
        Evento: {{ event_name }}
        Pedido: #{{ order_id }}
        
        Seu ingresso está em anexo. Apresente o QR Code na entrada do evento.
        
        Obrigado!
        """)
        
        # Create message
        msg = MIMEMultipart('mixed')
        msg['Subject'] = f'Confirmação de Inscrição - {event_name}'
        msg['From'] = settings.ses_sender_email
        msg['To'] = to_email
        
        # Create message body
        msg_body = MIMEMultipart('alternative')
        
        # Text part
        text_part = MIMEText(
            text_template.render(
                attendee_name=attendee_name,
                event_name=event_name,
                order_id=order_id
            ),
            'plain'
        )
        msg_body.attach(text_part)
        
        # HTML part
        html_part = MIMEText(
            html_template.render(
                attendee_name=attendee_name,
                event_name=event_name,
                order_id=order_id
            ),
            'html'
        )
        msg_body.attach(html_part)
        
        msg.attach(msg_body)
        
        # Attach QR code
        qr_attachment = MIMEApplication(qr_code_data)
        qr_attachment.add_header(
            'Content-Disposition',
            'attachment',
            filename=f'ticket_{order_id}.png'
        )
        msg.attach(qr_attachment)
        
        # Send email
        try:
            response = self.ses_client.send_raw_email(
                Source=settings.ses_sender_email,
                Destinations=[to_email],
                RawMessage={'Data': msg.as_string()}
            )
            return {"success": True, "message_id": response['MessageId']}
        except Exception as e:
            return {"success": False, "error": str(e)}