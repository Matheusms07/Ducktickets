import boto3
from botocore.exceptions import ClientError
from typing import Optional
from ..config import settings

class S3Storage:
    def __init__(self):
        self.s3_client = boto3.client('s3', region_name=settings.aws_region)
        self.bucket = settings.s3_bucket
    
    def upload_file(self, file_data: bytes, key: str, content_type: str = 'application/octet-stream') -> Optional[str]:
        """Upload file to S3 and return URL"""
        try:
            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=file_data,
                ContentType=content_type
            )
            
            return f"https://{self.bucket}.s3.{settings.aws_region}.amazonaws.com/{key}"
        except ClientError as e:
            print(f"Error uploading to S3: {e}")
            return None
    
    def delete_file(self, key: str) -> bool:
        """Delete file from S3"""
        try:
            self.s3_client.delete_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError as e:
            print(f"Error deleting from S3: {e}")
            return False
    
    def generate_presigned_url(self, key: str, expiration: int = 3600) -> Optional[str]:
        """Generate presigned URL for file access"""
        try:
            response = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket, 'Key': key},
                ExpiresIn=expiration
            )
            return response
        except ClientError as e:
            print(f"Error generating presigned URL: {e}")
            return None