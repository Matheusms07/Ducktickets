import boto3
import json
import time
from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..models import Order
from ..services.emails.ses_mailer import SESMailer
from ..services.qrcode.generator import generate_qr_code
from ..config import settings
from ..routes.webhook import process_payment_webhook

class SQSWorker:
    def __init__(self):
        self.sqs = boto3.client('sqs', region_name=settings.aws_region)
        self.queue_url = settings.sqs_queue_url
        self.dlq_url = settings.sqs_dlq_url
        self.mailer = SESMailer()
    
    def process_messages(self):
        """Process SQS messages"""
        while True:
            try:
                # Receive messages
                response = self.sqs.receive_message(
                    QueueUrl=self.queue_url,
                    MaxNumberOfMessages=10,
                    WaitTimeSeconds=20,
                    MessageAttributeNames=['All']
                )
                
                messages = response.get('Messages', [])
                
                for message in messages:
                    try:
                        self.process_single_message(message)
                        
                        # Delete message after successful processing
                        self.sqs.delete_message(
                            QueueUrl=self.queue_url,
                            ReceiptHandle=message['ReceiptHandle']
                        )
                        
                    except Exception as e:
                        print(f"Error processing message: {e}")
                        # Message will be retried or sent to DLQ
                
                if not messages:
                    time.sleep(5)  # No messages, wait a bit
                    
            except Exception as e:
                print(f"SQS polling error: {e}")
                time.sleep(10)
    
    def process_single_message(self, message):
        """Process a single SQS message"""
        body = json.loads(message['Body'])
        message_type = body.get('type')
        
        db = SessionLocal()
        try:
            if message_type == 'payment_webhook':
                # Process payment webhook
                webhook_data = body.get('data', {})
                process_payment_webhook(webhook_data, db)
                
            elif message_type == 'send_confirmation':
                # Send confirmation email
                order_id = body.get('order_id')
                self.send_confirmation_emails(order_id, db)
                
            else:
                print(f"Unknown message type: {message_type}")
                
        finally:
            db.close()
    
    def send_confirmation_emails(self, order_id: int, db: Session):
        """Send confirmation emails for order"""
        order = db.query(Order).filter(Order.id == order_id).first()
        
        if not order or order.status != "paid":
            return
        
        for attendee in order.attendees:
            try:
                # Generate QR code image
                qr_code_data = generate_qr_code(attendee.qr_code)
                
                # Send email
                result = self.mailer.send_confirmation_email(
                    attendee.email,
                    attendee.full_name,
                    order.event.name,
                    qr_code_data,
                    order.id
                )
                
                print(f"Email sent to {attendee.email}: {result}")
                
            except Exception as e:
                print(f"Error sending email to {attendee.email}: {e}")

def run_worker():
    """Run SQS worker"""
    worker = SQSWorker()
    print("Starting SQS worker...")
    worker.process_messages()

if __name__ == "__main__":
    run_worker()