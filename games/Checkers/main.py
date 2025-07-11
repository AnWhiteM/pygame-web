import pygame
import asyncio
import sys
import random
import copy

# --- КОНСТАНТИ ГРИ ---
BOARD_SIZE = 800
ROWS, COLS = 8, 8
SQUARE_SIZE = BOARD_SIZE // COLS

MARGIN = 50
TEXT_OFFSET = 10

LOG_AREA_WIDTH = 300
WIDTH, HEIGHT = BOARD_SIZE + MARGIN * 2 + LOG_AREA_WIDTH, BOARD_SIZE + MARGIN * 2
LOG_TEXT_COLOR = (255, 255, 255)
LOG_FONT_SIZE = 20
LOG_PADDING = 10

# --- КОЛЬОРИ (RGB) ---
DARK_WOOD = (118, 77, 49)
LIGHT_WOOD = (238, 207, 161)
BLACK_PIECE = (30, 30, 30)
WHITE_PIECE = (220, 220, 220)
HIGHLIGHT_GREEN = (0, 255, 0)
GREY = (128, 128, 128)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)

FPS = 60

# --- СТАНИ ГРИ ---
MAIN_MENU = 0
PLAYER_VS_MODE_SELECTION = 1
DIFFICULTY_SELECTION = 2
PLAYER_COLOR_SELECTION = 3
PLAYING = 4
GAME_OVER = 5
game_state = MAIN_MENU

# --- РЕЖИМИ ГРИ ---
MODE_VS_PLAYER = 0
MODE_VS_BOT = 1
CURRENT_GAME_MODE = None

# --- СКЛАДНІСТЬ БОТА ---
DIFFICULTY_EASY = 0
DIFFICULTY_MEDIUM = 1
DIFFICULTY_HARD = 2
CURRENT_BOT_DIFFICULTY = None

PLAYER_HUMAN_COLOR = None
BOT_COLOR = None

# --- ІНІЦІАЛІЗАЦІЯ PYGAME ---
pygame.init()
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Шашки")

# --- ШРИФТИ ---
FONT = pygame.font.Font(None, 50)
SMALL_FONT = pygame.font.Font(None, LOG_FONT_SIZE)
BUTTON_FONT = pygame.font.Font(None, 30)

# --- ДОПОМІЖНІ ФУНКЦІЇ ---
def get_row_col_from_mouse(pos):
    x, y = pos
    if MARGIN <= x < WIDTH - LOG_AREA_WIDTH - MARGIN and MARGIN <= y < HEIGHT - MARGIN:
        col = (x - MARGIN) // SQUARE_SIZE
        row = (y - MARGIN) // SQUARE_SIZE
        return row, col
    return -1, -1

def draw_text(surface, text, font, color, x, y, center=True):
    text_obj = font.render(text, True, color)
    text_rect = text_obj.get_rect()
    if center:
        text_rect.center = (x, y)
    else:
        text_rect.topleft = (x, y)
    surface.blit(text_obj, text_rect)

def draw_button(surface, rect, text, font, color, text_color):
    pygame.draw.rect(surface, color, rect, border_radius=10)
    draw_text(surface, text, font, text_color, rect.centerx, rect.centery)

def draw_logs(surface, logs):
    log_area_x = BOARD_SIZE + MARGIN * 2
    log_area_y = MARGIN
    log_area_height = BOARD_SIZE
    pygame.draw.rect(surface, GREY, (log_area_x, log_area_y, LOG_AREA_WIDTH, log_area_height))
    pygame.draw.rect(surface, BLACK_PIECE, (log_area_x, log_area_y, LOG_AREA_WIDTH, log_area_height), 2)
    draw_text(surface, "Логи Гри", SMALL_FONT, LOG_TEXT_COLOR,
              log_area_x + LOG_AREA_WIDTH // 2, log_area_y + LOG_PADDING, center=True)
    log_start_y = log_area_y + LOG_FONT_SIZE + 2 * LOG_PADDING
    for i, log_entry in enumerate(logs[-10:]):
        draw_text(surface, log_entry, SMALL_FONT, LOG_TEXT_COLOR,
                  log_area_x + LOG_PADDING, log_start_y + i * (LOG_FONT_SIZE + 5), center=False)

# --- МЕНЮ ТА ЕКРАНИ ---
def draw_main_menu(surface, start_button_rect):
    surface.fill(GREY)
    draw_text(surface, "Шашки", FONT, BLACK_PIECE, WIDTH // 2, HEIGHT // 4)
    draw_button(surface, start_button_rect, "Почати гру", BUTTON_FONT, BLUE, WHITE_PIECE)
    pygame.display.update()

def draw_player_vs_mode_selection_screen(surface, vs_player_button_rect, vs_bot_button_rect):
    surface.fill(GREY)
    draw_text(surface, "Оберіть режим гри", FONT, BLACK_PIECE, WIDTH // 2, HEIGHT // 4)
    draw_button(surface, vs_player_button_rect, "Гравець проти Гравця", BUTTON_FONT, BLUE, WHITE_PIECE)
    draw_button(surface, vs_bot_button_rect, "Гравець проти Бота", BUTTON_FONT, BLUE, WHITE_PIECE)
    pygame.display.update()

def draw_difficulty_selection_screen(surface, easy_button_rect, medium_button_rect, hard_button_rect):
    surface.fill(GREY)
    draw_text(surface, "Оберіть складність бота", FONT, BLACK_PIECE, WIDTH // 2, HEIGHT // 4)
    draw_button(surface, easy_button_rect, "Легко", BUTTON_FONT, GREEN, WHITE_PIECE)
    draw_button(surface, medium_button_rect, "Середнє", BUTTON_FONT, BLUE, WHITE_PIECE)
    draw_button(surface, hard_button_rect, "Складно", BUTTON_FONT, RED, WHITE_PIECE)
    pygame.display.update()

def draw_player_color_selection_screen(surface, white_color_button_rect, black_color_button_rect):
    surface.fill(GREY)
    draw_text(surface, "Оберіть колір", FONT, BLACK_PIECE, WIDTH // 2, HEIGHT // 4)
    draw_button(surface, white_color_button_rect, "Білі", BUTTON_FONT, WHITE_PIECE, BLACK_PIECE)
    draw_button(surface, black_color_button_rect, "Чорні", BUTTON_FONT, BLACK_PIECE, WHITE_PIECE)
    pygame.display.update()

def draw_end_game_screen(surface, message, restart_button_rect):
    surface.fill(GREY)
    draw_text(surface, "Гру завершено!", FONT, BLACK_PIECE, WIDTH // 2, HEIGHT // 4)
    draw_text(surface, message, FONT, RED, WIDTH // 2, HEIGHT // 2 - 50)
    draw_button(surface, restart_button_rect, "Почати знову", BUTTON_FONT, BLUE, WHITE_PIECE)
    pygame.display.update()

# --- КЛАСИ ---
class Piece:
    PADDING = 15
    OUTLINE = 2

    def __init__(self, row, col, color, king=False):
        self.row = row
        self.col = col
        self.color = color
        self.king = king
        self.x = 0
        self.y = 0
        self.calc_pos()

    def calc_pos(self):
        self.x = self.col * SQUARE_SIZE + SQUARE_SIZE // 2 + MARGIN
        self.y = self.row * SQUARE_SIZE + SQUARE_SIZE // 2 + MARGIN

    def make_king(self):
        self.king = True

    def draw(self, win):
        radius = SQUARE_SIZE // 2 - self.PADDING
        pygame.draw.circle(win, GREY, (self.x, self.y), radius + self.OUTLINE)
        pygame.draw.circle(win, self.color, (self.x, self.y), radius)
        if self.king:
            pygame.draw.circle(win, RED, (self.x, self.y), radius // 2)

    def move(self, row, col):
        self.row = row
        self.col = col
        self.calc_pos()

    def get_coords_str(self):
        return f"({self.row}, {self.col})"

class Board:
    def __init__(self):
        self.board = []
        self.black_left = 12
        self.white_left = 12
        self.create_board()

    def draw_squares(self, win):
        win.fill(DARK_WOOD)
        for row in range(ROWS):
            for col in range(row % 2, COLS, 2):
                pygame.draw.rect(win, LIGHT_WOOD, (col * SQUARE_SIZE + MARGIN, row * SQUARE_SIZE + MARGIN, SQUARE_SIZE, SQUARE_SIZE))
        
        pygame.draw.rect(win, BLACK_PIECE, (MARGIN, MARGIN, BOARD_SIZE, BOARD_SIZE), 3)

        font = pygame.font.Font(None, 30)
        for i in range(ROWS):
            row_label = font.render(str(i + 1), True, BLACK_PIECE)
            win.blit(row_label, (MARGIN - TEXT_OFFSET - row_label.get_width(), i * SQUARE_SIZE + SQUARE_SIZE // 2 + MARGIN - row_label.get_height() // 2))
            win.blit(row_label, (BOARD_SIZE + MARGIN + TEXT_OFFSET, i * SQUARE_SIZE + SQUARE_SIZE // 2 + MARGIN - row_label.get_height() // 2))
            
            col_label = font.render(chr(65 + i), True, BLACK_PIECE)
            win.blit(col_label, (i * SQUARE_SIZE + SQUARE_SIZE // 2 + MARGIN - col_label.get_width() // 2, MARGIN - TEXT_OFFSET - col_label.get_height()))
            win.blit(col_label, (i * SQUARE_SIZE + SQUARE_SIZE // 2 + MARGIN - col_label.get_width() // 2, BOARD_SIZE + MARGIN + TEXT_OFFSET))

    def create_board(self):
        for row in range(ROWS):
            self.board.append([])
            for col in range(COLS):
                if col % 2 == ((row + 1) % 2):
                    if row < 3:
                        self.board[row].append(Piece(row, col, BLACK_PIECE))
                    elif row > 4:
                        self.board[row].append(Piece(row, col, WHITE_PIECE))
                    else:
                        self.board[row].append(0)
                else:
                    self.board[row].append(0)

    def draw(self, win):
        self.draw_squares(win)
        for row in range(ROWS):
            for col in range(COLS):
                piece = self.board[row][col]
                if piece != 0:
                    piece.draw(win)

    def move_piece(self, piece, row, col, skipped_pieces=[]):
        self.board[piece.row][piece.col] = 0 
        piece.move(row, col) 
        self.board[row][col] = piece

        if skipped_pieces:
            for skipped_piece in skipped_pieces:
                self.remove_piece(skipped_piece)

        if (piece.color == WHITE_PIECE and piece.row == 0) or \
           (piece.color == BLACK_PIECE and piece.row == ROWS - 1):
            if not piece.king: 
                piece.make_king()
                game_logs.append(f"Шашка {piece.get_coords_str()} стала дамкою!")

    def remove_piece(self, piece_to_remove):
        r, c = piece_to_remove.row, piece_to_remove.col
        actual_piece_on_board = self.get_piece(r, c)

        if actual_piece_on_board != 0 and actual_piece_on_board.color == piece_to_remove.color:
            self.board[r][c] = 0
            if actual_piece_on_board.color == BLACK_PIECE:
                self.black_left -= 1
            else:
                self.white_left -= 1
        else:
            pass

    def winner(self):
        if self.black_left <= 0:
            return WHITE_PIECE
        elif self.white_left <= 0:
            return BLACK_PIECE
        return None
    
    def get_piece(self, row, col):
        if 0 <= row < ROWS and 0 <= col < COLS:
            return self.board[row][col]
        return 0 

    def _find_all_captures(self, piece, board_state, current_row, current_col, path_skipped_pieces):
        all_capture_paths = {} 

        if not piece:
             return all_capture_paths

        if not piece.king:
            move_directions = []
            if piece.color == WHITE_PIECE:
                move_directions = [(-1, -1), (-1, 1)] 
            else: 
                move_directions = [(1, -1), (1, 1)] 
        else:
            move_directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)] 

        found_any_capture_in_this_step = False

        for dr, dc in move_directions:
            if piece.king:
                temp_row, temp_col = current_row + dr, current_col + dc
                potential_skipped = None 

                while 0 <= temp_row < ROWS and 0 <= temp_col < COLS:
                    target_piece_on_board = board_state.get_piece(temp_row, temp_col)

                    if target_piece_on_board == 0:
                        if potential_skipped: 
                            capture_pos = (temp_row, temp_col)
                            new_skipped_path = path_skipped_pieces + [potential_skipped]
                            temp_board_for_recursion = copy.deepcopy(board_state)
                            
                            piece_to_move_sim = temp_board_for_recursion.get_piece(current_row, current_col)
                            skipped_sim = temp_board_for_recursion.get_piece(potential_skipped.row, potential_skipped.col)

                            if piece_to_move_sim and skipped_sim:
                                temp_board_for_recursion.board[current_row][current_col] = 0
                                piece_to_move_sim.row, piece_to_move_sim.col = capture_pos[0], capture_pos[1]
                                temp_board_for_recursion.board[capture_pos[0]][capture_pos[1]] = piece_to_move_sim
                                temp_board_for_recursion.remove_piece(skipped_sim)

                                if (piece_to_move_sim.color == WHITE_PIECE and capture_pos[0] == 0) or \
                                (piece_to_move_sim.color == BLACK_PIECE and capture_pos[0] == ROWS - 1):
                                    if not piece_to_move_sim.king:
                                        piece_to_move_sim.make_king()
                            else:
                                break

                            recursive_captures = self._find_all_captures(piece_to_move_sim, temp_board_for_recursion, capture_pos[0], capture_pos[1], new_skipped_path)
                            
                            if not recursive_captures: 
                                all_capture_paths[capture_pos] = new_skipped_path
                            else:
                                for final_pos, full_path_skipped in recursive_captures.items():
                                    all_capture_paths[final_pos] = full_path_skipped
                            found_any_capture_in_this_step = True 
                        
                    elif target_piece_on_board.color == piece.color:
                        break
                    else: 
                        if potential_skipped: 
                            break
                        else: 
                            potential_skipped = target_piece_on_board
                    
                    temp_row += dr
                    temp_col += dc
            else: 
                new_row, new_col = current_row + dr, current_col + dc
                capture_row, capture_col = current_row + 2 * dr, current_col + 2 * dc

                if (0 <= new_row < ROWS and 0 <= new_col < COLS and 
                    0 <= capture_row < ROWS and 0 <= capture_col < COLS): 
                    
                    target_piece_on_board = board_state.get_piece(new_row, new_col)
                    
                    if (target_piece_on_board != 0 and target_piece_on_board.color != piece.color and 
                        board_state.get_piece(capture_row, capture_col) == 0): 
                        
                        found_any_capture_in_this_step = True
                        new_skipped_path = path_skipped_pieces + [target_piece_on_board]

                        temp_board_for_recursion = copy.deepcopy(board_state)
                        piece_to_move_sim = temp_board_for_recursion.get_piece(current_row, current_col)
                        skipped_sim = temp_board_for_recursion.get_piece(target_piece_on_board.row, target_piece_on_board.col)

                        if piece_to_move_sim and skipped_sim:
                            temp_board_for_recursion.board[current_row][current_col] = 0
                            piece_to_move_sim.row, piece_to_move_sim.col = capture_row, capture_col
                            temp_board_for_recursion.board[capture_row][capture_col] = piece_to_move_sim
                            temp_board_for_recursion.remove_piece(skipped_sim)

                            if (piece_to_move_sim.color == WHITE_PIECE and capture_row == 0) or \
                               (piece_to_move_sim.color == BLACK_PIECE and capture_row == ROWS - 1):
                                if not piece_to_move_sim.king:
                                    piece_to_move_sim.make_king()
                            
                            recursive_captures = self._find_all_captures(piece_to_move_sim, temp_board_for_recursion, capture_row, capture_col, new_skipped_path)
                        else:
                            continue

                        if not recursive_captures: 
                            all_capture_paths[(capture_row, capture_col)] = new_skipped_path
                        else:
                            for final_pos, full_path_skipped in recursive_captures.items():
                                all_capture_paths[final_pos] = full_path_skipped
        
        if not found_any_capture_in_this_step and path_skipped_pieces:
            all_capture_paths[(current_row, current_col)] = path_skipped_pieces
            
        return all_capture_paths

    def valid_moves(self, piece):
        if piece == 0:
            return {}
            
        all_capture_paths = self._find_all_captures(piece, self, piece.row, piece.col, [])

        if all_capture_paths:
            max_captures = 0
            for move_pos, skipped_pieces in all_capture_paths.items():
                max_captures = max(max_captures, len(skipped_pieces))
            
            filtered_captures = {move_pos: skipped_pieces for move_pos, skipped_pieces in all_capture_paths.items() if len(skipped_pieces) == max_captures}
            return filtered_captures
        else:
            moves = {}
            if not piece.king:
                move_directions = []
                if piece.color == WHITE_PIECE:
                    move_directions = [(-1, -1), (-1, 1)]
                else: 
                    move_directions = [(1, -1), (1, 1)]
                
                for dr, dc in move_directions:
                    new_row, new_col = piece.row + dr, piece.col + dc
                    if 0 <= new_row < ROWS and 0 <= new_col < COLS and self.get_piece(new_row, new_col) == 0:
                        moves[(new_row, new_col)] = []
            else: 
                king_directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
                for dr, dc in king_directions:
                    current_row, current_col = piece.row + dr, piece.col + dc
                    while 0 <= current_row < ROWS and 0 <= current_col < COLS:
                        if self.get_piece(current_row, current_col) == 0:
                            moves[(current_row, current_col)] = []
                        else:
                            break 
                        current_row += dr
                        current_col += dc
            return moves

# --- АЛГОРИТМ MINIMAX ДЛЯ БОТА (СКЛАДНА СКЛАДНІСТЬ) ---
def evaluate_board(board, bot_color, opponent_color):
    score = 0
    for r in range(ROWS):
        for c in range(COLS):
            piece = board.get_piece(r, c)
            if piece != 0:
                value = 10
                if piece.king:
                    value = 25
                
                if piece.color == bot_color:
                    score += value
                    if not piece.king:
                        if bot_color == WHITE_PIECE:
                            score += (ROWS - 1 - r) * 0.5 
                        else: 
                            score += r * 0.5 
                else: 
                    score -= value
                    if not piece.king:
                        if opponent_color == WHITE_PIECE:
                            score -= (ROWS - 1 - r) * 0.5
                        else: 
                            score -= r * 0.5
    return score

def minimax(board, depth, maximizing_player, alpha, beta, bot_color, opponent_color):
    if depth == 0 or board.winner() is not None:
        return evaluate_board(board, bot_color, opponent_color), board 

    if maximizing_player:
        max_eval = float('-inf')
        best_board_state_for_max = None
        current_board_state = copy.deepcopy(board) 

        bot_pieces = [current_board_state.get_piece(r,c) for r in range(ROWS) for c in range(COLS) if current_board_state.get_piece(r,c) != 0 and current_board_state.get_piece(r,c).color == bot_color]

        for piece_sim in bot_pieces:
            if current_board_state.get_piece(piece_sim.row, piece_sim.col) == 0:
                continue

            moves = current_board_state.valid_moves(piece_sim)
            
            for move_pos, skipped_pieces_sim in moves.items():
                temp_board_sim = copy.deepcopy(current_board_state)
                temp_piece_to_move_sim = temp_board_sim.get_piece(piece_sim.row, piece_sim.col) 
                
                actual_skipped_on_temp_board = []
                if skipped_pieces_sim: 
                    for sp_sim in skipped_pieces_sim:
                        skipped_on_temp = temp_board_sim.get_piece(sp_sim.row, sp_sim.col)
                        if skipped_on_temp:
                             actual_skipped_on_temp_board.append(skipped_on_temp)
                
                if temp_piece_to_move_sim:
                    temp_board_sim.move_piece(temp_piece_to_move_sim, move_pos[0], move_pos[1], actual_skipped_on_temp_board)
                    evaluation, _ = minimax(temp_board_sim, depth - 1, False, alpha, beta, bot_color, opponent_color)

                    if evaluation > max_eval:
                        max_eval = evaluation
                        best_board_state_for_max = temp_board_sim 

                    alpha = max(alpha, evaluation)
                    if beta <= alpha:
                        break 
            if beta <= alpha:
                break
        return max_eval, best_board_state_for_max

    else: # minimizing_player
        min_eval = float('inf')
        best_board_state_for_min = None
        current_board_state = copy.deepcopy(board)

        opponent_pieces = [current_board_state.get_piece(r,c) for r in range(ROWS) for c in range(COLS) if current_board_state.get_piece(r,c) != 0 and current_board_state.get_piece(r,c).color == opponent_color]

        for piece_sim in opponent_pieces:
            if current_board_state.get_piece(piece_sim.row, piece_sim.col) == 0:
                continue

            moves = current_board_state.valid_moves(piece_sim)

            for move_pos, skipped_pieces_sim in moves.items():
                temp_board_sim = copy.deepcopy(current_board_state)
                temp_piece_to_move_sim = temp_board_sim.get_piece(piece_sim.row, piece_sim.col)

                actual_skipped_on_temp_board = []
                if skipped_pieces_sim:
                    for sp_sim in skipped_pieces_sim:
                        skipped_on_temp = temp_board_sim.get_piece(sp_sim.row, sp_sim.col)
                        if skipped_on_temp:
                            actual_skipped_on_temp_board.append(skipped_on_temp)
                
                if temp_piece_to_move_sim:
                    temp_board_sim.move_piece(temp_piece_to_move_sim, move_pos[0], move_pos[1], actual_skipped_on_temp_board)
                    evaluation, _ = minimax(temp_board_sim, depth - 1, True, alpha, beta, bot_color, opponent_color)

                    if evaluation < min_eval:
                        min_eval = evaluation
                        best_board_state_for_min = temp_board_sim

                    beta = min(beta, evaluation)
                    if beta <= alpha:
                        break
            if beta <= alpha:
                break
        return min_eval, best_board_state_for_min

# --- ЛОГІКА БОТА ДЛЯ ЛЕГКОЇ СКЛАДНОСТІ ---
def make_easy_bot_move(board, bot_color):
    all_possible_moves = []
    bot_pieces = [p for row_idx in range(ROWS) for col_idx in range(COLS) 
                  if (p := board.get_piece(row_idx, col_idx)) != 0 and p.color == bot_color]

    for piece in bot_pieces:
        moves = board.valid_moves(piece)
        for move_pos, skipped in moves.items():
            all_possible_moves.append({
                'piece': piece, 
                'move_pos': move_pos, 
                'skipped': skipped,
                'is_capture': bool(skipped)
            })
    
    if not all_possible_moves:
        return None, None, []

    capture_moves = [m for m in all_possible_moves if m['is_capture']]
    
    if capture_moves:
        chosen_move_data = random.choice(capture_moves)
    else:
        chosen_move_data = random.choice(all_possible_moves)
    
    original_piece = board.get_piece(chosen_move_data['piece'].row, chosen_move_data['piece'].col)
    original_skipped_pieces = [board.get_piece(s.row, s.col) for s in chosen_move_data['skipped'] if board.get_piece(s.row, s.col) != 0]

    return original_piece, chosen_move_data['move_pos'], original_skipped_pieces

# --- ЛОГІКА БОТА ДЛЯ СЕРЕДНЬОЇ СКЛАДНОСТІ ---
def make_medium_bot_move(board, bot_color):
    all_possible_moves_data = []
    opponent_color = WHITE_PIECE if bot_color == BLACK_PIECE else BLACK_PIECE

    bot_pieces_on_current_board = [
        p for r in range(ROWS) for c in range(COLS) 
        if (p := board.get_piece(r, c)) != 0 and p.color == bot_color
    ]

    must_capture = False
    for piece in bot_pieces_on_current_board:
        moves = board.valid_moves(piece)
        for move_pos, skipped_pieces in moves.items():
            if skipped_pieces:
                must_capture = True
            all_possible_moves_data.append({
                'piece_obj': piece,
                'move_pos': move_pos,
                'skipped_objs': skipped_pieces,
                'score': 0
            })
    
    if not all_possible_moves_data:
        return None, None, []

    if must_capture:
        all_possible_moves_data = [m for m in all_possible_moves_data if m['skipped_objs']]

    for move_data in all_possible_moves_data:
        score = 0
        temp_board = copy.deepcopy(board)
        
        sim_piece_to_move = temp_board.get_piece(move_data['piece_obj'].row, move_data['piece_obj'].col)
        sim_skipped_pieces = [temp_board.get_piece(s.row, s.col) for s in move_data['skipped_objs'] if temp_board.get_piece(s.row, s.col) !=0]

        if not sim_piece_to_move:
            continue

        temp_board.move_piece(sim_piece_to_move, move_data['move_pos'][0], move_data['move_pos'][1], sim_skipped_pieces)
        piece_after_move_sim = temp_board.get_piece(move_data['move_pos'][0], move_data['move_pos'][1])

        if move_data['skipped_objs']:
            score += 1000 + len(move_data['skipped_objs']) * 100

        if piece_after_move_sim and piece_after_move_sim.king and not move_data['piece_obj'].king:
            score += 250
        
        if piece_after_move_sim and not move_data['skipped_objs']:
            next_turn_potential_captures = temp_board.valid_moves(piece_after_move_sim)
            if any(sk for _, sk in next_turn_potential_captures.items() if sk):
                score += 150

        is_safe_from_immediate_capture = True
        if piece_after_move_sim:
            for r_opp in range(ROWS):
                for c_opp in range(COLS):
                    opp_piece_sim = temp_board.get_piece(r_opp, c_opp)
                    if opp_piece_sim != 0 and opp_piece_sim.color == opponent_color:
                        opp_next_moves = temp_board.valid_moves(opp_piece_sim)
                        for _, opp_skipped_list_sim in opp_next_moves.items():
                            if piece_after_move_sim in opp_skipped_list_sim:
                                is_safe_from_immediate_capture = False
                                break
                if not is_safe_from_immediate_capture:
                    break
        
        if not is_safe_from_immediate_capture:
            if not move_data['skipped_objs']:
                 score -= 200
            else:
                 score -= 50
        else:
            if not move_data['skipped_objs']:
                score += 50

        original_piece_is_threatened = False
        for r_opp_orig in range(ROWS):
            for c_opp_orig in range(COLS):
                opp_piece_orig = board.get_piece(r_opp_orig, c_opp_orig)
                if opp_piece_orig != 0 and opp_piece_orig.color == opponent_color:
                    opp_moves_on_orig_board = board.valid_moves(opp_piece_orig)
                    for _, opp_skipped_on_orig in opp_moves_on_orig_board.items():
                        if move_data['piece_obj'] in opp_skipped_on_orig:
                            original_piece_is_threatened = True
                            break
            if original_piece_is_threatened:
                break
        
        if original_piece_is_threatened and is_safe_from_immediate_capture:
            score += 180

        if piece_after_move_sim and not piece_after_move_sim.king:
            if bot_color == WHITE_PIECE:
                score += (ROWS - 1 - piece_after_move_sim.row) * 5
            else:
                score += piece_after_move_sim.row * 5
        
        move_data['score'] = score

    best_score = -float('inf')
    best_moves = []
    for m_data in all_possible_moves_data:
        if m_data['score'] > best_score:
            best_score = m_data['score']
            best_moves = [m_data]
        elif m_data['score'] == best_score:
            best_moves.append(m_data)
    
    if not best_moves:
        return make_easy_bot_move(board, bot_color)

    chosen_move_data = random.choice(best_moves)

    final_chosen_piece = board.get_piece(chosen_move_data['piece_obj'].row, chosen_move_data['piece_obj'].col)
    final_skipped_pieces = [board.get_piece(s.row, s.col) for s in chosen_move_data['skipped_objs'] if board.get_piece(s.row, s.col) !=0 ]

    return final_chosen_piece, chosen_move_data['move_pos'], final_skipped_pieces

# --- ОСНОВНА ЛОГІКА БОТА ---
async def bot_move(board, bot_color):
    chosen_piece_original = None
    chosen_move_pos = None
    skipped_pieces_original = []

    if CURRENT_BOT_DIFFICULTY == DIFFICULTY_EASY:
        chosen_piece_original, chosen_move_pos, skipped_pieces_original = make_easy_bot_move(board, bot_color)
    
    elif CURRENT_BOT_DIFFICULTY == DIFFICULTY_MEDIUM:
        chosen_piece_original, chosen_move_pos, skipped_pieces_original = make_medium_bot_move(board, bot_color)

    elif CURRENT_BOT_DIFFICULTY == DIFFICULTY_HARD:
        depth = 5 
        opponent_color = WHITE_PIECE if bot_color == BLACK_PIECE else BLACK_PIECE
        
        score, new_board_state_from_minimax = minimax(board, depth, True, float('-inf'), float('inf'), bot_color, opponent_color)

        if new_board_state_from_minimax is None:
            return make_easy_bot_move(board, bot_color)

        all_current_possible_moves = []
        bot_pieces_on_current_board = [
            p for r in range(ROWS) for c in range(COLS) 
            if (p := board.get_piece(r,c)) !=0 and p.color == bot_color
        ]
        
        for piece in bot_pieces_on_current_board:
            current_piece_moves = board.valid_moves(piece)
            for move_p, skipped_p in current_piece_moves.items():
                all_current_possible_moves.append({'piece': piece, 'move_pos': move_p, 'skipped': skipped_p})

        all_current_possible_moves.sort(key=lambda x: len(x['skipped']), reverse=True)

        found_matching_move = False
        for move_option in all_current_possible_moves:
            temp_board_for_check = copy.deepcopy(board)
            piece_to_sim_on_check = temp_board_for_check.get_piece(move_option['piece'].row, move_option['piece'].col)
            
            skipped_to_sim_on_check = []
            if move_option['skipped']:
                for sp_orig in move_option['skipped']: 
                    sp_sim_on_check = temp_board_for_check.get_piece(sp_orig.row, sp_orig.col)
                    if sp_sim_on_check:
                        skipped_to_sim_on_check.append(sp_sim_on_check)
            
            if not piece_to_sim_on_check: continue 

            temp_board_for_check.move_piece(piece_to_sim_on_check, move_option['move_pos'][0], move_option['move_pos'][1], skipped_to_sim_on_check)

            boards_match = True
            for r_comp in range(ROWS):
                for c_comp in range(COLS):
                    p1 = temp_board_for_check.get_piece(r_comp, c_comp)
                    p2 = new_board_state_from_minimax.get_piece(r_comp, c_comp)
                    
                    if (p1 == 0 and p2 != 0) or (p1 != 0 and p2 == 0):
                        boards_match = False; break
                    if p1 != 0 and p2 != 0:
                        if not (p1.row == p2.row and p1.col == p2.col and p1.color == p2.color and p1.king == p2.king):
                            boards_match = False; break
                if not boards_match: break
            
            if boards_match:
                chosen_piece_original = move_option['piece'] 
                chosen_move_pos = move_option['move_pos']
                skipped_pieces_original = [board.get_piece(s.row, s.col) for s in move_option['skipped'] if board.get_piece(s.row, s.col) != 0]
                found_matching_move = True
                break
        
        if not found_matching_move:
            return make_easy_bot_move(board, bot_color)
    
    if chosen_piece_original and chosen_move_pos:
        if board.get_piece(chosen_piece_original.row, chosen_piece_original.col) == chosen_piece_original:
             return chosen_piece_original, chosen_move_pos, skipped_pieces_original
        else:
            return make_easy_bot_move(board, bot_color) 
    else: 
        return None, None, []


# --- ГОЛОВНИЙ ЦИКЛ ГРИ ---
async def main():
    global game_state, CURRENT_GAME_MODE, PLAYER_HUMAN_COLOR, BOT_COLOR, CURRENT_BOT_DIFFICULTY, game_logs, game_result_message, turn

    run = True
    clock = pygame.time.Clock()

    board = Board()
    selected_piece = None
    valid_moves = {}
    turn = WHITE_PIECE 
    
    chained_capture_in_progress = None 

    game_logs = [""] 
    game_result_message = ""

    button_width, button_height = 250, 60
    button_y_offset = HEIGHT // 2 - button_height // 2 

    start_button_rect = pygame.Rect(WIDTH // 2 - button_width // 2, button_y_offset, button_width, button_height)
    vs_player_button_rect = pygame.Rect(WIDTH // 2 - button_width // 2, HEIGHT // 2 - button_height - 10, button_width, button_height)
    vs_bot_button_rect = pygame.Rect(WIDTH // 2 - button_width // 2, HEIGHT // 2 + 10, button_width, button_height)
    easy_button_rect = pygame.Rect(WIDTH // 2 - button_width // 2, HEIGHT // 2 - button_height * 1.5 - 20, button_width, button_height)
    medium_button_rect = pygame.Rect(WIDTH // 2 - button_width // 2, HEIGHT // 2 - button_height / 2 - 10, button_width, button_height)
    hard_button_rect = pygame.Rect(WIDTH // 2 - button_width // 2, HEIGHT // 2 + button_height / 2, button_width, button_height)
    white_color_button_rect = pygame.Rect(WIDTH // 2 - button_width // 2, HEIGHT // 2 - button_height - 10, button_width, button_height)
    black_color_button_rect = pygame.Rect(WIDTH // 2 - button_width // 2, HEIGHT // 2 + 10, button_width, button_height)
    restart_button_rect = pygame.Rect(WIDTH // 2 - button_width // 2, HEIGHT // 2 + 10, button_width, button_height)

    display_turn_indicator = True 

    while run:
        clock.tick(FPS) 
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                sys.exit()

            if game_state == MAIN_MENU:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if start_button_rect.collidepoint(event.pos):
                        game_state = PLAYER_VS_MODE_SELECTION
                continue

            if game_state == PLAYER_VS_MODE_SELECTION:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if vs_player_button_rect.collidepoint(event.pos):
                        CURRENT_GAME_MODE = MODE_VS_PLAYER
                        game_state = PLAYING
                        board = Board()
                        selected_piece = None
                        valid_moves = {}
                        turn = WHITE_PIECE 
                        game_logs = ["Початок гри! Білі ходять першими.", ""]
                        game_result_message = ""
                        display_turn_indicator = True 
                        chained_capture_in_progress = None
                    elif vs_bot_button_rect.collidepoint(event.pos):
                        CURRENT_GAME_MODE = MODE_VS_BOT
                        game_state = DIFFICULTY_SELECTION
                        display_turn_indicator = False 
                        chained_capture_in_progress = None
                continue

            if game_state == DIFFICULTY_SELECTION:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    difficulty_selected = False
                    if easy_button_rect.collidepoint(event.pos):
                        CURRENT_BOT_DIFFICULTY = DIFFICULTY_EASY
                        difficulty_selected = True
                    elif medium_button_rect.collidepoint(event.pos):
                        CURRENT_BOT_DIFFICULTY = DIFFICULTY_MEDIUM
                        difficulty_selected = True
                    elif hard_button_rect.collidepoint(event.pos):
                        CURRENT_BOT_DIFFICULTY = DIFFICULTY_HARD
                        difficulty_selected = True
                    
                    if difficulty_selected:
                        game_state = PLAYER_COLOR_SELECTION
                continue

            if game_state == PLAYER_COLOR_SELECTION:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    color_selected = False
                    if white_color_button_rect.collidepoint(event.pos):
                        PLAYER_HUMAN_COLOR = WHITE_PIECE
                        BOT_COLOR = BLACK_PIECE
                        turn = WHITE_PIECE 
                        color_selected = True
                    elif black_color_button_rect.collidepoint(event.pos):
                        PLAYER_HUMAN_COLOR = BLACK_PIECE
                        BOT_COLOR = WHITE_PIECE
                        turn = WHITE_PIECE
                        color_selected = True
                    
                    if color_selected:
                        game_state = PLAYING
                        board = Board()
                        selected_piece = None
                        valid_moves = {}
                        game_logs = ["Початок гри!", ""]
                        game_result_message = ""
                        chained_capture_in_progress = None
                        if turn == PLAYER_HUMAN_COLOR:
                            game_logs[0] = f"Початок гри! Гравець ({'Білі' if PLAYER_HUMAN_COLOR == WHITE_PIECE else 'Чорні'}) ходить першим."
                        else:
                            game_logs[0] = f"Початок гри! Бот ({'Білі' if BOT_COLOR == WHITE_PIECE else 'Чорні'}) ходить першим."
                continue 

            if game_state == GAME_OVER:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if restart_button_rect.collidepoint(event.pos):
                        game_state = MAIN_MENU
                        board = Board()
                        selected_piece = None
                        valid_moves = {}
                        turn = WHITE_PIECE
                        game_logs = [""]
                        game_result_message = ""
                        CURRENT_GAME_MODE = None
                        PLAYER_HUMAN_COLOR = None
                        BOT_COLOR = None
                        CURRENT_BOT_DIFFICULTY = None
                        display_turn_indicator = True 
                        chained_capture_in_progress = None
                continue

            if game_state == PLAYING:
                winner = board.winner()
                if winner is not None:
                    game_state = GAME_OVER
                    game_result_message = f"{'Білі' if winner == WHITE_PIECE else 'Чорні'} виграли!"
                    game_logs.append(f"Гру завершено: {game_result_message}")
                    continue 

                # Логіка ходу бота
                if CURRENT_GAME_MODE == MODE_VS_BOT and turn == BOT_COLOR:
                    if chained_capture_in_progress and chained_capture_in_progress[0].color == BOT_COLOR:
                        bot_piece_for_chain = chained_capture_in_progress[0]
                        potential_next_captures = board.valid_moves(bot_piece_for_chain)
                        next_captures_only = {pos: sk for pos, sk in potential_next_captures.items() if sk}

                        if next_captures_only:
                            chosen_next_move_pos = list(next_captures_only.keys())[0]
                            chosen_next_skipped = next_captures_only[chosen_next_move_pos]
                            actual_next_skipped_pieces = [board.get_piece(s.row, s.col) for s in chosen_next_skipped if board.get_piece(s.row, s.col) != 0]

                            board.move_piece(bot_piece_for_chain, chosen_next_move_pos[0], chosen_next_move_pos[1], actual_next_skipped_pieces)
                            game_logs[0] = f"Бот продовжив рубку з {bot_piece_for_chain.get_coords_str()} в ({chosen_next_move_pos[0]}, {chosen_next_move_pos[1]})."
                            game_logs[1] = f"Бот зрубав ще {len(actual_next_skipped_pieces)}."

                            piece_after_chain_move = board.get_piece(chosen_next_move_pos[0], chosen_next_move_pos[1])
                            further_captures_check = board.valid_moves(piece_after_chain_move)
                            can_capture_further = any(sk for _, sk in further_captures_check.items() if sk)

                            if can_capture_further:
                                chained_capture_in_progress = (piece_after_chain_move, actual_next_skipped_pieces)
                                turn = BOT_COLOR
                            else:
                                chained_capture_in_progress = None
                                turn = PLAYER_HUMAN_COLOR
                        else:
                            chained_capture_in_progress = None
                            turn = PLAYER_HUMAN_COLOR 
                        
                        selected_piece = None
                        valid_moves = {}
                        continue
                    
                    game_logs[1] = "Бот думає..."
                    WIN.fill(GREY)
                    board.draw(WIN)
                    draw_logs(WIN, game_logs)
                    pygame.display.update()
                    await asyncio.sleep(0.1)

                    bot_move_result = await bot_move(board, BOT_COLOR)
                    
                    if bot_move_result:
                        bot_selected_piece, bot_move_to_pos, bot_skipped_list = bot_move_result
                    else:
                        bot_selected_piece, bot_move_to_pos, bot_skipped_list = None, None, []

                    if bot_selected_piece and bot_move_to_pos:
                        actual_bot_piece = board.get_piece(bot_selected_piece.row, bot_selected_piece.col)
                        
                        if actual_bot_piece and actual_bot_piece.color == BOT_COLOR:
                            actual_skipped_for_bot_move = []
                            if bot_skipped_list:
                                for sp_obj in bot_skipped_list:
                                    if sp_obj and board.get_piece(sp_obj.row, sp_obj.col) == sp_obj:
                                        actual_skipped_for_bot_move.append(sp_obj)

                            board.move_piece(actual_bot_piece, bot_move_to_pos[0], bot_move_to_pos[1], actual_skipped_for_bot_move)
                            game_logs[0] = f"Бот походив з {actual_bot_piece.get_coords_str()} в ({bot_move_to_pos[0]}, {bot_move_to_pos[1]})."
                            
                            if actual_skipped_for_bot_move:
                                game_logs[1] = f"Бот зрубав {len(actual_skipped_for_bot_move)} шашок."
                                piece_after_bot_move = board.get_piece(bot_move_to_pos[0], bot_move_to_pos[1])
                                
                                if piece_after_bot_move:
                                    potential_chained_captures_bot = board.valid_moves(piece_after_bot_move)
                                    next_captures_for_bot = {pos: sk for pos, sk in potential_chained_captures_bot.items() if sk}

                                    if next_captures_for_bot:
                                        turn = BOT_COLOR 
                                        chained_capture_in_progress = (piece_after_bot_move, actual_skipped_for_bot_move) 
                                    else:
                                        turn = PLAYER_HUMAN_COLOR
                                        chained_capture_in_progress = None
                                else:
                                    turn = PLAYER_HUMAN_COLOR
                                    chained_capture_in_progress = None
                            else:
                                game_logs[1] = ""
                                turn = PLAYER_HUMAN_COLOR 
                                chained_capture_in_progress = None
                        else:
                            game_logs.append("Помилка бота: пропуск ходу.")
                            turn = PLAYER_HUMAN_COLOR
                            chained_capture_in_progress = None
                    else:
                        game_logs.append("Бот не знайшов хід. Пропуск ходу.")
                        turn = PLAYER_HUMAN_COLOR 
                        chained_capture_in_progress = None
                        if (bot_color == BLACK_PIECE and board.black_left > 0) or \
                           (bot_color == WHITE_PIECE and board.white_left > 0):
                            has_any_move_for_bot = False
                            for r in range(ROWS):
                                for c in range(COLS):
                                    p = board.get_piece(r,c)
                                    if p != 0 and p.color == bot_color:
                                        if board.valid_moves(p):
                                            has_any_move_for_bot = True; break
                                if has_any_move_for_bot: break
                            
                            if not has_any_move_for_bot:
                                game_state = GAME_OVER
                                game_result_message = f"Пат! {'Білі' if PLAYER_HUMAN_COLOR == WHITE_PIECE else 'Чорні'} (Гравець) виграли!"
                                game_logs.append(game_result_message)
                    
                    selected_piece = None
                    valid_moves = {}
                    continue

                # Логіка кліків гравця
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if CURRENT_GAME_MODE == MODE_VS_PLAYER or \
                       (CURRENT_GAME_MODE == MODE_VS_BOT and turn == PLAYER_HUMAN_COLOR):
                        
                        pos = pygame.mouse.get_pos()
                        row, col = get_row_col_from_mouse(pos)
                        
                        if row == -1 or col == -1:
                            if not chained_capture_in_progress:
                                selected_piece = None
                                valid_moves = {}
                            continue 

                        if selected_piece: 
                            if chained_capture_in_progress and selected_piece != chained_capture_in_progress[0]:
                                game_logs.append("Помилка: Завершіть серію рубок поточною шашкою.")
                                continue

                            if (row, col) in valid_moves: 
                                skipped_from_valid_moves = valid_moves[(row, col)]
                                
                                board.move_piece(selected_piece, row, col, skipped_from_valid_moves)
                                game_logs[0] = f"Хід з {selected_piece.get_coords_str()} в ({row}, {col})."
                                
                                if skipped_from_valid_moves:
                                    game_logs[1] = f"Зрубано: {len(skipped_from_valid_moves)} шашок."
                                    
                                    piece_after_player_move = board.get_piece(row, col)
                                    potential_chained_captures_player = board.valid_moves(piece_after_player_move)
                                    next_captures_for_player = {pos:sk for pos, sk in potential_chained_captures_player.items() if sk}

                                    if next_captures_for_player:
                                        game_logs[1] += " Продовжуйте рубати!"
                                        selected_piece = piece_after_player_move 
                                        valid_moves = next_captures_for_player 
                                        chained_capture_in_progress = (piece_after_player_move, skipped_from_valid_moves) 
                                    else:
                                        selected_piece = None
                                        valid_moves = {}
                                        chained_capture_in_progress = None
                                        if CURRENT_GAME_MODE == MODE_VS_PLAYER:
                                            turn = BLACK_PIECE if turn == WHITE_PIECE else WHITE_PIECE
                                        else:
                                            turn = BOT_COLOR 
                                else:
                                    game_logs[1] = ""
                                    selected_piece = None
                                    valid_moves = {}
                                    chained_capture_in_progress = None
                                    if CURRENT_GAME_MODE == MODE_VS_PLAYER:
                                        turn = BLACK_PIECE if turn == WHITE_PIECE else WHITE_PIECE
                                    else:
                                        turn = BOT_COLOR
                                    
                            else:
                                if chained_capture_in_progress:
                                    game_logs.append("Помилка: Ви повинні зробити рубку.")
                                else: 
                                    piece_clicked = board.get_piece(row, col)
                                    if piece_clicked != 0 and piece_clicked.color == turn: 
                                        selected_piece = piece_clicked
                                        valid_moves = board.valid_moves(selected_piece)
                                    else: 
                                        selected_piece = None
                                        valid_moves = {}
                        else:
                            piece_clicked = board.get_piece(row, col)
                            if piece_clicked != 0 and piece_clicked.color == turn: 
                                must_make_capture_somewhere = False
                                for r_check in range(ROWS):
                                    for c_check in range(COLS):
                                        p_check = board.get_piece(r_check, c_check)
                                        if p_check != 0 and p_check.color == turn:
                                            moves_for_p_check = board.valid_moves(p_check)
                                            if any(sk for _, sk in moves_for_p_check.items() if sk):
                                                must_make_capture_somewhere = True; break
                                    if must_make_capture_somewhere: break
                                
                                current_piece_can_capture = any(sk for _, sk in board.valid_moves(piece_clicked).items() if sk)

                                if must_make_capture_somewhere and not current_piece_can_capture:
                                    game_logs.append("Помилка: Ви зобов'язані рубати іншою шашкою!")
                                    selected_piece = None
                                    valid_moves = {}
                                else:
                                    selected_piece = piece_clicked
                                    valid_moves = board.valid_moves(selected_piece)
                                    if not valid_moves and must_make_capture_somewhere:
                                        game_logs.append("Помилка: Обрана шашка без ходів, але є обов'язкові рубки!")
                                        selected_piece = None
                
        if game_state == MAIN_MENU:
            draw_main_menu(WIN, start_button_rect)
        elif game_state == PLAYER_VS_MODE_SELECTION:
            draw_player_vs_mode_selection_screen(WIN, vs_player_button_rect, vs_bot_button_rect)
        elif game_state == DIFFICULTY_SELECTION:
            draw_difficulty_selection_screen(WIN, easy_button_rect, medium_button_rect, hard_button_rect)
        elif game_state == PLAYER_COLOR_SELECTION:
            draw_player_color_selection_screen(WIN, white_color_button_rect, black_color_button_rect)
        elif game_state == PLAYING:
            WIN.fill(GREY)
            board.draw(WIN)

            if display_turn_indicator or (CURRENT_GAME_MODE == MODE_VS_PLAYER):
                turn_text_str = ""
                if turn == WHITE_PIECE: turn_text_str = "Хід Білих"
                else: turn_text_str = "Хід Чорних"

                if CURRENT_GAME_MODE == MODE_VS_BOT:
                    if turn == PLAYER_HUMAN_COLOR: turn_text_str += " (Гравець)"
                    else: turn_text_str += " (Бот)"
                
                turn_text_color = WHITE_PIECE if turn == WHITE_PIECE else BLACK_PIECE
                text_surf = SMALL_FONT.render(turn_text_str, True, turn_text_color)
                text_rect = text_surf.get_rect(topleft=(MARGIN, MARGIN - SMALL_FONT.get_height() - 5))
                pygame.draw.rect(WIN, GREY, text_rect.inflate(4,4))
                WIN.blit(text_surf, text_rect)

            if selected_piece:
                actual_selected = board.get_piece(selected_piece.row, selected_piece.col)
                if actual_selected == selected_piece:
                    radius = SQUARE_SIZE // 2 - selected_piece.PADDING
                    pygame.draw.circle(WIN, HIGHLIGHT_GREEN, (selected_piece.x, selected_piece.y),
                                       radius + selected_piece.OUTLINE * 2, selected_piece.OUTLINE * 2)

                    if valid_moves:
                        for move_pos in valid_moves:
                            r_vm, c_vm = move_pos
                            pygame.draw.circle(WIN, HIGHLIGHT_GREEN, (c_vm * SQUARE_SIZE + SQUARE_SIZE // 2 + MARGIN,
                                                                      r_vm * SQUARE_SIZE + SQUARE_SIZE // 2 + MARGIN), 15)
                else:
                    selected_piece = None
                    valid_moves = {}

            draw_logs(WIN, game_logs)
            pygame.display.update()
        elif game_state == GAME_OVER:
            draw_end_game_screen(WIN, game_result_message, restart_button_rect)

        await asyncio.sleep(0) 

if __name__ == "__main__":
    asyncio.run(main())