# Generated by Django 5.0.3 on 2025-01-14 20:39

import chat.utils.file_validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0011_message_file_message_file_type_alter_message_text_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='message',
            name='file',
        ),
        migrations.RemoveField(
            model_name='message',
            name='file_type',
        ),
        migrations.RemoveField(
            model_name='message',
            name='image',
        ),
        migrations.RemoveField(
            model_name='message',
            name='text',
        ),
        migrations.RemoveField(
            model_name='message',
            name='type',
        ),
        migrations.CreateModel(
            name='MessageContent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content_type', models.CharField(choices=[('text', 'Text'), ('image', 'Image'), ('document', 'Document')], max_length=10)),
                ('text_content', models.TextField(blank=True, null=True)),
                ('file_content', models.FileField(blank=True, null=True, upload_to='chat_contents/%Y/%m/%d/', validators=[chat.utils.file_validators.validate_mime_type])),
                ('mime_type', models.CharField(blank=True, max_length=100, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('message', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='contents', to='chat.message')),
            ],
        ),
    ]
