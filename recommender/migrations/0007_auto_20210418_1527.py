# Generated by Django 3.1.7 on 2021-04-18 07:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recommender', '0006_auto_20210411_1748'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='breath_shortness',
            field=models.CharField(choices=[(0, 'NO'), (1, 'YES')], default='NO', max_length=10),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='cough',
            field=models.CharField(choices=[(0, 'NO'), (1, 'YES')], default='NO', max_length=10),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='fever',
            field=models.CharField(choices=[(0, 'NO'), (1, 'YES')], default='NO', max_length=10),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='headache',
            field=models.CharField(choices=[(0, 'NO'), (1, 'YES')], default='NO', max_length=10),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='sore_throat',
            field=models.CharField(choices=[(0, 'NO'), (1, 'YES')], default='NO', max_length=10),
        ),
    ]
