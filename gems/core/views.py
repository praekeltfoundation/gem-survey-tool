from django.contrib.auth import authenticate, login
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.generic.base import TemplateView
from models import ContactGroup, SurveyResult, Survey, Contact
import json


def user_login(request):
    # Like before, obtain the context for the user's request.
    context = RequestContext(request)

    # If the request is a HTTP POST, try to pull out the relevant information.
    if request.method == 'POST':
        # Gather the username and password provided by the user.
        # This information is obtained from the login form.
        username = request.POST['username']
        password = request.POST['password']

        # Use Django's machinery to attempt to see if the username/password
        # combination is valid - a User object is returned if it is.
        user = authenticate(username=username, password=password)

        # If we have a User object, the details are correct.
        # If None (Python's way of representing the absence of a value), no user
        # with matching credentials was found.
        if user:
            # Is the account active? It could have been disabled.
            if user.is_active:
                # If the account is valid and active, we can log the user in.
                # We'll send the user back to the homepage.
                login(request, user)
                return HttpResponseRedirect('/home/')
            else:
                # An inactive account was used - no logging in!
                return HttpResponse("Your GEM account is disabled.")
        else:
            # Bad login details were provided. So we can't log the user in.
            print "Invalid login details: {0}, {1}".format(username, password)
            return HttpResponse("Invalid login details supplied.")

    # The request is not a HTTP POST, so display the login form.
    # This scenario would most likely be a HTTP GET.
    else:
        # No context variables to pass to the template system, hence the
        # blank dictionary object...
        return render_to_response('login.html', {}, context)


class ContactGroupsView(TemplateView):

    template_name = "contact-groups.html"

    def get_context_data(self, **kwargs):
        context = super(ContactGroupsView, self).get_context_data(**kwargs)

        contactgroups = ContactGroup.objects.all()
        context['contactgroups'] = contactgroups

        return context


class CreateContactGroupsView(TemplateView):

    template_name = "createcontactgroup.html"

    def get_context_data(self, **kwargs):
        context = super(CreateContactGroupsView, self).get_context_data(**kwargs)

        contactgroups = ContactGroup.objects.all()
        context['contactgroups'] = contactgroups

        return context


def save_data(request):

    if(request.method == 'POST'):
        data=json.loads(request.body)
        answers = None
        contact_msisdn = None
        if data.has_key('user'):
            user = data['user']
            if user.has_key('answers'):
                answers = user["answers"]
        if data.has_key('contact'):
            contact = data['contact']
            if contact.has_key('msisdn'):
                contact_msisdn = contact['msisdn']

        # we have data
        if answers and contact_msisdn:
            try:
                # fetch/create the survey
                # fix this
                survey = Survey.objects.get_or_create(survey_id='1', name='Test', defaults={'survey_id': 1, 'name': 'Test'})
                survey.save()
                # add the contact
                contact = Contact.objects.get_or_create(msisdn=contact_msisdn, defaults={'age': 18, 'gender': 'F'})
                contact.save()
                # add the survey result
                survey_result = SurveyResult.objects.create();
                survey_result.survey_id = survey.survey_id
                survey_result.contact = contact
                survey_result.answer = answers
                survey.save()
            except:
                return HttpResponse('FAILED')
            else:
                return HttpResponse('OK')
    else:
        return HttpResponse('FAILED')