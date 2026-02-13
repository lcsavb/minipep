from django.db import migrations


def rename_and_create_groups(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name="staff").update(name="admin")
    Group.objects.filter(name="doctor").update(name="doctors")
    Group.objects.get_or_create(name="front_desk")


def reverse_groups(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name="admin").update(name="staff")
    Group.objects.filter(name="doctors").update(name="doctor")
    Group.objects.filter(name="front_desk").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0010_remove_encounter_reason"),
    ]

    operations = [
        migrations.RunPython(rename_and_create_groups, reverse_groups),
    ]
