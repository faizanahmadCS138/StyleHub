from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0008_size_alter_productvariant_unique_together_and_more'),
    ]

    operations = [
        # 1. Remove old string 'size' field directly from DB schema
        migrations.RemoveField(
            model_name='productvariant',
            name='size',
        ),
        # 2. Rename 'size_fk' (which holds all 67 migrated IDs) to 'size'
        migrations.RenameField(
            model_name='productvariant',
            old_name='size_fk',
            new_name='size',
        ),
        # 3. Apply Meta unique_together constraint
        migrations.AlterUniqueTogether(
            name='productvariant',
            unique_together={('product', 'size', 'color')},
        ),
    ]