# -*- coding: utf-8 -*-

import pygame
import random
import sys
import asyncio
import os
from pathlib import Path

# --- КОНСТАНТИ ТА НАЛАШТУВАННЯ ГРИ ---
CELL_SIZE = 40
GRID_SIZE = 10
MARGIN = 50
LOG_PANEL_WIDTH = 350
SCREEN_SIZE = (CELL_SIZE * GRID_SIZE * 2 + MARGIN * 3 + LOG_PANEL_WIDTH, CELL_SIZE * GRID_SIZE + MARGIN * 2)

# --- КОЛЬОРИ ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 200, 0)
TEXT_COLOR = (255, 255, 255)
LOG_BG_COLOR = (20, 20, 40)
GRID_COLOR = (50, 100, 150, 150)

# --- ФАЗИ ГРИ ---
MAIN_MENU = 0
DIFFICULTY_SELECTION = 1
SHIP_PLACEMENT = 2
IN_GAME = 3
GAME_OVER = 4

# --- ІНІЦІАЛІЗАЦІЯ PYGAME ТА ШРИФТІВ ---
try:
    pygame.init()
    screen = pygame.display.set_mode(SCREEN_SIZE)
    pygame.display.set_caption("Морський Бій")
    font = pygame.font.SysFont("Arial", 28, bold=True)
    font_large = pygame.font.SysFont("Arial", 48, bold=True)
    font_small = pygame.font.SysFont("Arial", 18)
    font_coords = pygame.font.SysFont("Arial", 16, bold=True)
    font_log = pygame.font.SysFont("Consolas", 16)
except Exception as e:
    print(f"Помилка під час ініціалізації Pygame: {e}")
    sys.exit()

# --- ЗАВАНТАЖЕННЯ ГРАФІЧНИХ АСЕТІВ ---
assets = {}
try:
    assets_path = Path(__file__).parent / "models"
    ship_images_info = {
        4: "battlecruiser.png", 3: "cruiser.png",
        2: "destroyer.png", 1: "boat.png"
    }
    assets['ships'] = {}
    for size, filename in ship_images_info.items():
        assets['ships'][size] = pygame.image.load(assets_path / filename).convert_alpha()

    assets['water'] = pygame.image.load(assets_path / 'water.png').convert()
    assets['explosion'] = pygame.transform.scale(pygame.image.load(assets_path / 'explosion.png').convert_alpha(), (CELL_SIZE, CELL_SIZE))
    assets['splash'] = pygame.transform.scale(pygame.image.load(assets_path / 'splash.png').convert_alpha(), (CELL_SIZE, CELL_SIZE))
except Exception as e:
    print(f"Не вдалося завантажити асети з папки 'models'. Переконайтеся, що всі файли на місці. Помилка: {e}")
    sys.exit()


# --- КЛАС ДЛЯ КОРАБЛІВ ---
class Ship:
    def __init__(self, size, pos, direction):
        self.size = size
        self.x, self.y = pos
        self.direction = direction
        self.hits = [False] * size
        original_image = assets['ships'][size]

        if self.direction == (1, 0):
            scaled_image = pygame.transform.scale(original_image, (CELL_SIZE, CELL_SIZE * self.size))
            self.image = pygame.transform.rotate(scaled_image, -90)
        else:
            self.image = pygame.transform.scale(original_image, (CELL_SIZE, CELL_SIZE * self.size))

        self.rect = self.image.get_rect(topleft=(MARGIN + self.x * CELL_SIZE, MARGIN + self.y * CELL_SIZE))

    def get_cells(self):
        cells = []
        for i in range(self.size):
            cells.append((self.x + i * self.direction[0], self.y + i * self.direction[1]))
        return cells

    def is_sunk(self):
        return all(self.hits)

    def draw(self, surface, offset_x=0):
        draw_rect = self.rect.copy()
        draw_rect.x += offset_x
        surface.blit(self.image, draw_rect)


# --- ГЛОБАЛЬНІ ЗМІННІ СТАНУ ГРИ ---
player_ships, enemy_ships = [], []
player_hits, enemy_hits = set(), set()
ship_sizes_to_place = [4, 3, 3, 2, 2, 2, 1, 1, 1, 1]
placing_index = 0
placing_direction = (1, 0)
is_player_turn = True
game_winner_message = ""
current_game_state = MAIN_MENU
selected_difficulty = "easy"
ai_last_hit = None
ai_hunting_mode = False
ai_hit_cells = []
game_log_messages = []
MAX_LOG_MESSAGES = 15

# --- ФУНКЦІЇ ---
def add_log_message(message):
    game_log_messages.insert(0, message)
    if len(game_log_messages) > MAX_LOG_MESSAGES:
        game_log_messages.pop()

def draw_background():
    w, h = assets['water'].get_size()
    for x in range(0, SCREEN_SIZE[0], w):
        for y in range(0, SCREEN_SIZE[1], h):
            screen.blit(assets['water'], (x, y))

def draw_ui_button(rect, text_content, is_active=True):
    button_color = GREEN if is_active else WHITE
    shadow_rect = pygame.Rect(rect.x + 3, rect.y + 3, rect.width, rect.height)
    pygame.draw.rect(screen, (0,0,0,150), shadow_rect, border_radius=12)
    pygame.draw.rect(screen, button_color, rect, border_radius=12)
    pygame.draw.rect(screen, BLACK, rect, 2, border_radius=12)
    label_surface = font.render(text_content, True, BLACK)
    screen.blit(label_surface, (rect.centerx - label_surface.get_width() // 2, rect.centery - label_surface.get_height() // 2))

def create_board_from_ships(ships):
    board = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    for ship in ships:
        for x, y in ship.get_cells():
            if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
                board[y][x] = ship
    return board

def render_game_board(ships, hits, offset_x, offset_y, hide_ships=False):
    for i in range(GRID_SIZE):
        row_label_surf = font_coords.render(chr(ord('А') + i), True, WHITE)
        screen.blit(row_label_surf, (offset_x - row_label_surf.get_width() - 10, offset_y + i * CELL_SIZE + (CELL_SIZE - row_label_surf.get_height()) // 2))
        col_label_surf = font_coords.render(str(i + 1), True, WHITE)
        screen.blit(col_label_surf, (offset_x + i * CELL_SIZE + (CELL_SIZE - col_label_surf.get_width()) // 2, offset_y - col_label_surf.get_height() - 5))

    for i in range(GRID_SIZE + 1):
        pygame.draw.line(screen, GRID_COLOR, (offset_x, offset_y + i * CELL_SIZE), (offset_x + GRID_SIZE * CELL_SIZE, offset_y + i * CELL_SIZE), 1)
        pygame.draw.line(screen, GRID_COLOR, (offset_x + i * CELL_SIZE, offset_y), (offset_x + i * CELL_SIZE, offset_y + GRID_SIZE * CELL_SIZE), 1)

    if not hide_ships:
        for ship in ships:
            ship.draw(screen)
            
    if hide_ships:
        for ship in ships:
            if ship.is_sunk():
                enemy_board_offset_x = MARGIN * 2 + GRID_SIZE * CELL_SIZE
                ship.draw(screen, offset_x=enemy_board_offset_x - MARGIN)

    board_data = create_board_from_ships(ships)
    for x, y in hits:
        cell_rect = pygame.Rect(offset_x + x * CELL_SIZE, offset_y + y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
        if board_data[y][x] is not None:
            screen.blit(assets['explosion'], cell_rect)
        else:
            screen.blit(assets['splash'], cell_rect)

def get_grid_cell_from_pos(mouse_pos, board_offset_x, board_offset_y):
    mouse_x, mouse_y = mouse_pos
    grid_x = (mouse_x - board_offset_x) // CELL_SIZE
    grid_y = (mouse_y - board_offset_y) // CELL_SIZE
    if 0 <= grid_x < GRID_SIZE and 0 <= grid_y < GRID_SIZE:
        return grid_x, grid_y
    return None

def can_place_ship(board_data, x, y, ship_size, direction):
    ship_cells = []
    for i in range(ship_size):
        ship_cells.append((x + i * direction[0], y + i * direction[1]))

    for cx, cy in ship_cells:
        if not (0 <= cx < GRID_SIZE and 0 <= cy < GRID_SIZE):
            return False
        for ox in range(-1, 2):
            for oy in range(-1, 2):
                nx, ny = cx + ox, cy + oy
                if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                    if board_data[ny][nx] is not None:
                        return False
    return True

def generate_computer_ships():
    ships_list = []
    board_data = create_board_from_ships([])
    for size in ship_sizes_to_place:
        placed = False
        attempts = 0
        while not placed and attempts < 1000:
            x, y = random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1)
            direction = random.choice([(1, 0), (0, 1)])
            if can_place_ship(board_data, x, y, size, direction):
                new_ship = Ship(size, (x, y), direction)
                ships_list.append(new_ship)
                board_data = create_board_from_ships(ships_list)
                placed = True
            attempts += 1
    return ships_list

def check_and_mark_sunk_ships(ships, hits):
    sunk_ships_this_turn = []
    board_data = create_board_from_ships(ships)
    
    for x, y in list(hits):
        ship = board_data[y][x]
        if ship:
            ship_cells = ship.get_cells()
            if (x, y) in ship_cells:
                hit_index = ship_cells.index((x,y))
                ship.hits[hit_index] = True
            
            if ship.is_sunk() and ship not in sunk_ships_this_turn:
                 sunk_ships_this_turn.append(ship)
    
    new_hits = set()
    for ship in sunk_ships_this_turn:
        for x, y in ship.get_cells():
            for ox in range(-1, 2):
                for oy in range(-1, 2):
                    nx, ny = x + ox, y + oy
                    if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                         new_hits.add((nx,ny))
    return sunk_ships_this_turn, new_hits

def all_ships_sunk(ships):
    return all(ship.is_sunk() for ship in ships)

# --- ЛОГІКА ШІ ---
def get_random_unhit_cell(hit_data):
    available = [(x,y) for x in range(GRID_SIZE) for y in range(GRID_SIZE) if (x,y) not in hit_data]
    return random.choice(available) if available else None

def get_adjacent_untried_cells(hit_cell, hit_data):
    x, y = hit_cell
    potential = []
    for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
        nx, ny = x+dx, y+dy
        if 0<=nx<GRID_SIZE and 0<=ny<GRID_SIZE and (nx,ny) not in hit_data:
            potential.append((nx,ny))
    return potential

def ai_make_move_easy(player_board, enemy_hits_data):
    return get_random_unhit_cell(enemy_hits_data)

def ai_make_move_medium(player_board, enemy_hits_data):
    global ai_hunting_mode, ai_hit_cells
    if ai_hunting_mode and ai_hit_cells:
        for hx, hy in reversed(ai_hit_cells):
            potential_targets = get_adjacent_untried_cells((hx, hy), enemy_hits_data)
            if potential_targets:
                return random.choice(potential_targets)
    return get_random_unhit_cell(enemy_hits_data)

def ai_make_move_hard(player_board, enemy_hits_data):
    global ai_hunting_mode, ai_hit_cells
    if ai_hunting_mode and ai_hit_cells:
        if len(ai_hit_cells) >= 2:
            hits = sorted(ai_hit_cells)
            h1x, h1y = hits[0]; h2x, h2y = hits[-1]
            dx, dy = (0, 1) if h1x == h2x else (1, 0)
            
            if dx != 0 or dy != 0:
                for d in [1, -1]:
                    nx, ny = hits[-1][0] + dx*d, hits[-1][1] + dy*d
                    if 0<=nx<GRID_SIZE and 0<=ny<GRID_SIZE and (nx,ny) not in enemy_hits_data: return (nx,ny)
                    nx, ny = hits[0][0] - dx*d, hits[0][1] - dy*d
                    if 0<=nx<GRID_SIZE and 0<=ny<GRID_SIZE and (nx,ny) not in enemy_hits_data: return (nx,ny)
        if ai_hit_cells:
            return ai_make_move_medium(player_board, enemy_hits_data)
    return get_random_unhit_cell(enemy_hits_data)

def ai_make_move_impossible(player_board, enemy_hits_data):
    if random.random() < 0.80:
        unhit_ship_cells = [(x,y) for ship in player_ships for i, (x, y) in enumerate(ship.get_cells()) if not ship.hits[i] and (x,y) not in enemy_hits_data]
        if unhit_ship_cells:
            return random.choice(unhit_ship_cells)
    return ai_make_move_hard(player_board, enemy_hits_data)

# --- ГОЛОВНИЙ ІГРОВИЙ ЦИКЛ ---
async def main_game_loop():
    global current_game_state, player_ships, enemy_ships, player_hits, enemy_hits, \
           ship_sizes_to_place, placing_index, placing_direction, is_player_turn, game_winner_message, \
           selected_difficulty, ai_last_hit, ai_hunting_mode, ai_hit_cells, game_log_messages

    bot_is_thinking, bot_action_delay, last_bot_move_time = False, 300, 0
    start_game_button_rect = easy_button_rect = medium_button_rect = hard_button_rect = \
    impossible_button_rect = restart_game_rect = back_to_menu_rect = pygame.Rect(0,0,0,0)
    difficulty_map = {"easy": "Легка", "medium": "Середня", "hard": "Складна", "impossible": "Неможлива"}

    running = True
    while running:
        draw_background()
        
        # --- ОБРОБКА ПОДІЙ ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if current_game_state == MAIN_MENU:
                if event.type == pygame.MOUSEBUTTONDOWN and start_game_button_rect.collidepoint(event.pos):
                    current_game_state = DIFFICULTY_SELECTION

            elif current_game_state == DIFFICULTY_SELECTION:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    difficulty = None
                    if easy_button_rect.collidepoint(event.pos): difficulty = "easy"
                    elif medium_button_rect.collidepoint(event.pos): difficulty = "medium"
                    elif hard_button_rect.collidepoint(event.pos): difficulty = "hard"
                    elif impossible_button_rect.collidepoint(event.pos): difficulty = "impossible"

                    if difficulty:
                        selected_difficulty = difficulty
                        player_ships, enemy_ships, player_hits, enemy_hits = [], generate_computer_ships(), set(), set()
                        placing_index, placing_direction, is_player_turn, game_winner_message = 0, (1, 0), True, ""
                        ai_last_hit, ai_hunting_mode, ai_hit_cells, game_log_messages = None, False, [], []
                        current_game_state = SHIP_PLACEMENT
                        add_log_message(f"Складність: {difficulty_map[selected_difficulty]}. Розташуйте кораблі.")

            elif current_game_state == SHIP_PLACEMENT:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    cell = get_grid_cell_from_pos(event.pos, MARGIN, MARGIN)
                    if cell and placing_index < len(ship_sizes_to_place):
                        if event.button == 1:
                            size = ship_sizes_to_place[placing_index]
                            if can_place_ship(create_board_from_ships(player_ships), cell[0], cell[1], size, placing_direction):
                                player_ships.append(Ship(size, cell, placing_direction))
                                placing_index += 1
                                add_log_message(f"Корабель {size}-палубний розміщено.")
                                if placing_index >= len(ship_sizes_to_place):
                                    current_game_state = IN_GAME
                                    add_log_message("Всі кораблі розміщено. Ваш хід!")
                            else:
                                add_log_message("Тут не можна розмістити корабель.")
                        elif event.button == 3:
                            placing_direction = (placing_direction[1], placing_direction[0])
            
            elif current_game_state == IN_GAME:
                if is_player_turn and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    enemy_board_offset_x = MARGIN * 2 + GRID_SIZE * CELL_SIZE
                    cell = get_grid_cell_from_pos(event.pos, enemy_board_offset_x, MARGIN)
                    if cell and cell not in player_hits:
                        player_hits.add(cell)
                        x, y = cell
                        cell_name = chr(ord('А') + y) + str(x + 1)
                        sunk_ships, new_hits = check_and_mark_sunk_ships(enemy_ships, player_hits)
                        player_hits.update(new_hits)
                        if create_board_from_ships(enemy_ships)[y][x]:
                            add_log_message(f"Постріл у {cell_name} - Влучання!")
                            if sunk_ships: add_log_message("Корабель супротивника потоплено!")
                        else:
                            add_log_message(f"Постріл у {cell_name} - Промах.")
                            is_player_turn = False
            
            elif current_game_state == GAME_OVER:
                if event.type == pygame.MOUSEBUTTONDOWN and (restart_game_rect.collidepoint(event.pos) or back_to_menu_rect.collidepoint(event.pos)):
                    player_ships, enemy_ships, player_hits, enemy_hits = [], [], set(), set()
                    placing_index, is_player_turn, game_winner_message = 0, True, ""
                    ai_last_hit, ai_hunting_mode, ai_hit_cells, game_log_messages = None, False, [], []
                    current_game_state = MAIN_MENU

        # --- ВІДМАЛЬОВКА ---
        if current_game_state == MAIN_MENU:
            title_surface = font_large.render("МОРСЬКИЙ БІЙ", True, WHITE)
            screen.blit(title_surface, (SCREEN_SIZE[0] // 2 - title_surface.get_width() // 2, 150))
            start_game_button_rect = pygame.Rect(SCREEN_SIZE[0] // 2 - 125, 300, 250, 50)
            draw_ui_button(start_game_button_rect, "Почати гру")

        elif current_game_state == DIFFICULTY_SELECTION:
            title_surface = font_large.render("Оберіть складність", True, WHITE)
            screen.blit(title_surface, (SCREEN_SIZE[0] // 2 - title_surface.get_width() // 2, 150))
            easy_button_rect = pygame.Rect(SCREEN_SIZE[0] // 2 - 125, 250, 250, 45)
            medium_button_rect = pygame.Rect(SCREEN_SIZE[0] // 2 - 125, 310, 250, 45)
            hard_button_rect = pygame.Rect(SCREEN_SIZE[0] // 2 - 125, 370, 250, 45)
            impossible_button_rect = pygame.Rect(SCREEN_SIZE[0] // 2 - 125, 430, 250, 45)
            draw_ui_button(easy_button_rect, "Легка")
            draw_ui_button(medium_button_rect, "Середня")
            draw_ui_button(hard_button_rect, "Складна")
            draw_ui_button(impossible_button_rect, "Неможлива")

        elif current_game_state == SHIP_PLACEMENT:
            render_game_board(player_ships, set(), MARGIN, MARGIN)
            if placing_index < len(ship_sizes_to_place):
                size = ship_sizes_to_place[placing_index]
                cell = get_grid_cell_from_pos(pygame.mouse.get_pos(), MARGIN, MARGIN)
                if cell:
                    color = (0, 255, 0, 150) if can_place_ship(create_board_from_ships(player_ships), cell[0], cell[1], size, placing_direction) else (255, 0, 0, 150)
                    for i in range(size):
                        rect = pygame.Rect(MARGIN + (cell[0] + i*placing_direction[0]) * CELL_SIZE, MARGIN + (cell[1] + i*placing_direction[1]) * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                        s = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
                        s.fill(color)
                        screen.blit(s, rect.topleft)
                instr_surf = font.render(f"Розмістіть {size}-палубний корабель (ПКМ - поворот)", True, WHITE)
                screen.blit(instr_surf, (SCREEN_SIZE[0] // 2 - instr_surf.get_width() // 2, SCREEN_SIZE[1] - 50))

        elif current_game_state == IN_GAME:
            enemy_board_offset_x = MARGIN * 2 + GRID_SIZE * CELL_SIZE
            render_game_board(player_ships, enemy_hits, MARGIN, MARGIN)
            render_game_board(enemy_ships, player_hits, enemy_board_offset_x, MARGIN, hide_ships=True)
            if is_player_turn:
                cell = get_grid_cell_from_pos(pygame.mouse.get_pos(), enemy_board_offset_x, MARGIN)
                if cell and cell not in player_hits:
                    rect = pygame.Rect(enemy_board_offset_x + cell[0]*CELL_SIZE, MARGIN + cell[1]*CELL_SIZE, CELL_SIZE, CELL_SIZE)
                    s = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
                    s.fill((255, 255, 0, 100))
                    screen.blit(s, rect.topleft)

        elif current_game_state == GAME_OVER:
            enemy_board_offset_x = MARGIN * 2 + GRID_SIZE * CELL_SIZE
            render_game_board(player_ships, enemy_hits, MARGIN, MARGIN)
            render_game_board(enemy_ships, player_hits, enemy_board_offset_x, MARGIN)

            dim_surface = pygame.Surface(screen.get_size())
            dim_surface.set_alpha(180)
            dim_surface.fill(BLACK)
            screen.blit(dim_surface, (0, 0))
            
            winner_surf = font_large.render(game_winner_message, True, GREEN if "Ви перемогли" in game_winner_message else "red")
            screen.blit(winner_surf, (SCREEN_SIZE[0] // 2 - winner_surf.get_width() // 2, SCREEN_SIZE[1] // 2 - 100))
            restart_game_rect = pygame.Rect(SCREEN_SIZE[0] // 2 - 125, SCREEN_SIZE[1] // 2, 250, 45)
            back_to_menu_rect = pygame.Rect(SCREEN_SIZE[0] // 2 - 125, SCREEN_SIZE[1] // 2 + 60, 250, 45)
            draw_ui_button(restart_game_rect, "Зіграти ще раз")
            draw_ui_button(back_to_menu_rect, "У головне меню")

        # --- ЛОГІКА ХОДУ БОТА ---
        if current_game_state == IN_GAME and not is_player_turn:
            if not bot_is_thinking:
                last_bot_move_time = pygame.time.get_ticks()
                bot_is_thinking = True
            elif pygame.time.get_ticks() - last_bot_move_time >= bot_action_delay:
                move_func = { "easy": ai_make_move_easy, "medium": ai_make_move_medium, "hard": ai_make_move_hard, "impossible": ai_make_move_impossible }[selected_difficulty]
                target = move_func(create_board_from_ships(player_ships), enemy_hits)
                if target and target not in enemy_hits:
                    enemy_hits.add(target)
                    x, y = target
                    if create_board_from_ships(player_ships)[y][x]:
                        add_log_message(f"Ворог влучив у {chr(ord('А') + y)}{x + 1}!")
                        ai_hunting_mode = True
                        if target not in ai_hit_cells: ai_hit_cells.append(target)
                        sunk_ships, new_hits = check_and_mark_sunk_ships(player_ships, enemy_hits)
                        enemy_hits.update(new_hits)
                        if sunk_ships:
                             add_log_message("Ваш корабель потоплено!")
                             sunk_cells = {cell for ship in sunk_ships for cell in ship.get_cells()}
                             ai_hit_cells = [cell for cell in ai_hit_cells if cell not in sunk_cells]
                             if not ai_hit_cells: ai_hunting_mode = False
                    else:
                        add_log_message(f"Ворог промахнувся по {chr(ord('А') + y)}{x + 1}.")
                        is_player_turn = True
                else: is_player_turn = True
                bot_is_thinking = False

        # --- ПЕРЕВІРКА ПЕРЕМОГИ ---
        if current_game_state == IN_GAME:
            if all_ships_sunk(enemy_ships):
                game_winner_message = "Ви перемогли!"
                add_log_message("ПЕРЕМОГА! Всі ворожі кораблі знищено.")
                current_game_state = GAME_OVER
            elif all_ships_sunk(player_ships):
                game_winner_message = "Комп'ютер переміг!"
                add_log_message("ПОРАЗКА! Всі ваші кораблі потоплено.")
                current_game_state = GAME_OVER

        # --- ПАНЕЛЬ ЛОГІВ ---
        if current_game_state in [IN_GAME, GAME_OVER, SHIP_PLACEMENT]:
            log_panel_x = MARGIN * 3 + GRID_SIZE * CELL_SIZE * 2
            log_rect = pygame.Rect(log_panel_x, MARGIN, LOG_PANEL_WIDTH, GRID_SIZE * CELL_SIZE)
            s = pygame.Surface(log_rect.size, pygame.SRCALPHA)
            s.fill((*LOG_BG_COLOR, 200))
            screen.blit(s, log_rect.topleft)
            pygame.draw.rect(screen, WHITE, log_rect, 1, border_radius=5)
            log_title_surf = font.render("ЖУРНАЛ ПОДІЙ", True, WHITE)
            screen.blit(log_title_surf, (log_rect.centerx - log_title_surf.get_width()//2, log_rect.top + 10))
            for i, msg in enumerate(game_log_messages):
                screen.blit(font_log.render(f"> {msg}", True, WHITE), (log_rect.left + 15, log_rect.top + 50 + i * 22))

        # --- КЕРУВАННЯ КУРСОРОМ ---
        pygame.mouse.set_visible(True)
        show_hand_cursor = False
        mouse_pos = pygame.mouse.get_pos()
        if current_game_state == SHIP_PLACEMENT and get_grid_cell_from_pos(mouse_pos, MARGIN, MARGIN):
            show_hand_cursor = True
        elif current_game_state == IN_GAME and is_player_turn:
            cell = get_grid_cell_from_pos(mouse_pos, MARGIN * 2 + GRID_SIZE * CELL_SIZE, MARGIN)
            if cell and cell not in player_hits: show_hand_cursor = True
        elif current_game_state == MAIN_MENU and start_game_button_rect.collidepoint(mouse_pos):
            show_hand_cursor = True
        elif current_game_state == DIFFICULTY_SELECTION:
            if easy_button_rect.collidepoint(mouse_pos) or medium_button_rect.collidepoint(mouse_pos) or \
               hard_button_rect.collidepoint(mouse_pos) or impossible_button_rect.collidepoint(mouse_pos):
                show_hand_cursor = True
        elif current_game_state == GAME_OVER and (restart_game_rect.collidepoint(mouse_pos) or back_to_menu_rect.collidepoint(mouse_pos)):
            show_hand_cursor = True
        
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND if show_hand_cursor else pygame.SYSTEM_CURSOR_ARROW)

        pygame.display.update()
        await asyncio.sleep(0)

    pygame.quit()
    sys.exit()

# --- ЗАПУСК ГРИ ---
if __name__ == "__main__":
    try:
        asyncio.run(main_game_loop())
    except Exception as e:
        print(f"Помилка під час запуску ігрового циклу: {e}")