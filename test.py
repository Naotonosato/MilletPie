from multi_language_textinput import MultiLanguageTextInput

from kivy.app import App

class TestApp(App):
    def build(self):
        return MultiLanguageTextInput()

TestApp().run()