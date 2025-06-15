import os
import zipfile
import shutil
from django.conf import settings
from django.core.files.storage import default_storage
from .models import Chat, Attachment

def handle_file_upload(file, chat_id):
    chat = Chat.objects.get(id=chat_id)
    file_name = default_storage.save(f'chat_{chat_id}/{file.name}', file)
    file_path = os.path.join(settings.MEDIA_ROOT, file_name)

    if file_name.endswith('.zip'):
        extract_path = os.path.join(settings.MEDIA_ROOT, f'chat_{chat_id}/extracted')
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
        
        for root, dirs, files in os.walk(extract_path):
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, extract_path)
                Attachment.objects.create(
                    chat=chat,
                    file=f'chat_{chat_id}/extracted/{relative_path}',
                    original_name=file
                )
        
        os.remove(os.path.join(settings.MEDIA_ROOT, file_name))
    else:
        Attachment.objects.create(
            chat=chat,
            file=file_name,
            original_name=file.name
        )

    return True

def get_file_contents(file_path, max_chars=None):
    with open(file_path, 'r') as file:
        content = file.read(max_chars) if max_chars else file.read()
    return content

def delete_attachment(attachment_id):
    attachment = Attachment.objects.get(id=attachment_id)
    file_path = os.path.join(settings.MEDIA_ROOT, str(attachment.file))
    
    if os.path.exists(file_path):
        if os.path.isdir(file_path):
            shutil.rmtree(file_path)
        else:
            os.remove(file_path)
    
    attachment.delete()
    return True