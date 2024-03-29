# Generated by Django 3.1.7 on 2021-03-28 07:45

import django.contrib.auth.models
import django.contrib.auth.validators
import django.utils.timezone
import ldapdb.models.fields
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="LdapGroup",
            fields=[
                (
                    "dn",
                    ldapdb.models.fields.CharField(
                        max_length=200, primary_key=True, serialize=False
                    ),
                ),
                (
                    "cn",
                    ldapdb.models.fields.CharField(
                        db_column="cn", max_length=200, unique=True
                    ),
                ),
                (
                    "description",
                    ldapdb.models.fields.CharField(
                        db_column="description", max_length=200
                    ),
                ),
                ("members", ldapdb.models.fields.ListField(db_column="member")),
            ],
            options={
                "verbose_name": "LDAP group",
                "verbose_name_plural": "LDAP groups",
            },
        ),
        migrations.CreateModel(
            name="LdapPerson",
            fields=[
                (
                    "dn",
                    ldapdb.models.fields.CharField(
                        max_length=200, primary_key=True, serialize=False
                    ),
                ),
                (
                    "uid",
                    ldapdb.models.fields.CharField(
                        db_column="uid", max_length=200, unique=True
                    ),
                ),
                ("cn", ldapdb.models.fields.CharField(db_column="cn", max_length=200)),
                ("sn", ldapdb.models.fields.CharField(db_column="sn", max_length=200)),
                (
                    "mail",
                    ldapdb.models.fields.CharField(db_column="mail", max_length=200),
                ),
            ],
            options={
                "verbose_name": "LDAP person",
                "verbose_name_plural": "LDAP people",
            },
        ),
        migrations.CreateModel(
            name="TapirUser",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("password", models.CharField(max_length=128, verbose_name="password")),
                (
                    "last_login",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="last login"
                    ),
                ),
                (
                    "is_superuser",
                    models.BooleanField(
                        default=False,
                        help_text="Designates that this user has all permissions without explicitly assigning them.",
                        verbose_name="superuser status",
                    ),
                ),
                (
                    "username",
                    models.CharField(
                        error_messages={
                            "unique": "A user with that username already exists."
                        },
                        help_text="Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.",
                        max_length=150,
                        unique=True,
                        validators=[
                            django.contrib.auth.validators.UnicodeUsernameValidator()
                        ],
                        verbose_name="username",
                    ),
                ),
                (
                    "first_name",
                    models.CharField(
                        blank=True, max_length=150, verbose_name="first name"
                    ),
                ),
                (
                    "last_name",
                    models.CharField(
                        blank=True, max_length=150, verbose_name="last name"
                    ),
                ),
                (
                    "email",
                    models.EmailField(
                        blank=True, max_length=254, verbose_name="email address"
                    ),
                ),
                (
                    "is_staff",
                    models.BooleanField(
                        default=False,
                        help_text="Designates whether the user can log into this admin site.",
                        verbose_name="staff status",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        default=True,
                        help_text="Designates whether this user should be treated as active. Unselect this instead of deleting accounts.",
                        verbose_name="active",
                    ),
                ),
                (
                    "date_joined",
                    models.DateTimeField(
                        default=django.utils.timezone.now, verbose_name="date joined"
                    ),
                ),
                (
                    "groups",
                    models.ManyToManyField(
                        blank=True,
                        help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.Group",
                        verbose_name="groups",
                    ),
                ),
                (
                    "user_permissions",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Specific permissions for this user.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.Permission",
                        verbose_name="user permissions",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
            managers=[
                ("objects", django.contrib.auth.models.UserManager()),
            ],
        ),
    ]
