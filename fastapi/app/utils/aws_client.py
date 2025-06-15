import boto3
import json
import logging
from typing import Dict, Any, Optional, AsyncGenerator
from botocore.exceptions import ClientError
from app.core.config import settings

logger = logging.getLogger(__name__)

class AWSBedrockClient:
    """AWS Bedrock client for Claude AI integration."""
    
    def __init__(self):
        self.client = boto3.client(
            'bedrock-runtime',
            aws_access_key_id=settings.AWS_BEDROCK_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_BEDROCK_SECRET_ACCESS_KEY,
            region_name=settings.AWS_BEDROCK_REGION
        )
        # log the keys and region
        logger.info(f"AWS Bedrock client initialized with keys: {settings.AWS_BEDROCK_ACCESS_KEY_ID} and region: {settings.AWS_BEDROCK_REGION}")
        
        # Claude model configurations
        self.models = {
            'claude-3.5-sonnet-v2': 'anthropic.claude-3-5-sonnet-20241022-v2:0',
            'claude-3.5-sonnet-v1': 'anthropic.claude-3-5-sonnet-20240620-v1:0',
            'claude-3.5-haiku': 'anthropic.claude-3-5-haiku-20241022-v1:0'
        }
        
        self.default_model = 'claude-3.5-sonnet-v2'
    
    async def generate_response(
        self,
        messages: list,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
        stream: bool = True
    ) -> AsyncGenerator[str, None]:
        """
        Generate streaming response from Claude via Bedrock.
        
        Args:
            messages: List of message dicts with role and content
            system_prompt: Optional system prompt
            model: Model to use (defaults to claude-3.5-sonnet-v2)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            stream: Whether to stream the response
            
        Yields:
            Text chunks from the streaming response
        """
        try:
            model_id = self.models.get(model or self.default_model)
            if not model_id:
                raise ValueError(f"Unknown model: {model}")
            
            # Prepare the request body
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "messages": messages,
                "temperature": temperature
            }
            
            if system_prompt:
                body["system"] = system_prompt
            
            logger.info(f"Sending request to {model_id} with {len(messages)} messages")
            
            if stream:
                # Stream the response
                response = self.client.invoke_model_with_response_stream(
                    modelId=model_id,
                    body=json.dumps(body)
                )
                
                for event in response['body']:
                    chunk = json.loads(event['chunk']['bytes'])
                    
                    if chunk['type'] == 'content_block_delta':
                        if chunk['delta']['type'] == 'text_delta':
                            yield chunk['delta']['text']
                    elif chunk['type'] == 'message_stop':
                        break
                        
            else:
                # Non-streaming response
                response = self.client.invoke_model(
                    modelId=model_id,
                    body=json.dumps(body)
                )
                
                result = json.loads(response['body'].read())
                if result.get('content'):
                    for content in result['content']:
                        if content['type'] == 'text':
                            yield content['text']
                            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ThrottlingException':
                logger.warning(f"Throttling detected for {model_id}, trying fallback")
                # Try with a fallback model
                if model != 'claude-3.5-haiku':
                    async for chunk in self.generate_response(
                        messages, system_prompt, 'claude-3.5-haiku', 
                        max_tokens, temperature, stream
                    ):
                        yield chunk
                else:
                    raise Exception("All models are throttled")
            else:
                logger.error(f"Bedrock error: {e}")
                raise Exception(f"AI service error: {error_code}")
                
        except Exception as e:
            logger.error(f"Unexpected error in generate_response: {e}")
            raise Exception(f"Failed to generate response: {str(e)}")
    
    async def generate_single_response(
        self,
        messages: list,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.0
    ) -> str:
        """
        Generate a single non-streaming response.
        
        Returns:
            Complete response text
        """
        response_text = ""
        async for chunk in self.generate_response(
            messages, system_prompt, model, max_tokens, temperature, stream=False
        ):
            response_text += chunk
        return response_text

class AWSS3Client:
    """AWS S3 client for file storage."""
    
    def __init__(self):
        self.client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION
        )
        self.bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    
    async def upload_file(
        self,
        file_content: bytes,
        file_key: str,
        content_type: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Upload a file to S3.
        
        Args:
            file_content: File content as bytes
            file_key: S3 key (path) for the file
            content_type: MIME type of the file
            metadata: Optional metadata dict
            
        Returns:
            S3 URL of the uploaded file
        """
        try:
            extra_args = {
                'ContentType': content_type,
                'ACL': 'private'  # Files are private by default
            }
            
            if metadata:
                extra_args['Metadata'] = metadata
            
            # Upload the file
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=file_key,
                Body=file_content,
                **extra_args
            )
            
            # Return the S3 URL
            url = f"https://{self.bucket_name}.s3.{settings.AWS_S3_REGION}.amazonaws.com/{file_key}"
            logger.info(f"File uploaded successfully to {url}")
            return url
            
        except ClientError as e:
            logger.error(f"S3 upload error: {e}")
            raise Exception(f"Failed to upload file: {e}")
    
    async def get_file_url(self, file_key: str, expires_in: int = 3600) -> str:
        """
        Generate a presigned URL for file access.
        
        Args:
            file_key: S3 key of the file
            expires_in: URL expiration time in seconds
            
        Returns:
            Presigned URL
        """
        try:
            url = self.client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': file_key},
                ExpiresIn=expires_in
            )
            return url
        except ClientError as e:
            logger.error(f"Error generating presigned URL: {e}")
            raise Exception(f"Failed to generate file URL: {e}")
    
    async def delete_file(self, file_key: str) -> bool:
        """
        Delete a file from S3.
        
        Args:
            file_key: S3 key of the file to delete
            
        Returns:
            True if successful
        """
        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=file_key)
            logger.info(f"File deleted successfully: {file_key}")
            return True
        except ClientError as e:
            logger.error(f"S3 delete error: {e}")
            return False

# Global instances
bedrock_client = AWSBedrockClient()
s3_client = AWSS3Client() 