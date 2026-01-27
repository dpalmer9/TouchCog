# Imports
from Classes.Survey import SurveyBase
from kivy.app import App
import pathlib
import json


# Survey Protocol Class

class SurveyProtocol(SurveyBase):
    """
    A demographic survey protocol for collecting participant information.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'Demographic'
        self.app = App.get_running_app()
        self.survey_name = "Demographic Survey"
        self.survey_title_label.text = self.survey_name
        self.survey_description = "A survey to collect demographic information from participants."
        self.survey_title_description.text = self.survey_description
        self.end_survey_text = "Thank you for completing the demographic survey."


        self.survey_json = None
        self.language = self.app.language
        self.survey_path = self.app.app_root / 'Protocol' / self.name / 'Language' / self.language / 'survey.json'

        with open(self.survey_path) as f:
            self.survey_json = json.load(f)

        self.load_survey(self.survey_json)

        self.start_screen()