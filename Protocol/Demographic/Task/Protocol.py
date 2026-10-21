"""Demographic survey protocol that collects participant information."""
# Imports
from Classes.Survey import SurveyBase
from kivy.app import App
import pathlib
import json


# Survey Protocol Class

class SurveyProtocol(SurveyBase):
    """Demographic survey that loads its questions from a per-language JSON file.

    Subclass of ``SurveyBase`` that sets the survey title, description and end
    text, loads ``Protocol/Demographic/Language/<language>/survey.json`` and
    starts the survey on construction.

    Attributes
    ----------
    name : str
        Screen name, ``'Demographic'``.
    app : kivy.app.App
        The running TouchCog app.
    survey_name : str
        Title text, ``'Demographic Survey'``.
    survey_description : str
        Description text shown under the title.
    end_survey_text : str
        Message shown when the survey is completed.
    language : str
        Language folder name taken from ``app.language``.
    survey_path : pathlib.Path
        Location of the ``survey.json`` question file for ``language``.
    survey_json : dict
        Parsed contents of ``survey_path``.
    """

    def __init__(self, **kwargs):
        """Set the survey texts, load the language survey JSON and show the start screen.

        Parameters
        ----------
        **kwargs : dict
            Passed to ``SurveyBase``.

        Raises
        ------
        FileNotFoundError
            If no ``survey.json`` exists for the app language.
        """
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