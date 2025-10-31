# Imports
from kivy.uix.screenmanager import Screen
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.checkbox import CheckBox
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.slider import Slider
from kivy.uix.widget import Widget
from kivy.graphics import Line, Color, Ellipse
from kivy.core.window import Window
import pandas as pd
import json
import configparser
import pathlib

# Survey Class

class LikertScale(Widget):
    """
    A custom Likert scale widget with a horizontal draggable indicator.
    """
    def __init__(self, scale_min, scale_max, **kwargs):
        super(LikertScale, self).__init__(**kwargs)
        self.scale_min = scale_min
        self.scale_max = scale_max
        self.current_value = scale_min
        self.indicator_size = 30
        self.padding = 40
        
        self.bind(pos=self.update_canvas, size=self.update_canvas)
        self.update_canvas()
        
    def update_canvas(self, *args):
        """Update the scale display with lines and labels."""
        self.canvas.clear()
        
        with self.canvas:
            Color(0.2, 0.2, 0.2, 1)
            
            # Draw scale line
            line_y = self.center_y
            line_x_start = self.x + self.padding
            line_x_end = self.x + self.width - self.padding
            Line(points=[line_x_start, line_y, line_x_end, line_y], width=2)
            
            # Draw tick marks
            num_points = self.scale_max - self.scale_min + 1
            tick_spacing = (line_x_end - line_x_start) / (num_points - 1) if num_points > 1 else 0
            
            for i in range(num_points):
                tick_x = line_x_start + (i * tick_spacing)
                # Draw tick mark
                Line(points=[tick_x, line_y - 5, tick_x, line_y + 5], width=1)
            
            # Draw indicator circle with white border
            indicator_x = self._get_indicator_x()
            
            # Draw blue circle (filled)
            Color(0.2, 0.6, 0.8, 1)
            Ellipse(pos=(indicator_x - self.indicator_size/2, line_y - self.indicator_size/2),
                    size=(self.indicator_size, self.indicator_size))
            
            # Draw white border around circle
            Color(1, 1, 1, 1)
            Line(circle=(indicator_x, line_y, self.indicator_size/2), width=2)
    
    def _get_indicator_x(self):
        """Calculate the x position of the indicator based on current value."""
        line_x_start = self.x + self.padding
        line_x_end = self.x + self.width - self.padding
        num_points = self.scale_max - self.scale_min + 1
        
        if num_points == 1:
            return (line_x_start + line_x_end) / 2
        
        value_ratio = (self.current_value - self.scale_min) / (self.scale_max - self.scale_min)
        return line_x_start + value_ratio * (line_x_end - line_x_start)
    
    def on_touch_down(self, touch):
        """Handle touch down on the scale."""
        if not self.collide_point(*touch.pos):
            return False
        
        self._update_value_from_touch(touch.x)
        touch.grab(self)
        return True
    
    def on_touch_move(self, touch):
        """Handle touch movement on the scale."""
        if touch.grab_current is self:
            self._update_value_from_touch(touch.x)
            return True
        return False
    
    def on_touch_up(self, touch):
        """Handle touch release."""
        if touch.grab_current is self:
            touch.ungrab(self)
            return True
        return False
    
    def _update_value_from_touch(self, touch_x):
        """Update the current value based on touch x position."""
        line_x_start = self.x + self.padding
        line_x_end = self.x + self.width - self.padding
        
        # Clamp touch position to the line
        clamped_x = max(line_x_start, min(line_x_end, touch_x))
        
        # Convert x position to value
        if line_x_end > line_x_start:
            value_ratio = (clamped_x - line_x_start) / (line_x_end - line_x_start)
            raw_value = self.scale_min + value_ratio * (self.scale_max - self.scale_min)
            self.current_value = round(raw_value)
        
        self.update_canvas()
    
    def get_value(self):
        """Get the current Likert scale value."""
        return self.current_value


class SurveyBase(Screen):

    def __init__(self, **kwargs):
        super(SurveyBase, self).__init__(**kwargs)

        self.name = "surveyscreen"

        self.app = App.get_running_app()

        #self.question_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        self.main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        self.add_widget(self.main_layout)

        self.language = self.app.language
        self.survey_title = "Survey"
        self.survey_description = "This is a survey."
        self.end_survey_button_text = "Continue"
        self.end_survey_text = "Thank you for completing the survey!"
        self.survey_title_label = Label(text=self.survey_title, font_size='24sp', halign='center', valign='middle')
        self.survey_title_description = Label(text=self.survey_description, font_size='16sp', halign='center', valign='middle')
        self.survey_button_text = "Next"
        self.survey_button = Button(text=self.survey_button_text, size_hint=(0.3, 0.2), pos_hint={'center_x': 0.5})

        self.demographic_data = pd.DataFrame(columns=['question', 'response'])

        self.survey_json = None

        self.question_list = []
        self.question_index = 0

    def _load_end_survey_text(self):
        self.end_survey_text = "Thank you for completing the survey!"
        self.end_survey_label = Label(text=self.end_survey_text, font_size='20sp', halign='center', valign='middle')
        self.end_survey_button = Button(text="Continue", size_hint=(0.5, 0.2), pos_hint={'center_x': 0.5})

    def _return_to_main_menu(self, instance):
        self.app.screen_manager.current = "mainmenu"


    def _create_multile_choice_question(self, layout,question_text, options):
        """
        Create a multiple choice question with given text and options.
        """

        question_label = Label(text=question_text)
        self.question_layout.add_widget(question_label)

        for option in options:
            option_button = Button(text=option)
            layout.add_widget(option_button)

        survey_continue_button = Button(text="Next", size_hint=(0.3, 0.2), pos_hint={'center_x': 0.5})
        survey_continue_button.bind(on_press=self.advance_survey)
        layout.add_widget(survey_continue_button)

        return layout

    def _create_text_input_question(self, layout, question_text):
        """
        Create a text input question with given text.
        """
        question_label = Label(text=question_text)
        layout.add_widget(question_label)

        from kivy.uix.textinput import TextInput
        text_input = TextInput(multiline=False)
        layout.add_widget(text_input)

        survey_continue_button = Button(text="Next", size_hint=(0.3, 0.2), pos_hint={'center_x': 0.5})
        survey_continue_button.bind(on_press=self.advance_survey)
        layout.add_widget(survey_continue_button)

        return layout

    def _create_multi_response_question(self, layout, question_text, options):
        """
        Create a multi-response question with given text and options.
        """
        question_label = Label(text=question_text)
        layout.add_widget(question_label)

        for option in options:
            option_button = Button(text=option)
            layout.add_widget(option_button)

        survey_continue_button = Button(text="Next", size_hint=(0.3, 0.2), pos_hint={'center_x': 0.5})
        survey_continue_button.bind(on_press=self.advance_survey)
        layout.add_widget(survey_continue_button)

        return layout

    def _create_multi_response_question(self, layout, question_text, options):
        """
        Create a multi-response question with given text and options.
        """
        question_label = Label(text=question_text)
        layout.add_widget(question_label)

        for option in options:
            option_checkbox = CheckBox()
            layout.add_widget(option_checkbox)
            option_label = Label(text=option)
            layout.add_widget(option_label)
        
        survey_continue_button = Button(text="Next", size_hint=(0.3, 0.2), pos_hint={'center_x': 0.5})
        survey_continue_button.bind(on_press=self.advance_survey)
        layout.add_widget(survey_continue_button)

        return layout

    def _create_rating_scale_question(self, layout, question_text, scale_min, scale_max):
        """
        Create a Likert scale question with a draggable horizontal indicator.
        """
        question_label = Label(text=question_text, size_hint_y=None, height=40)
        layout.add_widget(question_label)

        # Create a container for the scale with labels
        scale_container = BoxLayout(orientation='vertical', size_hint_y=None, height=100, spacing=5)
        
        # Add the Likert scale widget
        likert_scale = LikertScale(scale_min=scale_min, scale_max=scale_max, size_hint_y=0.6)
        scale_container.add_widget(likert_scale)
        
        # Add label row with min and max labels
        label_row = BoxLayout(size_hint_y=0.4, spacing=10)
        min_label = Label(text=str(scale_min), size_hint_x=None, width=40)
        max_label = Label(text=str(scale_max), size_hint_x=None, width=40)
        spacer = Widget()
        label_row.add_widget(min_label)
        label_row.add_widget(spacer)
        label_row.add_widget(max_label)
        scale_container.add_widget(label_row)

        layout.add_widget(scale_container)

        survey_continue_button = Button(text="Next", size_hint=(0.3, 0.2), pos_hint={'center_x': 0.5, 'center_y': 0.15})
        survey_continue_button.bind(on_press=self.advance_survey)
        layout.add_widget(survey_continue_button)

        return layout

    def create_question(self, question_text, options=None, question_type="multiple_choice"):
        """
        Create a survey question with given text and options.
        """
        question_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        if question_type == "multiple_choice":
            question_layout = self._create_multile_choice_question(question_layout, question_text, options)
        elif question_type == "text_input":
            question_layout = self._create_text_input_question(question_layout, question_text)
        elif question_type == "multi_response":
            question_layout = self._create_multi_response_question(question_layout, question_text, options)
        elif question_type == "rating_scale":
            question_layout = self._create_rating_scale_question(question_layout, question_text, options[0], options[1])

        self.question_list.append(question_layout)

    def remove_question(self):
        """
        Remove the current question from the layout.
        """
        self.main_layout.clear_widgets()

    def load_text(self):
        """
        Load survey text from language files.
        """
        language_path = pathlib.Path('Protocol') / self.name / 'Language' / self.language / 'startscreen.ini'
        language_description_path = pathlib.Path('Protocol') / self.name / 'Language' / self.language / 'description.txt'
        # Load texts from files
        config = configparser.ConfigParser()
        config.read(language_path)
        self.survey_title = config.get('Screen', 'survey_name', fallback=self.survey_title)
        self.end_survey_text = config.get('Screen', 'end_survey_text', fallback=self.end_survey_text)
        self.survey_button_text = config.get('Screen', 'survey_button', fallback=self.survey_button_text)
        self.end_survey_button_text = config.get('Screen', 'end_survey_button', fallback="Continue")
        # Load Description Text File
        with open(language_description_path, 'r', encoding='utf-8') as f:
            self.survey_description = f.read()
        self.survey_title_label.text = self.survey_title
        self.survey_title_description.text = self.survey_description
        self.survey_button.text = self.survey_button_text
        self.end_survey_label.text = self.end_survey_text
        self.end_survey_button.text = self.end_survey_button_text

    def load_survey(self, survey_json):
        """
        Load survey questions from a JSON structure.
        """
        self._load_end_survey_text()
        self.survey_json = survey_json
        for question in survey_json['questions']:
            q_text = question['text']
            q_type = question['type']
            q_options = question.get('options', None)
            self.create_question(q_text, q_options, q_type)
    
    def advance_survey(self):
        """
        Advance to the next question in the survey.
        """
        self.remove_question()
        self.question_index += 1
        if self.question_index < len(self.question_list):
            self.main_layout.add_widget(self.question_list[self.question_index])
        else:
            # Survey is complete
            self.end_survey()

    def run_survey(self, *args):
        self.main_layout.clear_widgets()
        self.main_layout.add_widget(self.question_list[self.question_index])

    def start_screen(self):
        self.main_layout.clear_widgets()
        self.main_layout.add_widget(self.survey_title_label)
        self.main_layout.add_widget(self.survey_title_description)
        self.main_layout.add_widget(self.survey_button)
        self.survey_button.bind(on_press=self.run_survey)

    def end_survey(self):
        self.main_layout.clear_widgets()
        self.main_layout.add_widget(self.end_survey_label)
        self.main_layout.add_widget(self.end_survey_button)
        self.end_survey_button.bind(on_press=self._return_to_main_menu)
