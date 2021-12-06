from PIL import Image, ImageDraw, ImageTk, ImageFont
from state import State, Move
from mcts import get_mcts_move
import tkinter as tk
import numpy as np
import random

WHITE = 0
BLACK = 1
NONE = 2

BAR = -1
BEARED_OFF_WHITE = -1
BEARED_OFF_BLACK = 24

class LastMove:
    def __init__(self, move, turn: int):
        self.move = move
        self.turn = turn

class TkApp(tk.Tk):
    def __init__(self, interface):
        super().__init__()
        self.interface = interface
        self.canvas = tk.Canvas(self, height=self.interface.ysize, width=self.interface.xsize)
        self.canvas.bind('<Button-1>', self.on_canvas_click)
        self.canvas.grid(row=0, column=0)
        self.frame = tk.Frame(self)
        self.button = tk.Button(self.frame, command=self.reset_game, text="Reset game")
        self.button.grid(row=0, column=0)
        self.button2 = tk.Button(self.frame, command=self.do_one_move, text="Next move")
        self.button2.grid(row=0, column=1)
        self.button3 = tk.Button(self.frame, command=self.simulated_game, text="Simulated Game")
        self.button3.grid(row=0, column=2)
        self.frame.grid(row=1, column=0)

        self.reset_game()

    def reset_game(self):
        self.interface.reset_state()
        self.state = State()
        self.update_interface()
    
    def do_move(self, move):
        if not self.state.game_ended():
            self.state.do_move(move)
            turn = self.state.get_player_turn()
            self.interface.set_player_turn(turn)
            if move.is_movement_move:
                self.interface.set_last_move(move, turn)
            elif not move.is_movement_move:
                self.interface.set_last_dice_rolls(move)
        self.update_interface()

    def do_one_ply(self):
        start_players_turn = self.state.get_player_turn()
        while not self.state.game_ended() and self.state.get_player_turn() == start_players_turn:
            self.do_one_move()

    def do_one_move(self):
        if not self.state.game_ended():
            moves = self.state.get_moves()
            if self.state.is_nature_turn():
                move = random.choice(moves)
            else:
                move = get_mcts_move(self.state, 2.0)
            self.do_move(move)

    def on_canvas_click(self, e):
        (x, y) = (e.x, e.y)
        self.interface.handle_click_event(x, y)
        if self.interface.has_suggested_move():
            suggested_move = self.interface.get_suggested_move()
            move_hashes = [hash(move) for move in self.state.get_moves()]
            if hash(suggested_move) in move_hashes:
                self.do_move(suggested_move)
            self.interface.clear_suggested_move()
        self.update_interface()
    
    def simulated_game(self):
        self.state = State()

        while not self.state.game_ended():
            moves = self.state.get_moves()
            if self.state.is_nature_turn():
                move = random.choice(moves)
            else:
                move = get_mcts_move(self.state, 2.0)
            self.do_move(move)

    def update_interface(self):
        self.interface.set_is_nature_turn(self.state.is_nature_turn())
        self.im = self.interface.get_img_from_state(self.state)
        self.photoimage = ImageTk.PhotoImage(self.im)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photoimage)
        self.canvas.update()

class Interface:
    baige = (225,225,200)
    dark_baige = (180,180,165)
    brown = (166, 42, 42)
    grey = (169, 169, 169)
    dark_grey = (84, 84, 84)
    white = (255, 255, 255)
    black = (0, 0, 0)
    green = (0, 128, 0)
    light_green = (0, 192, 0)
    dark_green = (0, 92, 0)
    blue = (0, 0, 128)
    yellow = (160, 160, 0)
    dark_yellow = (96, 96, 0)
    ratio = 4.57
    piece_distance = 5
    piece_size_scale = 0.5
    centre_distance = 50
    movement_rectangle_width = 4
    point_text_font = ImageFont.truetype("NotoSerif-Black.ttf", 20)
    dice_text_font = ImageFont.truetype("NotoSerif-Black.ttf", 40)
    player_turn_font = ImageFont.truetype("NotoSerif-Black.ttf", 30)
    piece_text_font = ImageFont.truetype("NotoSerif-Black.ttf", 18)

    base = (80, 650)
    base_size = 50

    max_pieces_per_point = 6

    def __init__(self):
        self.xsize = 800
        self.ysize = 650
        self.last_move = None
        self.player_turn = NONE
        self.last_dice_rolls = [0, 0]
        self.selected_point = None
        self.suggested_move = None
        self.is_nature_turn = True

    def reset_state(self):
        self.last_move = None
        self.player_turn = NONE
        self.last_dice_rolls = [0, 0]
        self.selected_point = None
        self.suggested_move = None
        self.is_nature_turn = True

    def handle_click_event(self, x, y):
        point = self.get_selected_point(x, y)
        if self.selected_point is not None:
            (src, dst) = (self.selected_point, point)
            if src == BAR:
                src = -1 if self.player_turn == BLACK else 24
            self.selected_point = None
            self.suggested_move = Move()
            self.suggested_move.is_movement_move = True
            self.suggested_move.src = src
            self.suggested_move.dst = dst
            self.suggested_move.n = abs(src - dst)
        else:
            if point is None:
                self.selected_point = None
                self.suggested_move = None
            else:
                self.selected_point = point
                self.suggested_move = None

    def set_is_nature_turn(self, is_nature_turn: bool):
        self.is_nature_turn = is_nature_turn

    def get_suggested_move(self):
        return self.suggested_move

    def clear_suggested_move(self):
        self.suggested_move = None

    def has_suggested_move(self):
        return self.suggested_move is not None

    def get_selected_point(self, x, y):
        for point in range(24):
            if self.is_point_in_point(x, y, point):
                return point
        if self.is_point_on_bar(x, y):
            return BAR
        elif self.is_point_on_black_bear_off(x, y):
            return BEARED_OFF_BLACK
        elif self.is_point_on_white_bear_off(x, y):
            return BEARED_OFF_WHITE
        return None

    def is_point_in_point(self, x, y, point):
        xy = self.point_to_xy(Interface.base, Interface.base_size, point)
        if self.point_is_flipped(point):
            return (x > xy[0] - Interface.base_size // 2 and y > xy[1] and x < xy[0] + Interface.base_size // 2 and y < round(xy[1] + Interface.ratio * Interface.base_size))
        else:
            return (x < xy[0] + Interface.base_size // 2 and y > round(xy[1] - Interface.ratio * Interface.base_size) and 
                    x > (xy[0] - Interface.base_size // 2) and y < xy[1] - Interface.base_size)

    def is_point_on_black_bear_off(self, x, y):
        return (x > Interface.base[0] - Interface.base_size * 1.5 and y < Interface.base[1] - Interface.base_size and x < Interface.base[0] - Interface.base_size * 0.5 and 
                y > Interface.base[1] - round(Interface.ratio * Interface.base_size) * 2 - Interface.centre_distance)

    def is_point_on_bar(self, x, y):
        return (x > Interface.base[0] + Interface.base_size * 6 and y < Interface.base[1] - Interface.base_size and x < Interface.base[0] + Interface.base_size * 7 and 
                y > Interface.base[1] - round(Interface.ratio * Interface.base_size) * 2 - Interface.centre_distance)

    def is_point_on_white_bear_off(self, x, y):
        return (x > Interface.base[0] + Interface.base_size * 13.5 and y < Interface.base[1] - Interface.base_size and x < Interface.base[0] * 14.5 and 
                y > Interface.base[1] - round(Interface.ratio * Interface.base_size) * 2 - Interface.centre_distance)

    def set_player_turn(self, player):
        self.player_turn = player

    def set_last_move(self, move, turn):
        self.last_move = LastMove(move, turn)

    def set_last_dice_rolls(self, move):
        self.last_dice_rolls = [move.i, move.j]

    def get_img_from_state(self, state: State):
        im = Image.new('RGB', (self.xsize, self.ysize), color=Interface.dark_baige)
        draw = ImageDraw.Draw(im)
        last_move = self.last_move
        self.draw_mat(draw, Interface.base, Interface.base_size)
        self.draw_state(draw, Interface.base, Interface.base_size, state)

        if last_move is not None:
            assert last_move.move.is_movement_move, last_move.move.is_movement_move
            self.draw_movement_move(draw, Interface.base, Interface.base_size, last_move)
        self.draw_dice(draw, Interface.base, Interface.base_size, self.last_dice_rolls[0], self.last_dice_rolls[1])
        self.draw_player_turn(draw, Interface.base, Interface.base_size)
        if self.selected_point is not None:
            if self.selected_point == BAR:
                self.draw_rectangle_around_bar(draw, (Interface.base[0] + Interface.base_size * 6.5, Interface.base[1]), 
                                               Interface.base_size, Interface.black)
            elif self.selected_point == BEARED_OFF_BLACK:
                self.draw_rectangle_around_bar(draw, (Interface.base[0] - Interface.base_size, Interface.base[1]), 
                                               Interface.base_size, Interface.black)
            elif self.selected_point == BEARED_OFF_WHITE:
                self.draw_rectangle_around_bar(draw, (Interface.base[0] + Interface.base_size * 14, Interface.base[1]), 
                                               Interface.base_size, Interface.black)
            else:
                self.draw_rectangle_around_point(draw, Interface.base, Interface.base_size, self.selected_point, Interface.black)
        return im
    
    def draw_rectangle_around_bar(self, draw: ImageDraw.Draw, base: tuple, base_size: int, color: tuple):
        draw.rectangle([(base[0] - base_size // 2, base[1] - base_size),
                (base[0] + base_size // 2, base[1] - round(Interface.ratio * base_size) * 2 - Interface.centre_distance)],
                outline=color, width=4)

    def draw_dice(self, draw: ImageDraw.Draw, base: tuple, base_size: int, roll1: int, roll2: int):
        if self.is_nature_turn:
            roll1 = "?"
            roll2 = "?"
        draw.rectangle([(base[0] - base_size * 0.5, base[1] - round(Interface.ratio * base_size) * 2 - Interface.centre_distance - base_size * 2),
                        (base[0] + base_size * 0.5, base[1] - round(Interface.ratio * base_size) * 2 - Interface.centre_distance - base_size)],
                        outline=Interface.black, width=4)
        draw.text((base[0], base[1] - round(Interface.ratio * base_size) * 2 - Interface.centre_distance - base_size * 1.5),
                  "{}".format(roll1), font=Interface.dice_text_font, fill=Interface.black, anchor="mm")

        draw.rectangle([(base[0] + base_size * 0.5, base[1] - round(Interface.ratio * base_size) * 2 - Interface.centre_distance - base_size * 2),
                        (base[0] + base_size * 1.5, base[1] - round(Interface.ratio * base_size) * 2 - Interface.centre_distance - base_size)],
                        outline=Interface.black, width=4)
        draw.text((base[0] + base_size, base[1] - round(Interface.ratio * base_size) * 2 - Interface.centre_distance - base_size * 1.5),
                  "{}".format(roll2), font=Interface.dice_text_font, fill=Interface.black, anchor="mm")

    def draw_player_turn(self, draw: ImageDraw.Draw, base: tuple, base_size: int):
        text = "WHITE" if self.player_turn == WHITE else "BLACK" if self.player_turn == BLACK else "NEITHER"
        draw.text((base[0] + base_size * 3.25, base[1] - round(Interface.ratio * base_size) * 2 - Interface.centre_distance - base_size * 1.5),
                  text, font=Interface.player_turn_font, fill=Interface.black, anchor="mm")

    def draw_mat(self, draw: ImageDraw.Draw, base: tuple, base_size: int):
        row1_start = base
        row2_start = (base[0] + base_size * 8, base[1])
        row3_start = (base[0], base[1] - round(Interface.ratio * base_size) * 2 - Interface.centre_distance)
        row4_start = (base[0] + base_size * 8, base[1] - round(Interface.ratio * base_size) * 2 - Interface.centre_distance)
        self.draw_row_of_triangles(draw, row1_start, base_size, Interface.brown, Interface.dark_grey, False, 6)
        self.draw_row_of_triangles(draw, row2_start, base_size, Interface.dark_grey, Interface.brown, False, 6)
        self.draw_row_of_triangles(draw, row3_start, base_size, Interface.dark_grey, Interface.brown, True, 6)
        self.draw_row_of_triangles(draw, row4_start, base_size, Interface.brown, Interface.dark_grey, True, 6)
        self.draw_bar(draw, (base[0] + base_size * 6.5, base[1]), base_size, Interface.grey)
        self.draw_bar(draw, (base[0] - base_size * 1, base[1]), base_size, Interface.grey)
        self.draw_bar(draw, (base[0] + base_size * 14, base[1]), base_size, Interface.grey)
        draw.rectangle([(base[0] - base_size * 1.5, base[1]), 
                        (base[0] + base_size * 14, base[1] - base_size)], 
                        fill=Interface.grey)
        draw.rectangle([(base[0] - base_size * 1.5, base[1] - round(Interface.ratio * base_size) * 2 - Interface.centre_distance),
                        (base[0] + base_size * 14.5, base[1] - round(Interface.ratio * base_size) * 2 - Interface.centre_distance - base_size)], 
                        fill=Interface.grey)
        self.draw_point_numbers(draw, base, base_size)

    def draw_point_numbers(self, draw: ImageDraw.Draw, base: int, base_size: int):
        for point in range(24):
            xy = self.point_to_xy(base, base_size, point)
            xy = (xy[0], xy[1] - base_size // 3)
            draw.text(xy, "{}".format(point + 1), align="centre", anchor="mb", fill=Interface.black, font=Interface.point_text_font)

    def point_to_xy(self, base: tuple, base_size: int, point: int):
        assert point >= 0 and point <= 23, point
        if point <= 5:
            xy = (base[0] + base_size * (13 - point), base[1])
        elif point <= 11:
            xy = (base[0] + base_size * (5 - (point - 6)), base[1])
        elif point <= 17:
            xy = (base[0] + base_size * (point - 12), base[1] - round(Interface.ratio * base_size) * 2 - Interface.centre_distance)
        else:
            xy = (base[0] + base_size * (point - 10), base[1] - round(Interface.ratio * base_size) * 2 - Interface.centre_distance)
        return xy

    def draw_movement_move(self, draw: ImageDraw.Draw, base: tuple, base_size: int, last_move):
        if last_move.move.src == -1:
            self.draw_rectangle_around_bar(draw, (base[0] + base_size * 6.5, base[1]), base_size, Interface.black)
        elif last_move.move.src == 24:
            self.draw_rectangle_around_bar(draw, (base[0] + base_size * 6.5, base[1]), base_size, Interface.black)
        else:
            self.draw_rectangle_around_point(draw, base, base_size, last_move.move.src, Interface.black)

        if last_move.move.dst == -1:
            self.draw_rectangle_around_bar(draw, (base[0] + base_size * 14, base[1]), base_size, Interface.black)
        elif last_move.move.dst == 24:
            self.draw_rectangle_around_bar(draw, (base[0] - base_size, base[1]), base_size, Interface.black)
        else:
            self.draw_rectangle_around_point(draw, base, base_size, last_move.move.dst, Interface.black)

    def draw_rectangle_around_point(self, draw: ImageDraw.Draw, base: tuple, base_size: int, point: int, color: tuple):
        xy = self.point_to_xy(base, base_size, point)
        if self.point_is_flipped(point):
            draw.rectangle([(xy[0] - base_size // 2, xy[1]), (xy[0] + base_size // 2, round(xy[1] + Interface.ratio * base_size))],
                           outline=color, width=Interface.movement_rectangle_width)
        else:
            draw.rectangle([(xy[0] + base_size // 2, round(xy[1] - Interface.ratio * base_size)), (xy[0] - base_size // 2, xy[1] - base_size)],
                           outline=color, width=Interface.movement_rectangle_width)

    def point_is_flipped(self, point: int):
        return point > 11

    def draw_state(self, draw: ImageDraw.Draw, base: tuple, base_size: int, state: State):
        (board, bar, beared_off) = (state.get_board(), state.get_bar(), state.get_beared_off())
        for point in range(24):
            xy = self.point_to_xy(base, base_size, point)
            is_flipped = self.point_is_flipped(point)
            if board[WHITE, point] > 0:
                self.draw_pieces(draw, xy, base_size, Interface.white, is_flipped, board[WHITE, point])
            elif board[BLACK, point] > 0:
                self.draw_pieces(draw, xy, base_size, Interface.black, is_flipped, board[BLACK, point])
        if bar[WHITE] > 0:
            self.draw_pieces(draw, (base[0] + base_size * 6.5, base[1]), base_size, Interface.white, False, bar[WHITE])
        if bar[BLACK] > 0:
            self.draw_pieces(draw, (base[0] + base_size * 6.5, base[1] - round(Interface.ratio * base_size) * 2 - Interface.centre_distance), base_size, Interface.black, True, bar[BLACK])
        if beared_off[WHITE] > 0:
            self.draw_pieces(draw, (base[0] + base_size * 14, base[1]), base_size, Interface.white, False, beared_off[WHITE])
        if beared_off[BLACK] > 0:
            self.draw_pieces(draw, (base[0] - base_size, base[1]), base_size, Interface.black, False, beared_off[BLACK])

    def draw_pieces(self, draw: ImageDraw.Draw, base: tuple, base_size: int, color: tuple, flipped: bool, n: int):
        for i in range(1, n + 1):
            text = None if i < min(n, Interface.max_pieces_per_point) else "{}".format(n)
            self.draw_piece(draw, base, base_size, color, flipped, i, n, text)

    def draw_piece(self, draw: ImageDraw.Draw, base: tuple, base_size: int, color: tuple, flipped: bool, n: int, total_n: int, text: str=None):
        other_color = Interface.black if color == Interface.white else Interface.white
        if n <= Interface.max_pieces_per_point:
            if not flipped:
                (x, y) = (base[0], base[1] - base_size - (n - 1) * Interface.piece_distance - (n - 1) * base_size * Interface.piece_size_scale)
                draw.ellipse([x - (base_size // 2) * Interface.piece_size_scale, y - (base_size * Interface.piece_size_scale),
                            x + (base_size // 2) * Interface.piece_size_scale,
                            y], fill=color)
                if text is not None:
                    draw.text((x, y - ((base_size // 4) * Interface.piece_size_scale)), "{}".format(total_n), align="centre", anchor="mb", fill=other_color, font=Interface.piece_text_font)
            else:
                (x, y) = (base[0], base[1] + (n - 1) * Interface.piece_distance + (n - 1) * base_size * Interface.piece_size_scale)
                draw.ellipse([x - (base_size // 2) * Interface.piece_size_scale, y,
                            x + (base_size // 2) * Interface.piece_size_scale,
                            y + (base_size * Interface.piece_size_scale)], fill=color)
                if text is not None:
                    draw.text((x, y + (base_size // 4 * 3) * Interface.piece_size_scale), "{}".format(total_n), align="centre", anchor="mb", fill=other_color, font=Interface.piece_text_font)

    def draw_bar(self, draw: ImageDraw.Draw, base: tuple, base_size: int, color: tuple):
        draw.rectangle([(base[0] - base_size // 2, base[1]),
                        (base[0] + base_size // 2, base[1] - round(Interface.ratio * base_size) * 2 - Interface.centre_distance)],
                        color)

    def draw_row_of_triangles(self, draw: ImageDraw.Draw, base: tuple, base_size: int, color1: tuple, color2: tuple, flipped: bool, n: int):
        for i in range(n):
            self.draw_triangle(draw, (base[0] + base_size * i, base[1]), base_size, color1 if i % 2 == 0 else color2, flipped)

    def draw_triangle(self, draw: ImageDraw.Draw, base: tuple, base_size: int, color: tuple, flipped: bool):
        """28x130"""
        (x, y) = base
        points = [(x - base_size // 2, y), (x + base_size // 2, y)]
        if flipped:
            points.append((x, round(y + Interface.ratio * base_size)))
        else:
            points.append((x, round(y - Interface.ratio * base_size)))
        draw.polygon(points, color)

def run():
    interface = Interface()
    root = TkApp(interface)
    root.mainloop()

run()