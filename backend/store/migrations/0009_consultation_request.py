from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0008_add_indexes'),
    ]

    operations = [
        migrations.CreateModel(
            name='ConsultationRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=160)),
                ('phone', models.CharField(max_length=40)),
                ('message', models.TextField(blank=True)),
                ('page_url', models.CharField(blank=True, max_length=500)),
                ('status', models.CharField(choices=[('new', 'New'), ('done', 'Done')], db_index=True, default='new', max_length=16)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('handled_at', models.DateTimeField(blank=True, null=True)),
            ],
        ),
    ]
