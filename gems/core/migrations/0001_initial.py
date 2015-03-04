# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Survey'
        db.create_table(u'core_survey', (
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200, primary_key=True)),
            ('survey_id', self.gf('django.db.models.fields.CharField')(unique=True, max_length=200)),
            ('created_on', self.gf('django.db.models.fields.DateField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal(u'core', ['Survey'])

        # Adding model 'Contact'
        db.create_table(u'core_contact', (
            ('msisdn', self.gf('django.db.models.fields.CharField')(max_length=15, primary_key=True)),
        ))
        db.send_create_signal(u'core', ['Contact'])

        # Adding model 'SurveyResult'
        db.create_table(u'core_surveyresult', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('survey', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Survey'])),
            ('contact', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Contact'])),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('answer', self.gf(u'django_hstore.fields.DictionaryField')()),
        ))
        db.send_create_signal(u'core', ['SurveyResult'])

        # Adding model 'ContactGroup'
        db.create_table(u'core_contactgroup', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('group_id', self.gf('django.db.models.fields.CharField')(max_length=5)),
            ('group_key', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('created_by', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('filters', self.gf('django.db.models.fields.CharField')(max_length=8000)),
            ('query_words', self.gf('django.db.models.fields.CharField')(max_length=8000)),
        ))
        db.send_create_signal(u'core', ['ContactGroup'])

        # Adding model 'ContactGroupMember'
        db.create_table(u'core_contactgroupmember', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.ContactGroup'])),
            ('contact', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Contact'])),
        ))
        db.send_create_signal(u'core', ['ContactGroupMember'])


    def backwards(self, orm):
        # Deleting model 'Survey'
        db.delete_table(u'core_survey')

        # Deleting model 'Contact'
        db.delete_table(u'core_contact')

        # Deleting model 'SurveyResult'
        db.delete_table(u'core_surveyresult')

        # Deleting model 'ContactGroup'
        db.delete_table(u'core_contactgroup')

        # Deleting model 'ContactGroupMember'
        db.delete_table(u'core_contactgroupmember')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'core.contact': {
            'Meta': {'object_name': 'Contact'},
            'msisdn': ('django.db.models.fields.CharField', [], {'max_length': '15', 'primary_key': 'True'})
        },
        u'core.contactgroup': {
            'Meta': {'object_name': 'ContactGroup'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'filters': ('django.db.models.fields.CharField', [], {'max_length': '8000'}),
            'group_id': ('django.db.models.fields.CharField', [], {'max_length': '5'}),
            'group_key': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'query_words': ('django.db.models.fields.CharField', [], {'max_length': '8000'})
        },
        u'core.contactgroupmember': {
            'Meta': {'object_name': 'ContactGroupMember'},
            'contact': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.Contact']"}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.ContactGroup']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'core.survey': {
            'Meta': {'object_name': 'Survey'},
            'created_on': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'primary_key': 'True'}),
            'survey_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'})
        },
        u'core.surveyresult': {
            'Meta': {'object_name': 'SurveyResult'},
            'answer': (u'django_hstore.fields.DictionaryField', [], {}),
            'contact': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.Contact']"}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'survey': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.Survey']"}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['core']