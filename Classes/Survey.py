# Imports
from kivy.uix.screenmanager import Screen
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.checkbox import CheckBox
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.slider import Slider
from kivy.uix.widget import Widget
from kivy.uix.scrollview import ScrollView
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
    Supports both numeric ranges and labeled options.
    """
    def __init__(self, options=None, scale_min=None, scale_max=None, **kwargs):
        super(LikertScale, self).__init__(**kwargs)
        
        # Handle both old format (scale_min, scale_max) and new format (options dict)
        if options is not None:
            # New format: options is a dict with keys as IDs and values as labels
            self.options = options
            self.option_keys = list(options.keys())
            self.scale_min = 0
            self.scale_max = len(self.option_keys) - 1
            self.current_value = 0
        else:
            # Old format: numeric range
            self.scale_min = scale_min if scale_min is not None else 0
            self.scale_max = scale_max if scale_max is not None else 5
            self.options = None
            self.option_keys = None
            self.current_value = self.scale_min
        
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
        if self.options is not None and self.option_keys is not None:
            # Return the option label corresponding to current value
            key = self.option_keys[self.current_value]
            return self.options.get(key, "")
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

        self.participant_id_entry = TextInput(hint_text="Participant ID", multiline=False, size_hint=(0.6, None), height=40, pos_hint={'center_x': 0.5})
        self.participant_id = 'Default'

        self.survey_data = pd.DataFrame(columns=['question', 'response'])
        self.app.survey_data = self.survey_data  # link to app-level survey data

        self.survey_json = None

        self.question_list = []
        self.question_metadata_list = []
        self.question_index = 0

        documents_path = pathlib.Path.home() / 'Documents'
        self.data_folder = documents_path / 'TouchCog' / 'Data'
        self.data_folder.mkdir(parents=True, exist_ok=True)

    def _record_response(self, question_text, response):
        """
        Append a response row to self.survey_data.
        response should be a string (or will be coerced to one).
        """
        try:
            # Coerce to string (empty string if None)
            resp_str = "" if response is None else str(response)
            self.survey_data.loc[len(self.survey_data)] = [question_text, resp_str]
        except Exception:
            # Best-effort: if pandas append fails, try concat
            try:
                new_row = pd.DataFrame([[question_text, "" if response is None else str(response)]], columns=self.survey_data.columns)
                self.survey_data = pd.concat([self.survey_data, new_row], ignore_index=True)
            except Exception:
                # give up silently (avoid crashing UI)
                pass

    def _should_question_be_visible(self, question_metadata):
        """
        Determine if a question should be visible based on:
        - visible: boolean flag (default behavior)
        - inclusions: list of conditions that make question visible if matched
        - exclusions: list of conditions that hide question if matched
        
        Logic:
        - If visible is false and inclusions match any condition, show the question
        - If visible is true but exclusions match any condition, hide the question
        - Otherwise, follow the visible flag
        
        Returns True if question should be displayed, False otherwise.
        """
        visible = question_metadata.get('visible', True)
        inclusions = question_metadata.get('inclusions', [])
        exclusions = question_metadata.get('exclusions', [])
        
        # Check inclusions: if any inclusion matches, question should be visible
        for inclusion in inclusions:
            if self._condition_matches(inclusion):
                return True
        
        # Check exclusions: if any exclusion matches, question should be hidden
        for exclusion in exclusions:
            if self._condition_matches(exclusion):
                return False
        
        # Default: follow the visible flag
        return visible

    def _condition_matches(self, condition):
        """
        Check if a condition (inclusion or exclusion) matches current survey responses.
        Condition structure: {
            'question_index': int,
            'question': str (optional),
            'response_value': str (the expected response)
        }
        
        Returns True if the condition matches, False otherwise.
        """
        try:
            question_index = condition.get('question_index')
            expected_value = condition.get('response_value')
            
            if question_index is None or expected_value is None:
                return False
            
            # Look for matching question in survey_data by index order
            # The question at question_index should have been recorded
            if question_index < len(self.question_list):
                # Get the question text from the question metadata
                question_metadata = self.question_metadata_list[question_index]
                question_text = question_metadata.get('text', '')
                
                # Find the response for this question in survey_data
                matching_rows = self.survey_data[self.survey_data['question'] == question_text]
                if not matching_rows.empty:
                    recorded_response = matching_rows.iloc[-1]['response']  # Get last recorded response
                    return recorded_response == expected_value
            
            return False
        except Exception:
            return False

    def _load_end_survey_text(self):
        self.end_survey_text = "Thank you for completing the survey!"
        self.end_survey_label = Label(text=self.end_survey_text, font_size='20sp', halign='center', valign='middle')
        self.end_survey_button = Button(text="Continue", size_hint=(0.5, 0.2), pos_hint={'center_x': 0.5})

    def _return_to_main_menu(self, instance):
        self.app.survey_data = self.survey_data
        self.app.survey_data.to_csv(self.app.survey_data_path, index=False)
        try:
            if getattr(self.app, 'battery_active', False):
				# delegate to MenuApp to advance and start next battery task
                if hasattr(self.app, 'battery_task_finished'):
                    self.app.battery_task_finished()
                    return
        except Exception:
			# best-effort: ignore failures here
            pass

        try:
            self.manager.current = 'mainmenu'
            return
        except Exception:
            pass

    def _create_multile_choice_question(self, layout, question_text, options):
        """
        Create a multiple choice question with given text and options.
        Handles "Other" option with text entry.
        """
        question_label = Label(text=question_text, size_hint_y=None, height=60)
        layout.add_widget(question_label)

        # Create scrollable container for options
        scroll_view = ScrollView(size_hint=(1, 0.7))
        options_container = BoxLayout(orientation='vertical', size_hint_y=None, spacing=10, padding=10)
        options_container.bind(minimum_height=options_container.setter('height'))

        # Track if "Other" option exists
        other_text_input = None
        
        # store selection state on the question layout
        layout.selected_choice = None
        # unique group per question so only one ToggleButton stays selected
        group_name = f"choice_group_{id(layout)}"

        for option in options:
            if option.lower() == "other":
                # Create horizontal layout for "Other" with a ToggleButton and text entry
                other_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=5)
                other_toggle = ToggleButton(text=option, group=group_name, size_hint_x=0.3)
                other_text_input = TextInput(multiline=False, size_hint_x=0.7, height=50)
                other_text_input.hint_text = "Specify other"
                # mark selection as 'Other' when toggle goes down
                def _mark_other(toggle, state, _layout=layout):
                    if state == 'down':
                        _layout.selected_choice = 'Other'
                other_toggle.bind(on_state=_mark_other)
                other_row.add_widget(other_toggle)
                other_row.add_widget(other_text_input)
                options_container.add_widget(other_row)
            else:
                option_toggle = ToggleButton(text=option, group=group_name, size_hint_y=None, height=50)
                # when toggled down, record this option label
                def _mark_choice(toggle, state, opt=option, _layout=layout):
                    if state == 'down':
                        _layout.selected_choice = opt
                option_toggle.bind(on_state=_mark_choice)
                options_container.add_widget(option_toggle)

        scroll_view.add_widget(options_container)
        layout.add_widget(scroll_view)

        survey_continue_button = Button(text="Next", size_hint_y=None, height=50)
        # custom handler: find the ToggleButton in the options_container that is down
        def _on_next(instance, qtext=question_text, _container=options_container, _other_input=other_text_input):
            selected_text = ""
            try:
                # options_container children may be ToggleButtons (for normal options) or BoxLayouts (for 'Other' rows)
                for child in _container.children:
                    # direct ToggleButton children
                    if isinstance(child, ToggleButton):
                        if child.state == 'down':
                            selected_text = child.text
                            break
                    # rows (e.g., BoxLayout) containing ToggleButton + TextInput
                    elif isinstance(child, BoxLayout):
                        for sub in child.children:
                            if isinstance(sub, ToggleButton) and sub.state == 'down':
                                if sub.text.lower() == 'other':
                                    # prefer the explicit other text input if present
                                    selected_text = _other_input.text if _other_input is not None else ""
                                else:
                                    selected_text = sub.text
                                break
                        if selected_text:
                            break
            except Exception:
                selected_text = ""

            response = selected_text if selected_text is not None else ""
            self._record_response(qtext, response)
            self.advance_survey()
        survey_continue_button.bind(on_press=_on_next)
        layout.add_widget(survey_continue_button)

        return layout

    def _create_text_input_question(self, layout, question_text):
        """
        Create a text input question with given text.
        """
        question_label = Label(text=question_text, size_hint_y=None, height=60)
        layout.add_widget(question_label)

        # Add spacer to push content up
        spacer = Widget(size_hint_y=0.3)
        layout.add_widget(spacer)

        from kivy.uix.textinput import TextInput
        text_input = TextInput(multiline=False, size_hint_y=None, height=50)
        layout.add_widget(text_input)

        survey_continue_button = Button(text="Next", size_hint_y=None, height=50)
        # custom handler: record the text value
        def _on_next_text(instance, qtext=question_text, _input=text_input):
            response = _input.text if _input is not None else ""
            self._record_response(qtext, response)
            self.advance_survey()
        survey_continue_button.bind(on_press=_on_next_text)
        layout.add_widget(survey_continue_button)

        return layout

    def _create_multi_response_question(self, layout, question_text, options):
        """
        Create a multi-response question with checkboxes for given text and options.
        Handles "Other" option with text entry instead of label.
        """
        question_label = Label(text=question_text, size_hint_y=None, height=60)
        layout.add_widget(question_label)

        # Create scrollable container for options
        scroll_view = ScrollView(size_hint=(1, 0.7))
        options_container = BoxLayout(orientation='vertical', size_hint_y=None, spacing=10, padding=10)
        options_container.bind(minimum_height=options_container.setter('height'))

        for option in options:
            if option.lower() == "other":
                # For "Other", replace label with text entry
                option_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=5)
                option_checkbox = CheckBox(size_hint_x=None, width=50)
                option_row.add_widget(option_checkbox)
                # Use the "Other" label as hint text in the entry field
                other_text_input = TextInput(multiline=False, hint_text=option, size_hint_x=1.0)
                option_row.add_widget(other_text_input)
                options_container.add_widget(option_row)
            else:
                option_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)
                option_checkbox = CheckBox(size_hint_x=None, width=50)
                option_row.add_widget(option_checkbox)
                option_label = Label(text=option, halign='left')
                option_row.add_widget(option_label)
                options_container.add_widget(option_row)

        scroll_view.add_widget(options_container)
        layout.add_widget(scroll_view)
        
        survey_continue_button = Button(text="Next", size_hint_y=None, height=50)
        # custom handler: iterate through rows and collect checked labels / text inputs
        def _on_next_multi(instance, qtext=question_text, _container=options_container):
            selected = []
            # options_container children are added top->bottom, but Kivy lays them out; iterate through children
            for row in _container.children:
                try:
                    # Expect row to be BoxLayout with first child a CheckBox and second a Label or TextInput
                    if len(row.children) >= 2:
                        # children order in a BoxLayout is reversed; find checkbox and input/label by type
                        cb = None
                        val_widget = None
                        for child in row.children:
                            if isinstance(child, CheckBox):
                                cb = child
                            elif isinstance(child, TextInput) or isinstance(child, Label):
                                val_widget = child
                        if cb and cb.active:
                            if isinstance(val_widget, TextInput):
                                txt = val_widget.text
                                if txt:
                                    selected.append(txt)
                            elif isinstance(val_widget, Label):
                                selected.append(val_widget.text)
                except Exception:
                    continue
            response = ", ".join(selected)
            self._record_response(qtext, response)
            self.advance_survey()
        survey_continue_button.bind(on_press=_on_next_multi)
        layout.add_widget(survey_continue_button)

        return layout

    def _create_rating_scale_question(self, layout, question_text, options):
        """
        Create a Likert scale question with a draggable horizontal indicator.
        Options can be either a dict {key: label, ...} or a tuple (min, max).
        """
        question_label = Label(text=question_text, size_hint_y=None, height=60)
        layout.add_widget(question_label)

        # Create a container for the scale with labels
        scale_container = BoxLayout(orientation='vertical', size_hint_y=None, height=150, spacing=5, padding=10)
        
        # Add the Likert scale widget
        if isinstance(options, dict):
            # New format: options dict with keys and labels
            likert_scale = LikertScale(options=options, size_hint_y=0.5)
            scale_container.add_widget(likert_scale)
            
            # Add label row with option labels
            label_row = BoxLayout(size_hint_y=0.5, spacing=5)
            option_values = list(options.values())
            num_options = len(option_values)
            
            for label_text in option_values:
                option_label = Label(text=label_text, size_hint_x=1.0 / num_options)
                label_row.add_widget(option_label)
            
            scale_container.add_widget(label_row)
        else:
            # Old format: numeric range (scale_min, scale_max)
            scale_min, scale_max = options[0], options[1]
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

        survey_continue_button = Button(text="Next", size_hint_y=None, height=50)
        # custom handler: read likert_scale value (label for dicts, numeric for ranges)
        def _on_next_scale(instance, qtext=question_text, _scale=likert_scale):
            try:
                response = _scale.get_value()
            except Exception:
                response = ""
            self._record_response(qtext, response)
            self.advance_survey()
        survey_continue_button.bind(on_press=_on_next_scale)
        layout.add_widget(survey_continue_button)

        return layout

    def create_question(self, question_text, options=None, question_type="multiple_choice"):
        """
        Create a survey question with given text and options.
        """
        # Create outer container with scroll view
        outer_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        question_layout = BoxLayout(orientation='vertical', padding=10, spacing=10, size_hint_y=None)
        question_layout.bind(minimum_height=question_layout.setter('height'))
        
        if question_type == "multiple_choice":
            # options should be a dict {key: label, ...}
            question_layout = self._create_multile_choice_question(question_layout, question_text, options.values() if isinstance(options, dict) else options)
        elif question_type == "text_input":
            question_layout = self._create_text_input_question(question_layout, question_text)
        elif question_type == "multi_response":
            # options should be a dict {key: label, ...}
            question_layout = self._create_multi_response_question(question_layout, question_text, options.values() if isinstance(options, dict) else options)
        elif question_type == "rating_scale":
            # options is now passed directly (dict or tuple)
            question_layout = self._create_rating_scale_question(question_layout, question_text, options)

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
        Stores metadata including visible, inclusions, and exclusions for each question.
        """
        self._load_end_survey_text()
        self.survey_json = survey_json
        for question in survey_json['questions']:
            q_text = question['text']
            q_type = question['type']
            q_options = question.get('options', None)
            q_visible = question.get('visible', True)
            q_inclusions = question.get('inclusions', [])
            q_exclusions = question.get('exclusions', [])
            
            # Create metadata dict for this question
            metadata = {
                'text': q_text,
                'type': q_type,
                'options': q_options,
                'visible': q_visible,
                'inclusions': q_inclusions,
                'exclusions': q_exclusions
            }
            
            # Store metadata
            self.question_metadata_list.append(metadata)
            
            # Create the question UI
            self.create_question(q_text, q_options, q_type)

    
    def advance_survey(self, *args):
        """
        Advance to the next question in the survey.
        Handles visibility logic: skips hidden questions and adds empty responses for them.
        """
        self.remove_question()
        self.question_index += 1
        
        # Loop through remaining questions to find the next visible one
        while self.question_index < len(self.question_list):
            question_metadata = self.question_metadata_list[self.question_index]
            
            # Check if this question should be visible
            if self._should_question_be_visible(question_metadata):
                # Display this visible question
                self._display_question(self.question_list[self.question_index])
                return
            else:
                # Question is hidden - record empty response and skip it
                question_text = question_metadata['text']
                self._record_response(question_text, "")
                self.question_index += 1
        
        # All remaining questions have been processed - survey is complete
        self.end_survey()

    def run_survey(self, *args):
        self.participant_id = self.participant_id_entry.text if self.participant_id_entry.text else 'Default'
        folder_path = pathlib.Path(self.data_folder, self.participant_id)
        folder_path.mkdir(parents=True, exist_ok=True)
        self.app.survey_data_path = str(folder_path / f"{self.name}.csv")
        self.main_layout.clear_widgets()
        
        # Start with question_index at -1 so advance_survey will move to 0
        self.question_index = -1
        # Use advance_survey to handle visibility logic from the start
        self.advance_survey()

    
    def _display_question(self, question_layout):
        """
        Display a question centered in the middle of the screen.
        """
        from kivy.uix.floatlayout import FloatLayout
        
        # Create a centered container
        container = FloatLayout()
        
        # Add question layout centered in the screen
        question_layout.size_hint = (0.8, 0.8)
        question_layout.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
        container.add_widget(question_layout)
        
        self.main_layout.add_widget(container)

    def start_screen(self):
        self.main_layout.clear_widgets()
        self.main_layout.add_widget(self.survey_title_label)
        self.main_layout.add_widget(self.survey_title_description)
        if not self.app.battery_active:
            self.main_layout.add_widget(self.participant_id_entry)
        self.main_layout.add_widget(self.survey_button)
        self.survey_button.bind(on_press=self.run_survey)

    def end_survey(self):
        self.main_layout.clear_widgets()
        self.main_layout.add_widget(self.end_survey_label)
        self.main_layout.add_widget(self.end_survey_button)
        self.end_survey_button.bind(on_press=self._return_to_main_menu)
