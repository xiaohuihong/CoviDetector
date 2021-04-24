from django.shortcuts import render
from django.http import HttpResponse
from django.http import HttpResponseRedirect
import datetime, pytz
from django.forms import modelform_factory
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import FormView, TemplateView, View
from . import constants
from .forms import BaseApplicationForm
from .models import UserProfile
import pickle
import os
import numpy as np
import pandas as pd
from random import sample
import matplotlib.pyplot as plt
from sklearn import tree
from sklearn.metrics import classification_report
from sklearn.metrics import confusion_matrix

from chatbot import chatter
from django.http import JsonResponse
import json
import logging
# Create your views here.

def index(request):
    context = {'news_list': "test"}
    return render(request, 'recommender/index.html', context=context)

def get_user_id_from_hash(user_id):
    # Find and return an unexpired, not-yet-completed JobApplication
    # with a matching user_id, or None if no such object exists.
    now = datetime.datetime.utcnow().replace(tzinfo=pytz.timezone('Asia/Singapore'))
    max_age = 300  # Or make this a setting in "settings.py"
    exclude_before = now - datetime.timedelta(seconds=max_age)
    return UserProfile.objects.filter(
        user_id=user_id,
        modified__gte=exclude_before
    ).exclude(
        stage=constants.COMPLETE
    ).first()

def predict_covid_result(fields):
    module_dir = os.path.dirname(__file__)
    print(module_dir)
    filename = os.path.join(module_dir, '../model/decision_tree_model.pkl')
    loaded_model = pickle.load(open(filename, 'rb'))

    # creating a list of column names
    column_values = ['cough', 'sore_throat', 'test_indication_Abroad', \
                     'shortness_of_breath', 'fever', 'test_indication_Contact with confirmed', \
                     'age_60_and_above_Yes', 'test_indication_Other', 'female', 'head_ache']

    cough = 1 if fields.Do_you_have_cough == constants.YES else 0
    shortness_of_breath = 1 if fields.Are_you_experiencing_breath_shortness ==  constants.YES else 0
    fever = 1 if fields.Are_you_running_a_fever ==  constants.YES else 0
    sore_throat = 1 if fields.Do_you_have_a_sore_throat ==  constants.YES else 0
    head_ache = 1 if fields.Do_you_have_a_headache ==  constants.YES else 0
    age_60_and_above_Yes = 1 if fields.What_is_your_age >= 60 else 0
    female = 1 if fields.What_is_your_gender == constants.FEMALE else 0
    test_indication_Contact = 1 if fields.Have_you_been_in_contact_with_someone_with_COVID_19 == constants.YES else 0
    test_indication_Abroad = 1 if fields.Have_you_been_overseas_in_the_last_14_days == constants.YES else 0
    if test_indication_Contact == 0 and test_indication_Abroad == 0:
        test_indication_Other = 1
    else:
        test_indication_Other = 0

    array = np.array([[cough, sore_throat, test_indication_Abroad, \
                     shortness_of_breath, fever, test_indication_Contact, \
                     age_60_and_above_Yes, test_indication_Other, female, head_ache]])

    # creating the dataframe
    df = pd.DataFrame(data=array,
                      columns=column_values)

    result = loaded_model.predict(df)
    print("The result is ", result[0])
    return result[0]

class RecommenderView(FormView):
    template_name = 'recommender/questionnaire.html'
    user_id = None
    form_class = None

    def dispatch(self, request, *args, **kwargs):
        user_id = request.session.get("user_id", None)
        # Get the job application for this session. It could be None.
        self.user_id = get_user_id_from_hash(user_id)
        # Attach the request to "self" so "form_valid()" can access it below.
        self.request = request
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        # This data is valid, so set this form's session hash in the session.
        self.request.session["user_id"] = form.instance.user_id
        current_stage = form.cleaned_data.get("stage")
        # Get the next stage after this one.
        new_stage = constants.STAGE_ORDER[constants.STAGE_ORDER.index(current_stage) + 1]
        form.instance.stage = new_stage
        form.save()  # This will save the underlying instance.

        if new_stage == constants.COMPLETE:
            predictor_output = predict_covid_result(form.instance)
            if predictor_output == 0:
                form.instance.outcome = "negative"
                return redirect(reverse("recommender:negative"))
            elif predictor_output == 1:
                form.instance.outcome = "positive"
                return redirect(reverse("recommender:positive"))

            form.save()
        return redirect(reverse("recommender:recommender"))

    def get_form_class(self):

        stage = self.user_id.stage if self.user_id else constants.STAGE_1

        fields = UserProfile.get_fields_by_stage(stage)

        return modelform_factory(UserProfile, BaseApplicationForm, fields)

    def get_form_kwargs(self):

        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.user_id
        return kwargs


class RecommenderThankYouView(TemplateView):
    template_name = 'recommender/thank_you.html'

class RecommenderWelcomeView(TemplateView):
    template_name = 'recommender/welcome.html'

class RecommenderPositiveView(TemplateView):
    template_name = 'recommender/positive.html'

class RecommenderNegativeView(TemplateView):
    template_name = 'recommender/negative.html'

class RecommenderAboutView(TemplateView):
    template_name = 'recommender/about.html'

class ChatBotAppView(TemplateView):
    template_name = 'recommender/chatbot.html'


class ChatBotApiView(View):
    """
    Provide an API endpoint to interact with ChatterBot.
    """
    logging.basicConfig(level=logging.INFO)

    print("===================================test==================================")

    cwd = os.getcwd()
    data_path = os.path.join(cwd + '\\..\\..\\Miscellaneous\\')
    excel_name = 'COVID_FAQ.xlsx'
    worksheet_name = 'FAQ'
    threshold = 0.6

    covid_faq_chatbot = chatter.faq_chatbot_initialize("Covid FAQ Chat Bot", excel_path=data_path + excel_name,
                                                       worksheet_name=worksheet_name)
    covid_nlp_chatbot = chatter.nlp_chatbot_initialize("Covid NLP Chat Bot", data_path)

    def post(self, request, *args, **kwargs):
        """
        Return a response to the statement in the posted data.
        * The JSON data should contain a 'text' attribute.
        """
        input_data = json.loads(request.body.decode('utf-8'))

        if 'text' not in input_data:
            return JsonResponse({
                'text': [
                    'The attribute "text" is required.'
                ]
            }, status=400)
        print(input_data['text'])
        # response = self.chatterbot.get_response(input_data['text'])
        response = chatter.get_answer(self.covid_faq_chatbot, self.covid_nlp_chatbot, input_data['text'],
                                      self.threshold)
        # response_data = response.serialize()

        return JsonResponse({
            'text': [
                response
            ]
        }, status=200)

    def get(self, request, *args, **kwargs):
        """
        Return data corresponding to the current conversation.
        """
        return JsonResponse({
            'name': self.covid_faq_chatbot.name
        })


if __name__ == "__main__":
    print("utility mod is run directly")