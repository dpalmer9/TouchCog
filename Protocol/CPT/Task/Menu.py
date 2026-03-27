from Classes.Menu import MenuBase, ImageSetDropdown, ImageSetItem, dp
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.dropdown import DropDown
from kivy.uix.checkbox import CheckBox

class ConfigureScreen(MenuBase):
    def __init__(self, **kwargs):
        super(ConfigureScreen, self).__init__(**kwargs)

        self.protocol = 'CPT'
        self.protocol_name = 'Continuous Performance Task'
        self.protocol_title_label.text = self.protocol_name
        self.name = self.protocol + '_configscreen'
        sim_config = False

        self.image_set_similarity_targets = [{'label': 'Target 1', 
                                              'images': [f'{self.app.app_root}/Protocol/CPT/Image/Fribbles/Fb/Fb2_1132.png'], 
                                              'value': 'Fb2_1132'},
                                              {'label': 'Target 2', 
                                              'images': [f'{self.app.app_root}/Protocol/CPT/Image/Fribbles/Fb/Fb2_1211.png'], 
                                              'value': 'Fb2_1211'},
                                              {'label': 'Target 3', 
                                              'images': [f'{self.app.app_root}/Protocol/CPT/Image/Fribbles/Fb/Fb2_1221.png'], 
                                              'value': 'Fb2_1221'},
                                              {'label': 'Target 4', 
                                              'images': [f'{self.app.app_root}/Protocol/CPT/Image/Fribbles/Fb/Fb2_1312.png'], 
                                              'value': 'Fb2_1312'},
                                              {'label': 'Target 5', 
                                              'images': [f'{self.app.app_root}/Protocol/CPT/Image/Fribbles/Fb/Fb2_1322.png'], 
                                              'value': 'Fb2_1322'},
                                              {'label': 'Target 6', 
                                              'images': [f'{self.app.app_root}/Protocol/CPT/Image/Fribbles/Fb/Fb2_1332.png'], 
                                              'value': 'Fb2_1332'},
                                              {'label': 'Random', 
                                              'images': [], 
                                              'value': 'set7'}
                                              ]
        
        self.image_set_standard = [{'label': 'Image Set 1',
                                    'images': [f'{self.app.app_root}/Protocol/CPT/Image/Fribbles/Blues/FA2-1.png',f'{self.app.app_root}/Protocol/CPT/Image/black.png',
                                               f'{self.app.app_root}/Protocol/CPT/Image/Fribbles/Blues/FA3-2.png',f'{self.app.app_root}/Protocol/CPT/Image/Fribbles/Blues/FB1-1.png',
                                               f'{self.app.app_root}/Protocol/CPT/Image/Fribbles/Blues/FB2-2.png',f'{self.app.app_root}/Protocol/CPT/Image/Fribbles/Blues/FC1-1.png'
                                               ,f'{self.app.app_root}/Protocol/CPT/Image/Fribbles/Blues/FC3-2.png'],
                                    'value': 'set1'},
                                    {'label': 'Image Set 2',
                                    'images': [f'{self.app.app_root}/Protocol/CPT/Image/Fribbles/Blues/FB2-3.png',f'{self.app.app_root}/Protocol/CPT/Image/black.png',
                                               f'{self.app.app_root}/Protocol/CPT/Image/Fribbles/Blues/FB3-1.png',f'{self.app.app_root}/Protocol/CPT/Image/Fribbles/Blues/FA2-2.png',
                                               f'{self.app.app_root}/Protocol/CPT/Image/Fribbles/Blues/FA4-1.png',f'{self.app.app_root}/Protocol/CPT/Image/Fribbles/Blues/FC2-2.png'
                                               ,f'{self.app.app_root}/Protocol/CPT/Image/Fribbles/Blues/FC4-2.png'],
                                    'value': 'set2'},
                                    {'label': 'Image Set 3',
                                    'images': [f'{self.app.app_root}/Protocol/CPT/Image/Fribbles/Blues/FC1-3.png',f'{self.app.app_root}/Protocol/CPT/Image/black.png',
                                               f'{self.app.app_root}/Protocol/CPT/Image/Fribbles/Blues/FC4-1.png',f'{self.app.app_root}/Protocol/CPT/Image/Fribbles/Blues/FA1-2.png',
                                               f'{self.app.app_root}/Protocol/CPT/Image/Fribbles/Blues/FA3-3.png',f'{self.app.app_root}/Protocol/CPT/Image/Fribbles/Blues/FB2-2.png'
                                               ,f'{self.app.app_root}/Protocol/CPT/Image/Fribbles/Blues/FB4-3.png'],
                                    'value': 'set3',
                                    },
                                    {'label': 'Random',
                                    'images': [],
                                    'value': 'rand',
                                    }
        ]

        self.cjb_image_set = [{'label': 'CJB Set 1',
                                    'images': [f'{self.app.app_root}/Protocol/CPT/Image/CJB/left 45.png', f'{self.app.app_root}/Protocol/CPT/Image/CJB/left 22.5.png',
                                               f'{self.app.app_root}/Protocol/CPT/Image/CJB/vert.png', f'{self.app.app_root}/Protocol/CPT/Image/CJB/right 22.5.png',
                                               f'{self.app.app_root}/Protocol/CPT/Image/CJB/right 45.png'],
                                    'value': 'cjb_set1'
                                    }
        ]

        # Defer creating the image selector until after the menu constructor
        # so we can inspect the dynamically created similarity_difficulty checkbox
        self.menu_constructor(self.protocol)

        # Try to find the similarity_difficulty checkbox that was created by menu_constructor if not in battery mode
        if not self.app.battery_active:
            sim_checkbox = None
            children = list(self.setting_gridlayout.children)
            for idx, w in enumerate(children):
                if isinstance(w, Label) and w.text == 'similarity_difficulty':
                    # GridLayout.children is in reverse-add order so the control should be at idx-1
                    if idx > 0 and isinstance(children[idx-1], CheckBox):
                        sim_checkbox = children[idx-1]
                    break
        # Else check the configuration file default for the similarity option as other widgets wont exist
        else:
            sim_checkbox = None
            sim_config = False
            sim_config = self.parameters_config.getboolean('similarity_difficulty')

        # Choose initial options based on the checkbox (default True if not found)
        if (sim_checkbox is None and sim_config) or (sim_checkbox.active):
            init_options = self.image_set_similarity_targets
        else:
            init_options = self.image_set_standard

        self.image_select_label = Label(text='Image Set')
        self.image_selector = ImageSetDropdown(init_options)
        self.cjb_select_label = Label(text='CJB Image Set')
        self.cjb_image_selector = ImageSetDropdown(self.cjb_image_set)

        self.setting_gridlayout.rows += 2
        self.setting_gridlayout.add_widget(self.image_select_label)
        self.setting_gridlayout.add_widget(self.image_selector)
        self.setting_gridlayout.add_widget(self.cjb_select_label)
        self.setting_gridlayout.add_widget(self.cjb_image_selector)

        # If the similarity checkbox exists, bind to changes to update the dropdown options
        if sim_checkbox is not None:
            def _on_similarity_toggle(instance, value):
                new_opts = self.image_set_similarity_targets if value else self.image_set_standard
                # replace options and rebuild dropdown items
                self.image_selector.options = new_opts
                try:
                    self.image_selector.dropdown.clear_widgets()
                except Exception:
                    pass
                for opt in self.image_selector.options:
                    label = opt.get('label', '')
                    images = opt.get('images', [])
                    val = opt.get('value', label)
                    item = ImageSetItem(label_text=label, image_paths=images, dropdown=self.image_selector.dropdown, value=val, thumb_size=self.image_selector.thumb_size, size_hint_y=None, height=self.image_selector.thumb_size + dp(12))
                    self.image_selector.dropdown.add_widget(item)
                # reset selection/display
                self.image_selector.selected_value = None
                self.image_selector.button.text = 'Select...'

            sim_checkbox.bind(active=_on_similarity_toggle)
        # If the cjb_training_task, cjb_discrimination_task, cjb_probe_var1_task, or cjb_probe_var2_task parameters are toggled on, add the CJB image set as an option
        # Conduct initial check to see if cjb task values are true and set the default state for the dropdown
        cjb_task_list = ['cjb_training_task', 'cjb_discrimination_task', 'cjb_probe_var1_task', 'cjb_probe_var2_task']
        cjb_bool_values = [self.parameters_config.getboolean(param) for param in cjb_task_list]
        if not any(cjb_bool_values):
            # Disable the cjb image selector if no CJB tasks are active
            self.cjb_image_selector.disabled = True
            
        def _on_cjb_task_toggle(instance, value):
            if value:
                # Make cjb image selector active if any CJB task is active
                self.cjb_image_selector.disabled = False
            else:
                # check if any other CJB tasks are still active by walking through the checkboxes again
                any_cjb_active = False
                for idx, w in enumerate(children):
                    if isinstance(w, Label) and w.text in cjb_task_list:
                        if idx > 0 and isinstance(children[idx-1], CheckBox):
                            if children[idx-1].active:
                                any_cjb_active = True
                                break
                if not any_cjb_active:
                    self.cjb_image_selector.disabled = True

        # Search through the layout for any checkboxes related to CJB tasks and bind them to update the image selector options when toggled
        if not self.app.battery_active:
            for idx, w in enumerate(children):
                    if isinstance(w, Label) and w.text in cjb_task_list:
                        # GridLayout.children is in reverse-add order so the control should be at idx-1
                        if idx > 0 and isinstance(children[idx-1], CheckBox):
                            cjb_checkbox = children[idx-1]
                            cjb_checkbox.bind(active=_on_cjb_task_toggle)


    def update_image_widget(self):
         # Try to find the similarity_difficulty checkbox that was created by menu_constructor if not in battery mode
        if not self.app.battery_active:
            sim_checkbox = None
            children = list(self.setting_gridlayout.children)
            for idx, w in enumerate(children):
                if isinstance(w, Label) and w.text == 'similarity_difficulty':
                    # GridLayout.children is in reverse-add order so the control should be at idx-1
                    if idx > 0 and isinstance(children[idx-1], CheckBox):
                        sim_checkbox = children[idx-1]
                    break
        # Else check the configuration file default for the similarity option as other widgets wont exist
        else:
            sim_checkbox = None
            sim_config = False
            sim_config = self.parameters_config.getboolean('similarity_difficulty')
        
        # Choose initial options based on the checkbox (default True if not found)
        if (sim_checkbox is None and sim_config) or (sim_checkbox is not None and sim_checkbox.active):
            init_options = self.image_set_similarity_targets
        else:
            init_options = self.image_set_standard
        # Change the options and rebuild dropdown items
        self.image_selector.options = init_options
        try:
            self.image_selector.dropdown.clear_widgets()
        except Exception:
            pass
        for opt in self.image_selector.options:
            label = opt.get('label', '')
            images = opt.get('images', [])
            val = opt.get('value', label)
            item = ImageSetItem(label_text=label, image_paths=images, dropdown=self.image_selector.dropdown, value=val, thumb_size=self.image_selector.thumb_size, size_hint_y=None, height=self.image_selector.thumb_size + dp(12))
            self.image_selector.dropdown.add_widget(item)
        # reset selection/display
        self.image_selector.selected_value = None
        self.image_selector.button.text = 'Select...'

