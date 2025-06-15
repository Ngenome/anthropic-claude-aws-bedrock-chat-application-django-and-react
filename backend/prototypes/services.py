import json
import boto3
import os
import re
from django.conf import settings
from .models import PrototypeVariant, PrototypeVersion

class PrototypeService:
    CLAUDE_35_SONNET_V2 = "anthropic.claude-3-5-sonnet-20241022-v2:0"
    CLAUDE_35_SONNET_V1 = "anthropic.claude-3-5-sonnet-20240620-v1:0"
    
    def __init__(self):
        self.bedrock_runtime = boto3.client(
            service_name="bedrock-runtime",
            region_name="us-west-2",
            aws_access_key_id=os.getenv("AWS_BEDROCK_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_BEDROCK_SECRET_ACCESS_KEY")
        )

        self.bedrock_runtime_us_east = boto3.client(
            service_name="bedrock-runtime",
            region_name="us-east-1",
            aws_access_key_id=os.getenv("AWS_BEDROCK_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_BEDROCK_SECRET_ACCESS_KEY")
        )
    
    def get_ui_prototype_system_prompt(self):
        return """You are an expert UI/UX designer and frontend developer specializing in creating beautiful, responsive, and functional prototypes.
When asked to create a prototype, you will generate clean, optimized HTML with CSS using Tailwind CSS classes, and JavaScript (if needed).
Your prototypes should demonstrate modern design principles, be visually appealing, and adhere to usability best practices.

IMPORTANT INSTRUCTIONS:
1. Your response MUST be ONLY the complete code inside XML tags: <prototype_file name="NAME">CODE HERE</prototype_file>
2. Replace "NAME" with a short, descriptive name for the prototype
3. Do not include ANY commentary, explanations, or incomplete examples
4. Create fully functional, self-contained prototypes with all necessary code
5. Use Tailwind CSS for styling - include the CDN link in your HTML
6. Include responsive design to work on mobile, tablet, and desktop
7. If JavaScript functionality is needed, include it inline with <script> tags
8. Use semantic HTML5 elements where appropriate
9. Ensure all UI elements have appropriate hover/focus states and animations where applicable
10. Optimize for performance and accessibility

Remember, your output MUST ONLY contain the complete code wrapped in <prototype_file> tags, with no other text.
"""

    def get_ui_prototype_edit_system_prompt(self):
        return """You are an expert UI/UX designer and frontend developer specializing in creating and modifying beautiful, responsive, and functional prototypes.
When asked to edit a prototype, you will carefully make the specified changes while maintaining the overall design integrity.

IMPORTANT INSTRUCTIONS:
1. I will provide you with the current HTML code for a prototype and a request for changes.
2. You MUST return the COMPLETE, MODIFIED code inside XML tags: <prototype_file name="NAME">CODE HERE</prototype_file>
3. Replace "NAME" with a short, descriptive name for this edited version
4. Do not provide explanations, comments, or partial code snippets - ONLY the complete, working HTML
5. Ensure all Tailwind CSS classes are properly applied and consistent with the original design
6. Make sure the edited code maintains responsive design, working across mobile, tablet, and desktop
7. Preserve the original JavaScript functionality unless specifically asked to modify it
8. Ensure all changes integrate seamlessly with the existing design
9. Maintain accessibility features and performance optimizations

Remember, your output MUST ONLY contain the complete modified code wrapped in <prototype_file> tags, with no other text.
"""

    def get_ui_prototype_variant_system_prompt(self):
        return """You are an expert UI/UX designer and frontend developer specializing in creating beautiful, responsive, and functional prototypes.
Your task is to create a variant of an existing prototype, keeping the core functionality but giving it a fresh, alternative design.

IMPORTANT INSTRUCTIONS:
1. I will provide you with the original HTML code for a prototype and optional instructions for the variant.
2. You MUST create an alternate design that maintains the same core functionality but offers a different visual approach.
3. Your response MUST be ONLY the complete code inside XML tags: <prototype_file name="NAME">CODE HERE</prototype_file>
4. Replace "NAME" with a short, descriptive name for this variant
5. Do not include ANY commentary, explanations, or incomplete examples
6. Create a fully functional, self-contained prototype with all necessary code
7. Use Tailwind CSS for styling - include the CDN link in your HTML
8. Ensure responsive design across mobile, tablet, and desktop
9. If the original has JavaScript functionality, maintain equivalent functionality but feel free to reimagine the implementation
10. Use semantic HTML5 elements where appropriate
11. Ensure all UI elements have appropriate hover/focus states and animations
12. Optimize for performance and accessibility

The variant should be clearly different in visual design while preserving the user experience and functionality.
Remember, your output MUST ONLY contain the complete code wrapped in <prototype_file> tags, with no other text.
"""

    def generate_prototype(self, prompt: str):
        """Generate a UI prototype using Claude"""
        
        # Prepare the messages for Claude
        messages = [{
            "role": "user",
            "content": [{
                "type": "text",
                "text": prompt
            }]
        }]
        
        # Create request body
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4096,
            "system": self.get_ui_prototype_system_prompt(),
            "messages": messages
        })
        
        # Invoke model and get response
        try:
            response = self.bedrock_runtime.invoke_model(
                body=body,
                modelId=self.CLAUDE_35_SONNET_V2
            )
            response_body = json.loads(response['body'].read().decode('utf-8'))
            content = response_body['content'][0]['text']
            
            # Extract HTML content from XML tags
            prototype_match = re.search(r'<prototype_file name="([^"]+)">(.*?)</prototype_file>', content, re.DOTALL)
            
            if prototype_match:
                prototype_name = prototype_match.group(1)
                html_content = prototype_match.group(2)
                return {
                    'name': prototype_name,
                    'html_content': html_content
                }
            else:
                return {
                    'name': 'Untitled Prototype',
                    'html_content': content  # Return raw content if no match
                }
                
        except Exception as e:
            # Fallback to other model or region
            try:
                response = self.bedrock_runtime_us_east.invoke_model(
                    body=body,
                    modelId=self.CLAUDE_35_SONNET_V1
                )
                response_body = json.loads(response['body'].read().decode('utf-8'))
                content = response_body['content'][0]['text']
                
                # Extract HTML content from XML tags
                prototype_match = re.search(r'<prototype_file name="([^"]+)">(.*?)</prototype_file>', content, re.DOTALL)
                
                if prototype_match:
                    prototype_name = prototype_match.group(1)
                    html_content = prototype_match.group(2)
                    return {
                        'name': prototype_name,
                        'html_content': html_content
                    }
                else:
                    return {
                        'name': 'Untitled Prototype',
                        'html_content': content  # Return raw content if no match
                    }
            except Exception as fallback_error:
                raise Exception(f"Failed to generate prototype: {str(fallback_error)}")

    def edit_prototype(self, current_html: str, edit_prompt: str):
        """
        Edit a UI prototype using Claude based on an existing version
        """
        
        # Prepare the messages for Claude
        messages = [{
            "role": "user",
            "content": [{
                "type": "text",
                "text": f"Here is the current prototype code:\n\n```html\n{current_html}\n```\n\nPlease make the following changes:\n\n{edit_prompt}"
            }]
        }]
        
        # Create request body
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4096,
            "system": self.get_ui_prototype_edit_system_prompt(),
            "messages": messages
        })
        
        try:
            response = self.bedrock_runtime.invoke_model(
                body=body,
                modelId=self.CLAUDE_35_SONNET_V2
            )
            response_body = json.loads(response['body'].read().decode('utf-8'))
            content = response_body['content'][0]['text']
            
            # Extract HTML content from XML tags
            prototype_match = re.search(r'<prototype_file name="([^"]+)">(.*?)</prototype_file>', content, re.DOTALL)
            
            if prototype_match:
                prototype_name = prototype_match.group(1)
                html_content = prototype_match.group(2)
                return {
                    'name': prototype_name,
                    'html_content': html_content
                }
            else:
                return {
                    'name': f"Edited Prototype",
                    'html_content': content  # Return raw content if no match
                }
                
        except Exception as e:
            # Fallback to other model or region
            try:
                response = self.bedrock_runtime_us_east.invoke_model(
                    body=body,
                    modelId=self.CLAUDE_35_SONNET_V1
                )
                response_body = json.loads(response['body'].read().decode('utf-8'))
                content = response_body['content'][0]['text']
                
                # Extract HTML content from XML tags
                prototype_match = re.search(r'<prototype_file name="([^"]+)">(.*?)</prototype_file>', content, re.DOTALL)
                
                if prototype_match:
                    prototype_name = prototype_match.group(1)
                    html_content = prototype_match.group(2)
                    return {
                        'name': prototype_name,
                        'html_content': html_content
                    }
                else:
                    return {
                        'name': f"Edited Prototype",
                        'html_content': content  # Return raw content if no match
                    }
            except Exception as fallback_error:
                raise Exception(f"Failed to edit prototype: {str(fallback_error)}")
    
    def create_variant(self, current_html: str, variant_prompt: str = None):
        """
        Create a variant of a UI prototype using Claude based on an existing version
        """
        
        # Prepare the messages for Claude
        prompt_text = "Here is the original prototype code:\n\n```html\n{}\n```\n\n".format(current_html)
        
        if variant_prompt:
            prompt_text += f"Please create a variant with these specific requirements:\n\n{variant_prompt}"
        else:
            prompt_text += "Please create a variant of this prototype with a different visual design but maintaining the same functionality."
        
        messages = [{
            "role": "user",
            "content": [{
                "type": "text",
                "text": prompt_text
            }]
        }]
        
        # Create request body
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4096,
            "system": self.get_ui_prototype_variant_system_prompt(),
            "messages": messages
        })
        
        try:
            response = self.bedrock_runtime.invoke_model(
                body=body,
                modelId=self.CLAUDE_35_SONNET_V2
            )
            response_body = json.loads(response['body'].read().decode('utf-8'))
            content = response_body['content'][0]['text']
            
            # Extract HTML content from XML tags
            prototype_match = re.search(r'<prototype_file name="([^"]+)">(.*?)</prototype_file>', content, re.DOTALL)
            
            if prototype_match:
                prototype_name = prototype_match.group(1)
                html_content = prototype_match.group(2)
                return {
                    'name': prototype_name,
                    'html_content': html_content
                }
            else:
                return {
                    'name': "New Variant",
                    'html_content': content  # Return raw content if no match
                }
                
        except Exception as e:
            # Fallback to other model or region
            try:
                response = self.bedrock_runtime_us_east.invoke_model(
                    body=body,
                    modelId=self.CLAUDE_35_SONNET_V1
                )
                response_body = json.loads(response['body'].read().decode('utf-8'))
                content = response_body['content'][0]['text']
                
                # Extract HTML content from XML tags
                prototype_match = re.search(r'<prototype_file name="([^"]+)">(.*?)</prototype_file>', content, re.DOTALL)
                
                if prototype_match:
                    prototype_name = prototype_match.group(1)
                    html_content = prototype_match.group(2)
                    return {
                        'name': prototype_name,
                        'html_content': html_content
                    }
                else:
                    return {
                        'name': "New Variant",
                        'html_content': content  # Return raw content if no match
                    }
            except Exception as fallback_error:
                raise Exception(f"Failed to create variant: {str(fallback_error)}") 