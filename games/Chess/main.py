import pygame
import os
import random
import asyncio

# --- Конфігурація шляху до фігур ---
FIGURES_FOLDER = "figures"

# Ініціалізація Pygame
pygame.init()
pygame.font.init()

# --- Розміри та розташування елементів ---
BOARD_SIZE_PX = 640
SQUARE_SIZE = BOARD_SIZE_PX // 8
NOTATION_AREA_SIZE = 30
LOG_AREA_WIDTH = 220
PADDING = 10

SCREEN_WIDTH = NOTATION_AREA_SIZE + BOARD_SIZE_PX + LOG_AREA_WIDTH + PADDING * 2
SCREEN_HEIGHT = NOTATION_AREA_SIZE + BOARD_SIZE_PX + NOTATION_AREA_SIZE

BOARD_START_X = NOTATION_AREA_SIZE
BOARD_START_Y = NOTATION_AREA_SIZE
LOG_START_X = BOARD_START_X + BOARD_SIZE_PX + PADDING
LOG_START_Y = BOARD_START_Y

SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Шахи")

# --- Кольори ---
BACKGROUND_COLOR = (45, 52, 54)
GAME_BACKGROUND_COLOR = (210, 218, 226)
WHITE_COL = (255, 255, 255)
BLACK_COL = (45, 52, 54)
LIGHT_BROWN = (236, 217, 185)
DARK_BROWN = (174, 137, 104)
HIGHLIGHT_COLOR = (130, 170, 150, 150)
CHECK_COLOR = (214, 115, 115, 150)
BUTTON_COLOR_NORMAL = (99, 110, 114)
BUTTON_COLOR_HOVER = (129, 140, 144)
BUTTON_TEXT_COLOR = WHITE_COL
LOG_BG_COLOR = (222, 226, 230)
GAME_OVER_OVERLAY_COLOR = (45, 52, 54, 180)

# --- Цінність фігур для бота ---
PIECE_VALUES = {"pawn": 10, "knight": 30, "bishop": 30, "rook": 50, "queen": 90, "king": 0}

# --- Шрифти ---
font_name = "georgia"
MENU_TITLE_FONT = pygame.font.SysFont(font_name, 70)
MENU_BUTTON_FONT = pygame.font.SysFont(font_name, 40)
NOTATION_FONT_SIZE = 20
LOG_FONT_SIZE = 18
GAME_OVER_FONT = pygame.font.SysFont(font_name, 60)
RESTART_BUTTON_FONT = pygame.font.SysFont(font_name, 40)
NOTATION_FONT = pygame.font.SysFont(font_name, NOTATION_FONT_SIZE)
LOG_FONT = pygame.font.SysFont(font_name, LOG_FONT_SIZE)

# --- Завантаження зображень фігур ---
FIGURES = {}
if not os.path.isdir(FIGURES_FOLDER):
    print(f"Помилка: Папка з фігурами '{FIGURES_FOLDER}' не знайдена.")
else:
    print(f"Використовується папка з фігурами: '{FIGURES_FOLDER}'")

piece_names_list_for_loading = [
    "black_king", "black_queen", "black_rook", "black_bishop", "black_knight", "black_pawn",
    "white_king", "white_queen", "white_rook", "white_bishop", "white_knight", "white_pawn"
]
for name in piece_names_list_for_loading:
    path = os.path.join(FIGURES_FOLDER, f"{name}.png")
    try:
        image = pygame.image.load(path).convert_alpha()
        FIGURES[name] = pygame.transform.scale(image, (SQUARE_SIZE, SQUARE_SIZE))
    except pygame.error as e:
        print(f"Помилка завантаження зображення {path}: {e}")
        FIGURES[name] = None

# --- Початкові стани гри ---
INITIAL_BOARD = [
    ["black_rook", "black_knight", "black_bishop", "black_queen", "black_king", "black_bishop", "black_knight", "black_rook"],
    ["black_pawn", "black_pawn", "black_pawn", "black_pawn", "black_pawn", "black_pawn", "black_pawn", "black_pawn"],
    [None, None, None, None, None, None, None, None],
    [None, None, None, None, None, None, None, None],
    [None, None, None, None, None, None, None, None],
    [None, None, None, None, None, None, None, None],
    ["white_pawn", "white_pawn", "white_pawn", "white_pawn", "white_pawn", "white_pawn", "white_pawn", "white_pawn"],
    ["white_rook", "white_knight", "white_bishop", "white_queen", "white_king", "white_bishop", "white_knight", "white_rook"]
]
INITIAL_CASTLING_RIGHTS = {
    "white": {"king_moved": False, "rook_h1_moved": False, "rook_a1_moved": False},
    "black": {"king_moved": False, "rook_h8_moved": False, "rook_a8_moved": False}
}

# --- Змінні стану гри та меню ---
BOARD, castling_rights, selected_piece, possible_moves, in_check, current_turn, game_state, move_log = [], {}, None, [], None, "", "", []
game_mode = None
bot_difficulty = None
player_chosen_color = None
bot_color = None
bot_is_thinking = False
bot_thinking_message = ""

white_king_button_img, black_king_button_img = None, None
PIECE_BUTTON_SIZE = (SQUARE_SIZE, SQUARE_SIZE)
if FIGURES.get("white_king"):
    white_king_button_img = pygame.transform.scale(FIGURES["white_king"], PIECE_BUTTON_SIZE)
if FIGURES.get("black_king"):
    black_king_button_img = pygame.transform.scale(FIGURES["black_king"], PIECE_BUTTON_SIZE)

MENU_BUTTON_WIDTH = 420
MENU_BUTTON_HEIGHT = 50
MENU_BUTTON_SPACING = 20
btn_start_game = pygame.Rect(SCREEN_WIDTH // 2 - MENU_BUTTON_WIDTH // 2, SCREEN_HEIGHT // 2 - MENU_BUTTON_HEIGHT // 2, MENU_BUTTON_WIDTH, MENU_BUTTON_HEIGHT)
btn_pvp = pygame.Rect(SCREEN_WIDTH // 2 - MENU_BUTTON_WIDTH // 2, SCREEN_HEIGHT // 2 - MENU_BUTTON_HEIGHT - MENU_BUTTON_SPACING // 2, MENU_BUTTON_WIDTH, MENU_BUTTON_HEIGHT)
btn_pve = pygame.Rect(SCREEN_WIDTH // 2 - MENU_BUTTON_WIDTH // 2, SCREEN_HEIGHT // 2 + MENU_BUTTON_SPACING // 2, MENU_BUTTON_WIDTH, MENU_BUTTON_HEIGHT)
btn_easy = pygame.Rect(SCREEN_WIDTH // 2 - MENU_BUTTON_WIDTH // 2, SCREEN_HEIGHT // 2 - MENU_BUTTON_HEIGHT * 1.5 - MENU_BUTTON_SPACING, MENU_BUTTON_WIDTH, MENU_BUTTON_HEIGHT)
btn_medium = pygame.Rect(SCREEN_WIDTH // 2 - MENU_BUTTON_WIDTH // 2, SCREEN_HEIGHT // 2 - MENU_BUTTON_HEIGHT * 0.5, MENU_BUTTON_WIDTH, MENU_BUTTON_HEIGHT)
btn_hard = pygame.Rect(SCREEN_WIDTH // 2 - MENU_BUTTON_WIDTH // 2, SCREEN_HEIGHT // 2 + MENU_BUTTON_HEIGHT * 0.5 + MENU_BUTTON_SPACING, MENU_BUTTON_WIDTH, MENU_BUTTON_HEIGHT)
btn_choose_white = pygame.Rect(SCREEN_WIDTH // 2 - PIECE_BUTTON_SIZE[0] - MENU_BUTTON_SPACING, SCREEN_HEIGHT // 2, PIECE_BUTTON_SIZE[0], PIECE_BUTTON_SIZE[1])
btn_choose_black = pygame.Rect(SCREEN_WIDTH // 2 + MENU_BUTTON_SPACING, SCREEN_HEIGHT // 2, PIECE_BUTTON_SIZE[0], PIECE_BUTTON_SIZE[1])
btn_back = pygame.Rect(PADDING, SCREEN_HEIGHT - MENU_BUTTON_HEIGHT - PADDING, 100, MENU_BUTTON_HEIGHT)

# --- Допоміжні функції ---
def get_piece_color(piece_name):
    if piece_name: return piece_name.split('_')[0]
    return None

def get_piece_type(piece_name):
    if piece_name: return piece_name.split('_')[1]
    return None

def is_valid_coord(row, col):
    return 0 <= row < 8 and 0 <= col < 8

def get_king_pos(color, board_state):
    for r in range(8):
        for c in range(8):
            if board_state[r][c] == f"{color}_king": return (r, c)
    return None

def is_square_attacked(row, col, attacking_color, current_board):
    pawn_direction = -1 if attacking_color == "white" else 1
    for dc_pawn in [-1, 1]:
        p_row, p_col = row - pawn_direction, col + dc_pawn
        if is_valid_coord(p_row, p_col) and current_board[p_row][p_col] == f"{attacking_color}_pawn": return True
    knight_moves_list = [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]
    for dr_k, dc_k in knight_moves_list:
        n_row, n_col = row + dr_k, col + dc_k
        if is_valid_coord(n_row, n_col) and current_board[n_row][n_col] == f"{attacking_color}_knight": return True
    straight_directions_list = [(0,1),(0,-1),(1,0),(-1,0)]
    for dr_s, dc_s in straight_directions_list:
        for i_s in range(1,8):
            t_row_s, t_col_s = row + dr_s*i_s, col + dc_s*i_s
            if not is_valid_coord(t_row_s,t_col_s): break
            piece_s = current_board[t_row_s][t_col_s]
            if piece_s:
                if get_piece_color(piece_s)==attacking_color and (get_piece_type(piece_s)=="rook" or get_piece_type(piece_s)=="queen"): return True
                break
    diag_directions_list = [(1,1),(1,-1),(-1,1),(-1,-1)]
    for dr_d, dc_d in diag_directions_list:
        for i_d in range(1,8):
            t_row_d, t_col_d = row + dr_d*i_d, col + dc_d*i_d
            if not is_valid_coord(t_row_d,t_col_d): break
            piece_d = current_board[t_row_d][t_col_d]
            if piece_d:
                if get_piece_color(piece_d)==attacking_color and (get_piece_type(piece_d)=="bishop" or get_piece_type(piece_d)=="queen"): return True
                break
    king_moves_list_isa = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
    for dr_kg, dc_kg in king_moves_list_isa:
        k_row, k_col = row + dr_kg, col + dc_kg
        if is_valid_coord(k_row, k_col) and current_board[k_row][k_col] == f"{attacking_color}_king": return True
    return False

def check_for_check(board_state_to_check, color_to_check):
    king_pos_val = get_king_pos(color_to_check, board_state_to_check)
    if king_pos_val is None: return False
    king_row, king_col = king_pos_val
    opponent_color_val = "white" if color_to_check == "black" else "black"
    return is_square_attacked(king_row, king_col, opponent_color_val, board_state_to_check)

def add_move_if_valid(moves_list_param, current_r, current_c, target_r, target_c, p_color, board_state_param):
    if not is_valid_coord(target_r, target_c): return False
    target_piece_val = board_state_param[target_r][target_c]
    target_color_val = get_piece_color(target_piece_val)
    if target_piece_val is None:
        moves_list_param.append((target_r, target_c))
        return True
    elif target_color_val != p_color:
        moves_list_param.append((target_r, target_c))
        return False
    return False

def get_possible_moves(row_param, col_param, board_state_param, current_castling_rights_param):
    moves_list_gpm = []
    piece_name_gpm = board_state_param[row_param][col_param]
    if not piece_name_gpm: return moves_list_gpm
    
    piece_color_gpm = get_piece_color(piece_name_gpm)
    piece_type_gpm = get_piece_type(piece_name_gpm)
    
    if piece_type_gpm == "pawn":
        direction_pawn = -1 if piece_color_gpm == "white" else 1
        target_row_one_step = row_param + direction_pawn
        if is_valid_coord(target_row_one_step, col_param) and board_state_param[target_row_one_step][col_param] is None:
            moves_list_gpm.append((target_row_one_step, col_param))
            if (piece_color_gpm == "white" and row_param == 6) or (piece_color_gpm == "black" and row_param == 1):
                target_row_two_steps = row_param + 2 * direction_pawn
                if is_valid_coord(target_row_two_steps, col_param) and board_state_param[target_row_two_steps][col_param] is None:
                    moves_list_gpm.append((target_row_two_steps, col_param))
        for dc_pawn_cap in [-1, 1]:
            target_row_capture = row_param + direction_pawn
            target_col_capture = col_param + dc_pawn_cap
            if is_valid_coord(target_row_capture, target_col_capture):
                target_piece_cap = board_state_param[target_row_capture][target_col_capture]
                if target_piece_cap and get_piece_color(target_piece_cap) != piece_color_gpm:
                    moves_list_gpm.append((target_row_capture, target_col_capture))
    elif piece_type_gpm == "rook":
        directions_list_linear = [(0,1),(0,-1),(1,0),(-1,0)]
        for dr_r, dc_r in directions_list_linear:
            for i_r in range(1,8):
                if not add_move_if_valid(moves_list_gpm, row_param, col_param, row_param+dr_r*i_r, col_param+dc_r*i_r, piece_color_gpm, board_state_param): break
    elif piece_type_gpm == "knight":
        knight_moves_gpm_list = [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]
        for dr_kn, dc_kn in knight_moves_gpm_list:
            add_move_if_valid(moves_list_gpm, row_param, col_param, row_param+dr_kn, col_param+dc_kn, piece_color_gpm, board_state_param)
    elif piece_type_gpm == "bishop":
        directions_list_diag = [(1,1),(1,-1),(-1,1),(-1,-1)]
        for dr_b, dc_b in directions_list_diag:
            for i_b in range(1,8):
                if not add_move_if_valid(moves_list_gpm, row_param, col_param, row_param+dr_b*i_b, col_param+dc_b*i_b, piece_color_gpm, board_state_param): break
    elif piece_type_gpm == "queen":
        directions_list_all = [(0,1),(0,-1),(1,0),(-1,0),(1,1),(1,-1),(-1,1),(-1,-1)]
        for dr_q, dc_q in directions_list_all:
            for i_q in range(1,8):
                if not add_move_if_valid(moves_list_gpm, row_param, col_param, row_param+dr_q*i_q, col_param+dc_q*i_q, piece_color_gpm, board_state_param): break
    elif piece_type_gpm == "king":
        king_moves_gpm_direct = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
        for dr_kg_gpm, dc_kg_gpm in king_moves_gpm_direct:
            add_move_if_valid(moves_list_gpm, row_param, col_param, row_param+dr_kg_gpm, col_param+dc_kg_gpm, piece_color_gpm, board_state_param)
        king_start_row_gpm = 7 if piece_color_gpm == "white" else 0
        if not current_castling_rights_param[piece_color_gpm]["king_moved"] and row_param == king_start_row_gpm and col_param == 4:
            kingside_rook_key = "rook_h1_moved" if piece_color_gpm == "white" else "rook_h8_moved"
            queenside_rook_key = "rook_a1_moved" if piece_color_gpm == "white" else "rook_a8_moved"
            if not current_castling_rights_param[piece_color_gpm][kingside_rook_key] and board_state_param[king_start_row_gpm][5] is None and board_state_param[king_start_row_gpm][6] is None:
                moves_list_gpm.append((king_start_row_gpm, 6))
            if not current_castling_rights_param[piece_color_gpm][queenside_rook_key] and board_state_param[king_start_row_gpm][1] is None and board_state_param[king_start_row_gpm][2] is None and board_state_param[king_start_row_gpm][3] is None:
                moves_list_gpm.append((king_start_row_gpm, 2))

    valid_moves_after_filter_gpm = []
    for move_r_gpm, move_c_gpm in moves_list_gpm:
        temp_board_gpm = [r[:] for r in board_state_param]
        moved_piece_temp_gpm = temp_board_gpm[row_param][col_param]
        temp_board_gpm[move_r_gpm][move_c_gpm] = moved_piece_temp_gpm
        temp_board_gpm[row_param][col_param] = None
        
        if get_piece_type(moved_piece_temp_gpm) == "king" and abs(move_c_gpm - col_param) == 2:
            opponent_color_gpm = "black" if piece_color_gpm == "white" else "white"
            if is_square_attacked(row_param, col_param, opponent_color_gpm, board_state_param):
                continue 
            path_col = 5 if move_c_gpm == 6 else 3
            if is_square_attacked(row_param, path_col, opponent_color_gpm, board_state_param):
                continue 
            k_orig_row_gpm = row_param
            rook_name_temp_gpm = f"{piece_color_gpm}_rook"
            if move_c_gpm == 6: 
                temp_board_gpm[k_orig_row_gpm][5] = rook_name_temp_gpm
                temp_board_gpm[k_orig_row_gpm][7] = None
            elif move_c_gpm == 2: 
                temp_board_gpm[k_orig_row_gpm][3] = rook_name_temp_gpm
                temp_board_gpm[k_orig_row_gpm][0] = None
        
        if not check_for_check(temp_board_gpm, piece_color_gpm):
            valid_moves_after_filter_gpm.append((move_r_gpm, move_c_gpm))
            
    return valid_moves_after_filter_gpm

def to_algebraic(row, col):
    return 'abcdefgh'[col] + '87654321'[row]

def get_move_notation_str(piece_name, start_pos_alg, end_pos_alg, is_capture, is_castling_type=None):
    if is_castling_type:
        return is_castling_type
    p_type = get_piece_type(piece_name)
    piece_char = ''
    if p_type == "knight": piece_char = "N"
    elif p_type == "rook": piece_char = "R"
    elif p_type == "bishop": piece_char = "B"
    elif p_type == "queen": piece_char = "Q"
    elif p_type == "king": piece_char = "K"
    return f"{piece_char}{start_pos_alg}{'x' if is_capture else '–'}{end_pos_alg}"

# --- Функції малювання ---
def draw_board_and_notations():
    for r_idx in range(8):
        for c_idx in range(8):
            color = LIGHT_BROWN if (r_idx + c_idx) % 2 == 0 else DARK_BROWN
            pygame.draw.rect(SCREEN, color, (BOARD_START_X + c_idx * SQUARE_SIZE, BOARD_START_Y + r_idx * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
    letters = 'abcdefgh'
    numbers_chess = '87654321'
    for i in range(8):
        letter_surf = NOTATION_FONT.render(letters[i], True, BLACK_COL)
        letter_rect = letter_surf.get_rect(center=(BOARD_START_X + i * SQUARE_SIZE + SQUARE_SIZE // 2, BOARD_START_Y + BOARD_SIZE_PX + NOTATION_AREA_SIZE // 2))
        SCREEN.blit(letter_surf, letter_rect)
        letter_rect_top = letter_surf.get_rect(center=(BOARD_START_X + i * SQUARE_SIZE + SQUARE_SIZE // 2, BOARD_START_Y - NOTATION_AREA_SIZE // 2))
        SCREEN.blit(letter_surf, letter_rect_top)
        number_surf = NOTATION_FONT.render(numbers_chess[i], True, BLACK_COL)
        number_rect = number_surf.get_rect(center=(BOARD_START_X - NOTATION_AREA_SIZE // 2, BOARD_START_Y + i * SQUARE_SIZE + SQUARE_SIZE // 2))
        SCREEN.blit(number_surf, number_rect)
        number_rect_right = number_surf.get_rect(center=(BOARD_START_X + BOARD_SIZE_PX + NOTATION_AREA_SIZE // 2, BOARD_START_Y + i * SQUARE_SIZE + SQUARE_SIZE // 2))
        SCREEN.blit(number_surf, number_rect_right)

def draw_pieces():
    for r_idx in range(8):
        for c_idx in range(8):
            piece_name_draw = BOARD[r_idx][c_idx]
            if piece_name_draw and FIGURES.get(piece_name_draw):
                SCREEN.blit(FIGURES[piece_name_draw], (BOARD_START_X + c_idx * SQUARE_SIZE, BOARD_START_Y + r_idx * SQUARE_SIZE))

def draw_highlight():
    if selected_piece:
        r_idx, c_idx = selected_piece
        s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
        s.fill(HIGHLIGHT_COLOR)
        SCREEN.blit(s, (BOARD_START_X + c_idx * SQUARE_SIZE, BOARD_START_Y + r_idx * SQUARE_SIZE))
    if possible_moves:
        for mr, mc in possible_moves:
            s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            s.fill(HIGHLIGHT_COLOR)
            SCREEN.blit(s, (BOARD_START_X + mc * SQUARE_SIZE, BOARD_START_Y + mr * SQUARE_SIZE))
    if in_check:
        king_pos_draw = get_king_pos(in_check, BOARD)
        if king_pos_draw:
            kr, kc = king_pos_draw
            s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            s.fill(CHECK_COLOR)
            SCREEN.blit(s, (BOARD_START_X + kc * SQUARE_SIZE, BOARD_START_Y + kr * SQUARE_SIZE))

def draw_game_log():
    log_area_rect = pygame.Rect(LOG_START_X, LOG_START_Y, LOG_AREA_WIDTH, BOARD_SIZE_PX)
    pygame.draw.rect(SCREEN, LOG_BG_COLOR, log_area_rect)
    pygame.draw.rect(SCREEN, BLACK_COL, log_area_rect, 2)
    y_pos_log = LOG_START_Y + 5
    max_log_height = LOG_START_Y + BOARD_SIZE_PX - 25 
    start_index_log = 0
    
    available_height = max_log_height - y_pos_log
    num_moves_to_display = 0
    if LOG_FONT_SIZE > 0:
        num_moves_to_display = available_height // (LOG_FONT_SIZE + 2)
    
    total_pairs_log = (len(move_log) + 1) // 2
    if total_pairs_log > num_moves_to_display:
        start_index_log = (total_pairs_log - num_moves_to_display) * 2

    for i_log_draw in range(start_index_log, len(move_log), 2):
        move_number_log = (i_log_draw // 2) + 1
        white_m_log = move_log[i_log_draw]
        black_m_log = move_log[i_log_draw+1] if (i_log_draw+1) < len(move_log) else ""
        line_text_log = f"{move_number_log}. {white_m_log}  {black_m_log}"
        text_surf_log = LOG_FONT.render(line_text_log, True, BLACK_COL)
        if y_pos_log + LOG_FONT_SIZE <= max_log_height:
            SCREEN.blit(text_surf_log, (LOG_START_X + 5, y_pos_log))
            y_pos_log += (LOG_FONT_SIZE + 2)
        else: break
    
    if bot_thinking_message:
        msg_surf = LOG_FONT.render(bot_thinking_message, True, BLACK_COL)
        msg_rect = msg_surf.get_rect(centerx=log_area_rect.centerx, bottom=log_area_rect.bottom - 5)
        SCREEN.blit(msg_surf, msg_rect)

def draw_game_over_screen():
    current_go_btn_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 20, 200, 50)
    if game_state != 'playing' and "menu" not in game_state:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill(GAME_OVER_OVERLAY_COLOR)
        SCREEN.blit(overlay, (0,0))
        text_content_go = ""
        if "checkmate" in game_state:
            winner_color_go = "Білих" if game_state.split('_')[1] == "white" else "Чорних"
            text_content_go = f"Мат! Перемога за {winner_color_go}!"
        elif "stalemate" in game_state:
            text_content_go = "Пат! Нічия!"
        
        text_surface_go = GAME_OVER_FONT.render(text_content_go, True, WHITE_COL)
        text_rect_go = text_surface_go.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 60))
        SCREEN.blit(text_surface_go, text_rect_go)
        
        draw_button(current_go_btn_rect, "В меню", pygame.mouse.get_pos(), font_param=RESTART_BUTTON_FONT)
    return current_go_btn_rect

def draw_text(text_str, font_obj, color_obj, surface_obj, x_pos, y_pos, center_x=True, center_y=True):
    text_obj_draw = font_obj.render(text_str, True, color_obj)
    text_rect_draw = text_obj_draw.get_rect()
    if center_x and center_y: text_rect_draw.center = (x_pos, y_pos)
    elif center_x: text_rect_draw.midtop = (x_pos, y_pos); text_rect_draw.y = y_pos
    else: text_rect_draw.topleft = (x_pos,y_pos)
    surface_obj.blit(text_obj_draw, text_rect_draw)

def draw_button(rect_param, text_param, mouse_pos_param, surface_param=SCREEN, normal_color=BUTTON_COLOR_NORMAL, hover_color=BUTTON_COLOR_HOVER, font_param=MENU_BUTTON_FONT, text_color_param=BUTTON_TEXT_COLOR, radius=10):
    color_btn = hover_color if rect_param.collidepoint(mouse_pos_param) else normal_color
    pygame.draw.rect(surface_param, color_btn, rect_param, border_radius=radius)
    pygame.draw.rect(surface_param, (0,0,0,50), rect_param.inflate(2,2), 1, radius)
    draw_text(text_param, font_param, text_color_param, surface_param, rect_param.centerx, rect_param.centery)

def draw_image_button(rect_img_btn, image_param, mouse_pos_img_btn, surface_img_btn=SCREEN, hover_increase=30, border_rad=5):
    if image_param is None: return
    base_image_btn = image_param.copy()
    if rect_img_btn.collidepoint(mouse_pos_img_btn):
        brighter_image_btn = image_param.copy()
        brighter_image_btn.fill((hover_increase, hover_increase, hover_increase), special_flags=pygame.BLEND_RGB_ADD)
        surface_img_btn.blit(brighter_image_btn, rect_img_btn.topleft)
        pygame.draw.rect(surface_img_btn, BUTTON_COLOR_HOVER, rect_img_btn, 2, border_radius=border_rad)
    else:
        surface_img_btn.blit(base_image_btn, rect_img_btn.topleft)
        pygame.draw.rect(surface_img_btn, BUTTON_COLOR_NORMAL, rect_img_btn, 1, border_radius=border_rad)

def draw_main_menu(mouse_pos_mm):
    draw_text("Шахи", MENU_TITLE_FONT, BLACK_COL, SCREEN, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4)
    draw_button(btn_start_game, "Почати гру", mouse_pos_mm)

def draw_mode_selection_menu(mouse_pos_msm):
    draw_text("Оберіть режим", MENU_TITLE_FONT, BLACK_COL, SCREEN, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4)
    draw_button(btn_pvp, "Гравець проти гравця", mouse_pos_msm)
    draw_button(btn_pve, "Гравець проти бота", mouse_pos_msm)
    draw_button(btn_back, "Назад", mouse_pos_msm)

def draw_bot_difficulty_menu(mouse_pos_bdm):
    draw_text("Оберіть складність", MENU_TITLE_FONT, BLACK_COL, SCREEN, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4)
    draw_button(btn_easy, "Легка", mouse_pos_bdm)
    draw_button(btn_medium, "Середня", mouse_pos_bdm)
    draw_button(btn_hard, "Висока", mouse_pos_bdm)
    draw_button(btn_back, "Назад", mouse_pos_bdm)

def draw_bot_color_menu(mouse_pos_bcm):
    draw_text("Оберіть колір", MENU_TITLE_FONT, BLACK_COL, SCREEN, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4)
    draw_image_button(btn_choose_white, white_king_button_img, mouse_pos_bcm)
    draw_image_button(btn_choose_black, black_king_button_img, mouse_pos_bcm)
    draw_button(btn_back, "Назад", mouse_pos_bcm)

# --- Логіка гри ---
def check_game_over_conditions(player_to_check_color_cgoc):
    global game_state
    if game_state != 'playing': return 
    all_legal_moves_for_player_cgoc = get_all_valid_moves_for_bot(BOARD, player_to_check_color_cgoc, castling_rights)
    if not all_legal_moves_for_player_cgoc: 
        king_is_currently_in_check_cgoc = check_for_check(BOARD, player_to_check_color_cgoc)
        if king_is_currently_in_check_cgoc:
            winner_cgoc = "white" if player_to_check_color_cgoc == "black" else "black"
            game_state = f"checkmate_{winner_cgoc}_wins"
        else:
            game_state = "stalemate_draw"
            
def make_move(start_pos_mm, end_pos_mm):
    global in_check, current_turn, game_state, move_log, castling_rights, BOARD, selected_piece, possible_moves
    start_row_mm, start_col_mm = start_pos_mm
    end_row_mm, end_col_mm = end_pos_mm
    
    moved_piece_name_mm = BOARD[start_row_mm][start_col_mm]
    start_pos_alg_mm = to_algebraic(start_row_mm, start_col_mm)
    end_pos_alg_mm = to_algebraic(end_row_mm, end_col_mm)
    is_capture_mm = BOARD[end_row_mm][end_col_mm] is not None
    castling_type_for_log_mm = None

    piece_mm = BOARD[start_row_mm][start_col_mm]
    piece_color_mm = get_piece_color(piece_mm)
    piece_type_mm = get_piece_type(piece_mm)

    if piece_type_mm == "king": castling_rights[piece_color_mm]["king_moved"] = True
    elif piece_type_mm == "rook":
        if piece_color_mm=="white":
            if start_row_mm==7 and start_col_mm==0: castling_rights["white"]["rook_a1_moved"]=True
            elif start_row_mm==7 and start_col_mm==7: castling_rights["white"]["rook_h1_moved"]=True
        elif piece_color_mm=="black":
            if start_row_mm==0 and start_col_mm==0: castling_rights["black"]["rook_a8_moved"]=True
            elif start_row_mm==0 and start_col_mm==7: castling_rights["black"]["rook_h8_moved"]=True
    
    if piece_type_mm == "king" and abs(end_col_mm - start_col_mm) == 2:
        rook_orig_c_mm, rook_target_c_mm = (7,5) if end_col_mm==6 else (0,3)
        BOARD[start_row_mm][rook_target_c_mm] = BOARD[start_row_mm][rook_orig_c_mm]
        BOARD[start_row_mm][rook_orig_c_mm] = None
        castling_type_for_log_mm = "O-O" if end_col_mm == 6 else "O-O-O"

    BOARD[end_row_mm][end_col_mm] = piece_mm
    BOARD[start_row_mm][start_col_mm] = None
    
    current_move_str_mm = get_move_notation_str(moved_piece_name_mm, start_pos_alg_mm, end_pos_alg_mm, is_capture_mm, castling_type_for_log_mm)
    
    opponent_color_mm = "white" if piece_color_mm == "black" else "black"
    is_opponent_in_check_after_move_mm = check_for_check(BOARD, opponent_color_mm)
    
    if is_opponent_in_check_after_move_mm:
        in_check = opponent_color_mm
    else: in_check = None
    
    current_turn = opponent_color_mm 
    check_game_over_conditions(current_turn)

    if "checkmate" in game_state: current_move_str_mm += "#"
    elif is_opponent_in_check_after_move_mm: current_move_str_mm += "+"
    
    move_log.append(current_move_str_mm)
    selected_piece = None
    possible_moves = []
    return True

def initialize_game_board_state():
    global BOARD, castling_rights, current_turn, selected_piece, possible_moves, in_check, move_log, bot_color, game_mode, player_chosen_color, game_state, bot_is_thinking
    BOARD = [row[:] for row in INITIAL_BOARD]
    castling_rights = {color: rights.copy() for color, rights in INITIAL_CASTLING_RIGHTS.items()}
    current_turn = "white"
    selected_piece = None
    possible_moves = []
    in_check = None
    move_log = []
    bot_is_thinking = False
    
    if game_mode == 'pve':
        if player_chosen_color == 'white':
            bot_color = 'black'
        else:
            bot_color = 'white'
    else:
        bot_color = None
    
# --- Логіка бота ---
def evaluate_board_state_minimax(board_state_mm_eval, player_color_mm_eval):
    score_mm_eval = 0
    for r_mm_eval in range(8):
        for c_mm_eval in range(8):
            piece_mm_eval = board_state_mm_eval[r_mm_eval][c_mm_eval]
            if piece_mm_eval:
                value_mm_eval = PIECE_VALUES.get(get_piece_type(piece_mm_eval), 0)
                if get_piece_color(piece_mm_eval) == player_color_mm_eval:
                    score_mm_eval += value_mm_eval
                else:
                    score_mm_eval -= value_mm_eval
    return score_mm_eval

def evaluate_move_medium(board_after_move_mb, bot_color_eval_mb, original_board_state_mb, move_tuple_mb):
    score_mb = 0
    opponent_color_eval_mb = "white" if bot_color_eval_mb == "black" else "black"
    start_pos_mb, end_pos_mb = move_tuple_mb
    moved_piece_name_mb = board_after_move_mb[end_pos_mb[0]][end_pos_mb[1]]
    original_captured_piece_mb = original_board_state_mb[end_pos_mb[0]][end_pos_mb[1]]
    if check_for_check(board_after_move_mb, opponent_color_eval_mb): score_mb += 50
    if original_captured_piece_mb: score_mb += PIECE_VALUES.get(get_piece_type(original_captured_piece_mb), 0)
    if moved_piece_name_mb and is_square_attacked(end_pos_mb[0], end_pos_mb[1], opponent_color_eval_mb, board_after_move_mb):
        score_mb -= PIECE_VALUES.get(get_piece_type(moved_piece_name_mb), 0) * 0.5
    if moved_piece_name_mb and is_square_attacked(start_pos_mb[0], start_pos_mb[1], opponent_color_eval_mb, original_board_state_mb) and \
       not is_square_attacked(end_pos_mb[0], end_pos_mb[1], opponent_color_eval_mb, board_after_move_mb):
        score_mb += PIECE_VALUES.get(get_piece_type(moved_piece_name_mb), 0) * 0.8
    score_mb += random.uniform(-1, 1)
    return score_mb

def get_all_valid_moves_for_bot(current_board_state_bot, color_of_bot_param, current_castling_rights_state_bot):
    all_moves_bot = []
    for r_bot in range(8):
        for c_bot in range(8):
            piece_bot = current_board_state_bot[r_bot][c_bot]
            if piece_bot and get_piece_color(piece_bot) == color_of_bot_param:
                possible_piece_moves_bot = get_possible_moves(r_bot, c_bot, current_board_state_bot, current_castling_rights_state_bot)
                for end_pos_move_bot in possible_piece_moves_bot:
                    all_moves_bot.append(((r_bot, c_bot), end_pos_move_bot))
    return all_moves_bot

def check_game_over_conditions_for_board(board_state_cgofb, player_to_check_color_cgofb, current_castling_rights_cgofb):
    all_legal_moves_cgofb = get_all_valid_moves_for_bot(board_state_cgofb, player_to_check_color_cgofb, current_castling_rights_cgofb)
    return not all_legal_moves_cgofb

def choose_easy_bot_move(current_board_state_eb, color_of_bot_eb, current_castling_rights_state_eb):
    all_moves_eb = get_all_valid_moves_for_bot(current_board_state_eb, color_of_bot_eb, current_castling_rights_state_eb)
    if not all_moves_eb:
        return None
    capture_moves = []
    opponent_color = "white" if color_of_bot_eb == "black" else "black"
    for move in all_moves_eb:
        start_pos, end_pos = move
        end_row, end_col = end_pos
        target_piece = current_board_state_eb[end_row][end_col]
        if target_piece and get_piece_color(target_piece) == opponent_color:
            capture_moves.append(move)
    if capture_moves:
        return random.choice(capture_moves)
    else:
        return random.choice(all_moves_eb)

def choose_medium_bot_move(current_board_state_mb, color_of_bot_mb, current_castling_rights_state_mb):
    all_moves_mb = get_all_valid_moves_for_bot(current_board_state_mb, color_of_bot_mb, current_castling_rights_state_mb)
    if not all_moves_mb: return None
    best_score_mb = -float('inf')
    best_moves_list_mb = []
    for move_mb in all_moves_mb:
        start_p_mb, end_p_mb = move_mb
        temp_board_mb = [row[:] for row in current_board_state_mb]
        moved_p_name_mb_sim = temp_board_mb[start_p_mb[0]][start_p_mb[1]]
        temp_board_mb[end_p_mb[0]][end_p_mb[1]] = moved_p_name_mb_sim
        temp_board_mb[start_p_mb[0]][start_p_mb[1]] = None
        current_score_mb = evaluate_move_medium(temp_board_mb, color_of_bot_mb, current_board_state_mb, move_mb)
        if current_score_mb > best_score_mb:
            best_score_mb = current_score_mb
            best_moves_list_mb = [move_mb]
        elif current_score_mb == best_score_mb:
            best_moves_list_mb.append(move_mb)
    return random.choice(best_moves_list_mb) if best_moves_list_mb else None

def minimax(board_state_mm, depth_mm, alpha_mm, beta_mm, maximizing_player_color_mm, is_maximizing_turn_mm, current_castling_rights_mm):
    current_player_for_sim_moves = maximizing_player_color_mm if is_maximizing_turn_mm else ("white" if maximizing_player_color_mm == "black" else "black")
    if depth_mm == 0 or check_game_over_conditions_for_board(board_state_mm, current_player_for_sim_moves, current_castling_rights_mm):
        return evaluate_board_state_minimax(board_state_mm, maximizing_player_color_mm)
    possible_next_moves_mm = get_all_valid_moves_for_bot(board_state_mm, current_player_for_sim_moves, current_castling_rights_mm)
    if not possible_next_moves_mm:
         return evaluate_board_state_minimax(board_state_mm, maximizing_player_color_mm)
    if is_maximizing_turn_mm:
        max_eval_mm = -float('inf')
        for move_mm_max in possible_next_moves_mm:
            start_p_mm_max, end_p_mm_max = move_mm_max
            temp_board_mm_max = [row[:] for row in board_state_mm]
            temp_castling_rights = {k:v.copy() for k,v in current_castling_rights_mm.items()}
            moved_p_name_mm_max = temp_board_mm_max[start_p_mm_max[0]][start_p_mm_max[1]]
            moved_p_type = get_piece_type(moved_p_name_mm_max)
            moved_p_color = get_piece_color(moved_p_name_mm_max)
            temp_board_mm_max[end_p_mm_max[0]][end_p_mm_max[1]] = moved_p_name_mm_max
            temp_board_mm_max[start_p_mm_max[0]][start_p_mm_max[1]] = None
            if moved_p_type == "king": temp_castling_rights[moved_p_color]["king_moved"] = True
            eval_score_mm_max = minimax(temp_board_mm_max, depth_mm - 1, alpha_mm, beta_mm, maximizing_player_color_mm, False, temp_castling_rights)
            max_eval_mm = max(max_eval_mm, eval_score_mm_max)
            alpha_mm = max(alpha_mm, eval_score_mm_max)
            if beta_mm <= alpha_mm: break
        return max_eval_mm
    else:
        min_eval_mm = float('inf')
        for move_mm_min in possible_next_moves_mm:
            start_p_mm_min, end_p_mm_min = move_mm_min
            temp_board_mm_min = [row[:] for row in board_state_mm]
            temp_castling_rights = {k:v.copy() for k,v in current_castling_rights_mm.items()}
            moved_p_name_mm_min = temp_board_mm_min[start_p_mm_min[0]][start_p_mm_min[1]]
            moved_p_type = get_piece_type(moved_p_name_mm_min)
            moved_p_color = get_piece_color(moved_p_name_mm_min)
            temp_board_mm_min[end_p_mm_min[0]][end_p_mm_min[1]] = moved_p_name_mm_min
            temp_board_mm_min[start_p_mm_min[0]][start_p_mm_min[1]] = None
            if moved_p_type == "king": temp_castling_rights[moved_p_color]["king_moved"] = True
            eval_score_mm_min = minimax(temp_board_mm_min, depth_mm - 1, alpha_mm, beta_mm, maximizing_player_color_mm, True, temp_castling_rights)
            min_eval_mm = min(min_eval_mm, eval_score_mm_min)
            beta_mm = min(beta_mm, eval_score_mm_min)
            if beta_mm <= alpha_mm: break
        return min_eval_mm

def choose_hard_bot_move(current_board_state_hb, color_of_bot_hb, current_castling_rights_state_hb):
    all_moves_hb = get_all_valid_moves_for_bot(current_board_state_hb, color_of_bot_hb, current_castling_rights_state_hb)
    if not all_moves_hb: return None
    best_move_hb = None
    max_eval_for_bot_hb = -float('inf')
    search_depth_hb = 1
    for move_hb in all_moves_hb:
        start_p_hb, end_p_hb = move_hb
        temp_board_hb = [row[:] for row in current_board_state_hb]
        temp_castling_rights_hb = {k:v.copy() for k,v in current_castling_rights_state_hb.items()}
        moved_p_name_hb = temp_board_hb[start_p_hb[0]][start_p_hb[1]]
        moved_p_type_hb = get_piece_type(moved_p_name_hb)
        moved_p_color_hb = get_piece_color(moved_p_name_hb)
        temp_board_hb[end_p_hb[0]][end_p_hb[1]] = moved_p_name_hb
        temp_board_hb[start_p_hb[0]][start_p_hb[1]] = None
        if moved_p_type_hb == "king": temp_castling_rights_hb[moved_p_color_hb]["king_moved"] = True
        move_eval_hb = minimax(temp_board_hb, search_depth_hb, -float('inf'), float('inf'), color_of_bot_hb, False, temp_castling_rights_hb)
        if move_eval_hb > max_eval_for_bot_hb:
            max_eval_for_bot_hb = move_eval_hb
            best_move_hb = move_hb
        elif move_eval_hb == max_eval_for_bot_hb and random.choice([True,False]):
            best_move_hb = move_hb
    if not best_move_hb and all_moves_hb :
        return random.choice(all_moves_hb)
    return best_move_hb

async def trigger_bot_turn():
    global bot_is_thinking, BOARD, current_turn, castling_rights, game_mode, bot_color, bot_difficulty, game_state, possible_moves, selected_piece, bot_thinking_message
    
    if game_mode == 'pve' and current_turn == bot_color and not bot_is_thinking and game_state == 'playing':
        bot_is_thinking = True
        bot_thinking_message = "Бот думає..."
        
        chosen_move_tuple_tbt = None
        
        if bot_difficulty == 'easy':
            chosen_move_tuple_tbt = choose_easy_bot_move(BOARD, bot_color, castling_rights)
        elif bot_difficulty == 'medium':
            chosen_move_tuple_tbt = choose_medium_bot_move(BOARD, bot_color, castling_rights)
        elif bot_difficulty == 'hard':
            chosen_move_tuple_tbt = choose_hard_bot_move(BOARD, bot_color, castling_rights)
        
        await asyncio.sleep(0.25)

        if chosen_move_tuple_tbt:
            start_pos, end_pos = chosen_move_tuple_tbt
            possible_moves.clear()
            selected_piece = None
            make_move(start_pos, end_pos)
        else:
            check_game_over_conditions(bot_color)

        bot_is_thinking = False
        bot_thinking_message = ""
        pygame.display.set_caption("Шахи")

async def main():
    global game_state, game_mode, bot_difficulty, player_chosen_color, selected_piece, possible_moves
    game_state = 'main_menu'
    running = True

    while running:
        mouse_pos_frame_main = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if game_state == 'main_menu':
                        if btn_start_game.collidepoint(mouse_pos_frame_main): game_state = 'mode_selection_menu'
                    elif game_state == 'mode_selection_menu':
                        if btn_pvp.collidepoint(mouse_pos_frame_main):
                            game_mode = 'pvp'; initialize_game_board_state(); game_state = 'playing'
                        elif btn_pve.collidepoint(mouse_pos_frame_main):
                            game_mode = 'pve'; game_state = 'bot_difficulty_menu'
                        elif btn_back.collidepoint(mouse_pos_frame_main): game_state = 'main_menu'
                    elif game_state == 'bot_difficulty_menu':
                        if btn_easy.collidepoint(mouse_pos_frame_main): bot_difficulty = 'easy'; game_state = 'bot_color_menu'
                        elif btn_medium.collidepoint(mouse_pos_frame_main): bot_difficulty = 'medium'; game_state = 'bot_color_menu'
                        elif btn_hard.collidepoint(mouse_pos_frame_main): bot_difficulty = 'hard'; game_state = 'bot_color_menu'
                        elif btn_back.collidepoint(mouse_pos_frame_main): game_state = 'mode_selection_menu'
                    elif game_state == 'bot_color_menu':
                        if btn_choose_white.collidepoint(mouse_pos_frame_main) and white_king_button_img:
                            player_chosen_color = 'white'; initialize_game_board_state(); game_state = 'playing'
                        elif btn_choose_black.collidepoint(mouse_pos_frame_main) and black_king_button_img:
                            player_chosen_color = 'black'; initialize_game_board_state(); game_state = 'playing'
                        elif btn_back.collidepoint(mouse_pos_frame_main): game_state = 'bot_difficulty_menu'
                    
                    elif game_state == 'playing':
                        is_player_turn = (game_mode == 'pvp') or (game_mode == 'pve' and current_turn != bot_color)

                        if is_player_turn:
                            if BOARD_START_X <= mouse_pos_frame_main[0] < BOARD_START_X + BOARD_SIZE_PX and \
                               BOARD_START_Y <= mouse_pos_frame_main[1] < BOARD_START_Y + BOARD_SIZE_PX:
                                clicked_col_main = (mouse_pos_frame_main[0] - BOARD_START_X) // SQUARE_SIZE
                                clicked_row_main = (mouse_pos_frame_main[1] - BOARD_START_Y) // SQUARE_SIZE
                                if selected_piece:
                                    if (clicked_row_main, clicked_col_main) in possible_moves:
                                        make_move(selected_piece, (clicked_row_main, clicked_col_main))
                                    else: 
                                        new_piece_main = BOARD[clicked_row_main][clicked_col_main]
                                        if new_piece_main and get_piece_color(new_piece_main) == current_turn:
                                            selected_piece = (clicked_row_main, clicked_col_main)
                                            possible_moves = get_possible_moves(clicked_row_main, clicked_col_main, BOARD, castling_rights)
                                        else: selected_piece = None; possible_moves = []
                                else: 
                                    piece_at_click_main = BOARD[clicked_row_main][clicked_col_main]
                                    if piece_at_click_main and get_piece_color(piece_at_click_main) == current_turn:
                                        selected_piece = (clicked_row_main, clicked_col_main)
                                        possible_moves = get_possible_moves(clicked_row_main, clicked_col_main, BOARD, castling_rights)
                                    else:
                                        selected_piece = None; possible_moves = []
                            else: selected_piece = None; possible_moves = []
                    
                    elif "checkmate" in game_state or "stalemate" in game_state:
                        game_over_btn_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 20, 200, 50)
                        if game_over_btn_rect.collidepoint(mouse_pos_frame_main):
                            game_state = 'main_menu'
        
        if game_state == 'playing' and game_mode == 'pve' and current_turn == bot_color and not bot_is_thinking:
            await trigger_bot_turn()

        SCREEN.fill(BACKGROUND_COLOR)
        if game_state == 'main_menu': draw_main_menu(mouse_pos_frame_main)
        elif game_state == 'mode_selection_menu': draw_mode_selection_menu(mouse_pos_frame_main)
        elif game_state == 'bot_difficulty_menu': draw_bot_difficulty_menu(mouse_pos_frame_main)
        elif game_state == 'bot_color_menu': draw_bot_color_menu(mouse_pos_frame_main)
        elif game_state == 'playing' or "checkmate" in game_state or "stalemate" in game_state :
            SCREEN.fill(GAME_BACKGROUND_COLOR)
            draw_board_and_notations()
            if game_state == 'playing':
                 draw_highlight()
            draw_pieces()
            draw_game_log()
            if "checkmate" in game_state or "stalemate" in game_state:
                draw_game_over_screen()

        pygame.display.flip()
        await asyncio.sleep(0)

    pygame.quit()

if __name__ == "__main__":
    asyncio.run(main())