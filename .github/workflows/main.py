from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.animation import Animation
from kivy.properties import NumericProperty, StringProperty, BooleanProperty
from kivy.clock import Clock
from kivy.metrics import sp, dp
from kivy.utils import platform
from kivy.core.window import Window  # Добавляем импорт Window
import random

# Конфигурация для Android
if platform == 'android':
    from android.runnable import run_on_ui_thread
    from jnius import autoclass

class MainMenuScreen(Screen):
    pass

class GameScreen(Screen):
    pass

class AnimatedButton(Button):
    scale = NumericProperty(1)
    
    def on_press(self):
        anim = Animation(scale=0.95, duration=0.1) + Animation(scale=1, duration=0.1)
        anim.start(self)

class TicTacToeApp(App):
    current_player = StringProperty('X')
    game_active = BooleanProperty(True)
    player_x_score = NumericProperty(0)
    player_o_score = NumericProperty(0)
    ties = NumericProperty(0)
    game_mode = StringProperty('friend')
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.board = ['' for _ in range(9)]
    
    def build(self):
        # Настройка для Android
        if platform == 'android':
            self.disable_android_gestures()
        
        self.sm = ScreenManager()
        
        # Главное меню
        menu_screen = MainMenuScreen(name='menu')
        menu_layout = BoxLayout(orientation='vertical', padding=dp(30), spacing=dp(20))
        
        title_label = Label(
            text='[b]Крестики-нолики[/b]',
            font_size=sp(36),
            markup=True,
            size_hint=(1, 0.3)
        )
        menu_layout.add_widget(title_label)
        
        mode_label = Label(
            text='Выберите режим игры:',
            font_size=sp(22),
            size_hint=(1, 0.2)
        )
        menu_layout.add_widget(mode_label)
        
        mode_layout = BoxLayout(orientation='vertical', spacing=dp(15), size_hint=(1, 0.5))
        
        vs_friend_btn = AnimatedButton(
            text='Играть с другом',
            font_size=sp(20),
            background_color=(0.2, 0.6, 0.2, 1),
            background_normal='',
            size_hint_y=None,
            height=dp(60),
            on_press=lambda x: self.start_game('friend')
        )
        
        vs_ai_btn = AnimatedButton(
            text='Играть с ИИ',
            font_size=sp(20),
            background_color=(0.2, 0.4, 0.8, 1),
            background_normal='',
            size_hint_y=None,
            height=dp(60),
            on_press=lambda x: self.start_game('ai')
        )
        
        mode_layout.add_widget(vs_friend_btn)
        mode_layout.add_widget(vs_ai_btn)
        menu_layout.add_widget(mode_layout)
        
        menu_screen.add_widget(menu_layout)
        self.sm.add_widget(menu_screen)
        
        # Экран игры
        self.game_screen = GameScreen(name='game')
        self.sm.add_widget(self.game_screen)
        
        # Обработка кнопки "Назад" на Android
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)
        
        return self.sm
    
    def disable_android_gestures(self):
        """Отключает системные жесты на Android"""
        try:
            @run_on_ui_thread
            def disable_gestures():
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                View = autoclass('android.view.View')
                
                activity = PythonActivity.mActivity
                window = activity.getWindow()
                decor_view = window.getDecorView()
                
                # Скрываем панель навигации
                flags = (View.SYSTEM_UI_FLAG_HIDE_NAVIGATION | 
                        View.SYSTEM_UI_FLAG_FULLSCREEN |
                        View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY)
                decor_view.setSystemUiVisibility(flags)
            
            disable_gestures()
        except Exception as e:
            print(f"Не удалось отключить жесты: {e}")
    
    def _keyboard_closed(self):
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None
    
    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        """Обработка кнопки Назад на Android"""
        if keycode[1] == 'escape' or keycode[1] == 'backspace':
            if self.sm.current == 'game':
                self.back_to_menu()
                return True
        return False

    def start_game(self, mode):
        self.game_mode = mode
        self.reset_game()
        self.sm.current = 'game'
        self.build_game_screen()
    
    def build_game_screen(self):
        self.game_screen.clear_widgets()
        
        main_layout = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(10))
        
        # Верхняя панель
        top_panel = BoxLayout(orientation='horizontal', size_hint=(1, 0.12), spacing=dp(10))
        
        back_btn = Button(
            text='← Меню',
            font_size=sp(16),
            size_hint=(0.25, 1),
            background_color=(0.5, 0.5, 0.5, 1),
            background_normal='',
            on_press=self.back_to_menu
        )
        
        mode_info = Label(
            text=f'Режим: {"с другом" if self.game_mode == "friend" else "с ИИ"}',
            font_size=sp(16),
            halign='center'
        )
        
        self.score_label = Label(
            text=f"X: {self.player_x_score} | O: {self.player_o_score} | Ничьи: {self.ties}",
            font_size=sp(14),
            halign='right'
        )
        
        top_panel.add_widget(back_btn)
        top_panel.add_widget(mode_info)
        top_panel.add_widget(self.score_label)
        main_layout.add_widget(top_panel)
        
        # Статус игры
        self.status_label = Label(
            text=self.get_status_text(),
            font_size=sp(20),
            markup=True,
            size_hint=(1, 0.1)
        )
        main_layout.add_widget(self.status_label)
        
        # Игровое поле
        self.game_grid = GridLayout(cols=3, rows=3, spacing=dp(5), size_hint=(1, 0.6))
        self.buttons = []
        
        for i in range(9):
            btn = AnimatedButton(
                text='',
                font_size=sp(42),
                background_color=(0.15, 0.15, 0.15, 1),
                background_normal='',
                on_press=lambda instance, pos=i: self.make_move(instance, pos)
            )
            self.buttons.append(btn)
            self.game_grid.add_widget(btn)
        
        main_layout.add_widget(self.game_grid)
        
        # Панель управления
        control_layout = BoxLayout(orientation='horizontal', spacing=dp(5), size_hint=(1, 0.15))
        
        new_game_btn = Button(
            text='Новая игра',
            font_size=sp(18),
            background_color=(0.2, 0.7, 0.3, 1),
            background_normal='',
            on_press=self.reset_game
        )
        
        if self.game_mode == 'ai':
            ai_move_btn = Button(
                text='Ход ИИ',
                font_size=sp(18),
                background_color=(0.3, 0.5, 0.8, 1),
                background_normal='',
                on_press=self.make_ai_move
            )
            control_layout.add_widget(ai_move_btn)
        
        control_layout.add_widget(new_game_btn)
        main_layout.add_widget(control_layout)
        
        self.game_screen.add_widget(main_layout)
        
        if self.game_mode == 'ai' and self.current_player == 'O':
            Clock.schedule_once(lambda dt: self.make_ai_move(), 0.5)

    def get_status_text(self):
        if self.game_mode == 'friend':
            color = "ff5555" if self.current_player == 'X' else "5555ff"
            return f"[b]Ходит игрок:[/b] [color={color}]{self.current_player}[/color]"
        else:
            if self.current_player == 'X':
                return "[b]Ваш ход[/b] [color=ff5555](X)[/color]"
            else:
                return "[b]Ходит ИИ[/b] [color=5555ff](O)[/color]"
    
    def make_move(self, button, position):
        if not self.game_active or self.board[position] != '':
            return
        
        button.text = self.current_player
        self.board[position] = self.current_player
        
        if self.current_player == 'X':
            button.background_color = (0.8, 0.2, 0.2, 1)
        else:
            button.background_color = (0.2, 0.2, 0.8, 1)
        
        anim = Animation(font_size=sp(48), duration=0.2) + Animation(font_size=sp(42), duration=0.1)
        anim.start(button)
        
        self.check_game_result()
    
    def make_ai_move(self, instance=None):
        if not self.game_active or self.current_player != 'O' or self.game_mode != 'ai':
            return
        
        available_moves = [i for i, cell in enumerate(self.board) if cell == '']
        if available_moves:
            move = self.find_winning_move('O')
            if move is None:
                move = self.find_winning_move('X')
            if move is None:
                move = self.take_center()
            if move is None:
                move = self.take_corner()
            if move is None:
                move = random.choice(available_moves)
            
            Clock.schedule_once(lambda dt: self.execute_ai_move(move), 0.7)
    
    def execute_ai_move(self, position):
        if self.game_active and self.board[position] == '':
            self.make_move(self.buttons[position], position)
    
    def find_winning_move(self, player):
        for i in range(9):
            if self.board[i] == '':
                self.board[i] = player
                if self.check_winner() == player:
                    self.board[i] = ''
                    return i
                self.board[i] = ''
        return None
    
    def take_center(self):
        return 4 if self.board[4] == '' else None
    
    def take_corner(self):
        corners = [0, 2, 6, 8]
        available_corners = [c for c in corners if self.board[c] == '']
        return random.choice(available_corners) if available_corners else None
    
    def check_game_result(self):
        winner = self.check_winner()
        
        if winner:
            self.game_active = False
            self.show_winner_popup(winner)
            self.update_score(winner)
            self.highlight_winning_line()
        elif all(cell != '' for cell in self.board):
            self.game_active = False
            self.show_tie_popup()
            self.ties += 1
            self.update_score_display()
        else:
            self.current_player = 'O' if self.current_player == 'X' else 'X'
            self.status_label.text = self.get_status_text()
            
            if self.game_mode == 'ai' and self.current_player == 'O':
                Clock.schedule_once(lambda dt: self.make_ai_move(), 0.3)
    
    def check_winner(self):
        lines = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],
            [0, 3, 6], [1, 4, 7], [2, 5, 8],
            [0, 4, 8], [2, 4, 6]
        ]
        
        for line in lines:
            if self.board[line[0]] == self.board[line[1]] == self.board[line[2]] != '':
                return self.board[line[0]]
        return None
    
    def highlight_winning_line(self):
        lines = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],
            [0, 3, 6], [1, 4, 7], [2, 5, 8],
            [0, 4, 8], [2, 4, 6]
        ]
        
        for line in lines:
            if self.board[line[0]] == self.board[line[1]] == self.board[line[2]] != '':
                for pos in line:
                    anim = Animation(background_color=(0, 1, 0, 0.7), duration=0.5)
                    anim.start(self.buttons[pos])
                break
    
    def show_winner_popup(self, winner):
        if self.game_mode == 'friend':
            message = f'Игрок [color=ff5555]{winner}[/color] побеждает!' if winner == 'X' else f'Игрок [color=5555ff]{winner}[/color] побеждает!'
        else:
            if winner == 'X':
                message = '[color=00ff00]Вы победили![/color] 🎉'
            else:
                message = '[color=ff0000]ИИ победил![/color] 🤖'
        
        self.show_popup('Игра окончена!', message)
    
    def show_tie_popup(self):
        self.show_popup('Игра окончена!', 'Ничья! 🤝')
    
    def show_popup(self, title, message):
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(20))
        
        message_label = Label(
            text=message,
            font_size=sp(22),
            markup=True
        )
        
        button_layout = BoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=0.4)
        
        menu_btn = Button(
            text='В меню',
            font_size=sp(18),
            background_color=(0.5, 0.5, 0.5, 1)
        )
        
        again_btn = Button(
            text='Играть ещё',
            font_size=sp(18),
            background_color=(0.2, 0.7, 0.3, 1)
        )
        
        menu_btn.bind(on_press=lambda x: (popup.dismiss(), self.back_to_menu()))
        again_btn.bind(on_press=lambda x: (popup.dismiss(), self.reset_game()))
        
        button_layout.add_widget(menu_btn)
        button_layout.add_widget(again_btn)
        
        content.add_widget(message_label)
        content.add_widget(button_layout)
        
        popup = Popup(
            title=title,
            content=content,
            size_hint=(0.8, 0.5),
            auto_dismiss=False
        )
        popup.open()
    
    def update_score(self, winner):
        if winner == 'X':
            self.player_x_score += 1
        else:
            self.player_o_score += 1
        self.update_score_display()
    
    def update_score_display(self):
        self.score_label.text = f"X: {self.player_x_score} | O: {self.player_o_score} | Ничьи: {self.ties}"
    
    def reset_game(self, instance=None):
        self.board = ['' for _ in range(9)]
        self.game_active = True
        self.current_player = 'X'
        
        if hasattr(self, 'buttons'):
            for button in self.buttons:
                button.text = ''
                button.background_color = (0.15, 0.15, 0.15, 1)
                button.font_size = sp(42)
        
        if hasattr(self, 'status_label'):
            self.status_label.text = self.get_status_text()
        
        if self.game_mode == 'ai' and self.current_player == 'O':
            Clock.schedule_once(lambda dt: self.make_ai_move(), 0.5)
    
    def back_to_menu(self, instance=None):
        self.sm.current = 'menu'

if __name__ == '__main__':
    TicTacToeApp().run()
