# Generated by Django 4.2.7 on 2024-01-19 06:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('grabify', '0006_orderitems_variant'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderdetails',
            name='arriving_date',
            field=models.DateTimeField(null=True),
        ),
    ]
