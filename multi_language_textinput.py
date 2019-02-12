from ctypes import windll,cdll
import ctypes
from kivy.app import App
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.resources import resource_add_path
from kivy.core.text import LabelBase,DEFAULT_FONT
from kivy.utils import platform
from kivy.base import EventLoop
from kivy.properties import StringProperty,ObjectProperty,NumericProperty,ListProperty
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.uix.behaviors import ButtonBehavior
from kivy.utils import escape_markup
from functools import partial

def set(family,*filenames):
    for f in filenames:
        try:
            LabelBase.register(family,f)
            break
        except:
            pass

if platform == 'win':
    resource_add_path('c:/Windows/Fonts')
    set(DEFAULT_FONT,'YuGothR.ttc')
    print(DEFAULT_FONT)

dll = cdll.LoadLibrary('./ime_operator.dll')

dll.getCandidate.restype = ctypes.c_char_p
dll.getComposition.restype = ctypes.c_char_p
dll.getEnterdString.restype = ctypes.c_char_p#POINTER(ctypes.c_char)

class TextInputIME(TextInput):

    composition_string = StringProperty()
    sdl_composition = StringProperty()
    composition_window = ObjectProperty()
    candidate_window = ObjectProperty()
    old_cursor_color = ListProperty()
    composition_cursor_index = NumericProperty()

    def __init__(self,**kwargs):
        
        super(TextInputIME,self).__init__(**kwargs)
        
        self.disable_on_textedit = (False,False)
        self.is_openIME = False
        self.old_cursor_color = self.cursor_color
        self.old_composition = ''
        
        EventLoop.window.bind(on_textedit=self._on_textedit)
    
    def _on_textedit(self,_,value):
        '''
        when there is nothing to be acquired,
        'getEnterdSting','getComposition','getCandidate'
        function returns '\n\n'.
        (It's because I think that IME will not returns '\n\n')
        
        valiable of value can only retains 
        about 15 charactors.
        
        But 'on_textedit' event is fired when size of composition
        string exceeds 15 too.
        
        So when fired the event,this function does
        processing such as acquistion candidates.

        返すべき値がないとき、
        'getEnterdSting','getComposition','getCandidate'
        これらの関数は、'\n\n'という文字列を返します。（IMEからこの文字列が
        取得されることがあるとは考えられないからです）

        なおSDL2の制約により、この関数の引数であるvalueには15文字程度以上
        は保持出来ません。しかし、texteditイベント自体は入力中の文字が15文字
        を超えても発火されるため、このイベントが呼ばれたタイミングで変換候補取得などの
        処理をしています。
        '''
        self.sdl_composition = value
        self.is_openIME = bool(dll.getIsOpenIME())


        try:
            entered_text = dll.getEnterdString().decode('cp932')
            composition_string = dll.getComposition().decode('cp932')
            candidates = dll.getCandidate().decode('cp932').split()
        except UnicodeError:
            print('failed to decode IME information')
            
        #data = [{'text':text,'on_release':partial(self.select_candidate,text)} for text in candidates.split()]
        #self.candidate_window.data = data
        
        raw_text = '\n'.join([f'[ref={i}]' + i + '[/ref]' for i in candidates])
        escaped_text = '\n'.join([f'[ref={escape_markup(i)}]' + escape_markup(i) + '[/ref]' for i in candidates])

        self.candidate_window.raw_text = raw_text
        self.candidate_window.escaped_text = escaped_text
        self.candidate_window.text = escaped_text

        self.composition_string = composition_string if composition_string != '\n\n' else ''

        if entered_text != '\n\n' and self.is_openIME and self.old_composition != value:
            
            index = self.cursor_index()
            self.text = self.text[:index-1] + entered_text + self.text[index:]
            self.composition_string = ''
            self.old_composition = value
            return None
        
        self.old_composition = value
        
    def insert_text(self,substring,from_undo=False):
        
        if substring == self.sdl_composition:
            return None
        else:
            return super(TextInputIME,self).insert_text(substring,from_undo)

    def keyboard_on_key_down(self, window, keycode, text, modifiers,dt=0):
        
        cursor_operations = {'left','up','right','down','backspace','tab'}
        self.composition_cursor_index = len(self.composition_string)

        if keycode[1] == 'left':
            self.composition_cursor_index -= 1
            
        if keycode[1] == 'right':
            self.composition_cursor_index += 1
            


        if keycode[1] in cursor_operations and self.composition_string:
            return None

        return super(TextInputIME,self).keyboard_on_key_down(window, keycode, text, modifiers)

    def on_composition_string(self,_,value):

        if self.composition_string:
            self.cursor_color = (0,0,0,0)
        else:
            self.cursor_color = self.old_cursor_color
        
        if not dll.getIsOpenIME():
            return
        
        #this is to underline text.
        #下線を引くための処理です。
        #https://kivy.org/doc/stable/api-kivy.core.text.markup.html
        self.composition_window.text = '[u]' + value + '[/u]'

    def select_candidate(self,text):
    
        self.focus = True
        self.readonly = False
        text = text.encode('cp932')
        text = ctypes.create_string_buffer(text)
        dll.setComposition(text)
        

class CandidateLabel(Label):

    raw_text = StringProperty()
    escaped_text = StringProperty()
    textinput = ObjectProperty()

    
    def on_touch_down(self,touch):
        
        super(CandidateLabel,self).on_touch_down(touch)
        self.textinput.focus = True
        self.textinput.readonly = False
        
    def on_ref_press(self,text):
        
        self.textinput.focus = True
        self.textinput.readonly = False
        text = text.replace('&amp;','&').replace('&bl;','[').replace('&br;',']')
        self.textinput.select_candidate(text)
    

class CompositionLabel(Label):
    
    textinput = ObjectProperty()

    def __init__(self,**kwargs):

        super(CompositionLabel,self).__init__(**kwargs)
        
        '''
        It's implemenintg these in the guture.
        drawin cursor in the composition window
        '''

        #self.drawing_cursor_event = Clock.schedule_interval(self.draw_cursor,0.1)
        #self.cursor_drawed = False


class MultiLanguageTextInput(FloatLayout):
    pass

candidate_window_kv = """
<CandidateLabel>:
    markup: True
    color: 0,0,0,1
"""
composition_window_kv = r"""
<CompositionLabel>:
    size_hint_x: None
    size_hint_y: None
    width: self.font_size * (len(self.text)-7)
    height: self.font_size 
    color: 0,0,0,1
    markup: True
    canvas.before:
        Color: 
            rgba: 1,1,1,len(self.text)-7
        Rectangle:
            pos: self.pos
            size: self.size
"""
multi_language_textinput_kv = r"""
<MultiLanguageTextInput>:
    candidate_font_size: textinput.font_size
    composition_font_size: textinput.font_size

    TextInputIME:
        id: textinput
        font_size: dp(50)
        composition_window: cmp_window
        candidate_window: cand_window
        pos: root.pos
        size: root.size 
    CompositionLabel:
        id: cmp_window
        textinput: textinput
        font_size: root.composition_font_size
        x: textinput.cursor_pos[0]
        y: textinput.cursor_pos[1] - self.height
    CandidateLabel:
        id: cand_window
        textinput: textinput
        pos_hint_x: None
        pos_hint_y: None
        font_size: root.candidate_font_size
        x: cmp_window.x
        y: (textinput.cursor_pos[1] - textinput.height) - self.font_size * self.text.count('\n')
"""
Builder.load_string(candidate_window_kv)
Builder.load_string(composition_window_kv)
Builder.load_string(multi_language_textinput_kv)

if __name__ == '__main__':

    class TestApp(App):
        def build(self):
            root = BoxLayout()
            root.add_widget(MultiLanguageTextInput())
            return root
   
    TestApp().run()