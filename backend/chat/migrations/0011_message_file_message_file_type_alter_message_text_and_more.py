# Generated by Django 5.0.3 on 2025-01-14 13:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0010_alter_tokenusage_options_rename_date_chat_created_at_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='file',
            field=models.FileField(blank=True, null=True, upload_to='chat/files/'),
        ),
        migrations.AddField(
            model_name='message',
            name='file_type',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='message',
            name='text',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='message',
            name='type',
            field=models.CharField(choices=[('text', 'text'), ('image', 'image'), ('file', 'file')], default='text', max_length=10),
        ),
    ]
