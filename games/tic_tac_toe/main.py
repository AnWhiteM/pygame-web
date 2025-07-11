# -*- coding: utf-8 -*-

import pygame
import sys
import random
import asyncio

WIDTH, HEIGHT = 600, 700
LINE_WIDTH = 15
BOARD_ROWS = 3
BOARD_COLS = 3
SQUARE_SIZE = WIDTH // BOARD_COLS
CIRCLE_RADIUS = SQUARE_SIZE // 3
CIRCLE_WIDTH = 15
CROSS_WIDTH = 20
SPACE = SQUARE_SIZE // 4

BG_COLOR = (28, 170, 156)
LINE_COLOR = (23, 145, 135)
CIRCLE_COLOR = (239, 231, 200)
CROSS_COLOR = (66, 66, 66)
BUTTON_COLOR = (84, 84, 84)
BUTTON_HOVER = (120, 120, 120)
TEXT_COLOR = (255, 255, 255)

try:
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption('Хрестики-нулики')
    font = pygame.font.SysFont(None, 40)
except Exception as e:
    print(f"Error during Pygame initialization: {e}")
    sys.exit()

board = []
player = 1
game_over = False

def create_board():
    return [[0 for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]

def draw_lines():
    for i in range(1, BOARD_ROWS):
        pygame.draw.line(screen, LINE_COLOR, (0, i * SQUARE_SIZE), (WIDTH, i * SQUARE_SIZE), LINE_WIDTH)
        pygame.draw.line(screen, LINE_COLOR, (i * SQUARE_SIZE, 0), (i * SQUARE_SIZE, SQUARE_SIZE * 3), LINE_WIDTH)

def draw_figures():
    for row in range(BOARD_ROWS):
        for col in range(BOARD_COLS):
            if board[row][col] == 1:
                pygame.draw.line(screen, CROSS_COLOR,
                                 (col * SQUARE_SIZE + SPACE, row * SQUARE_SIZE + SPACE),
                                 (col * SQUARE_SIZE + SQUARE_SIZE - SPACE, row * SQUARE_SIZE + SQUARE_SIZE - SPACE),
                                 CROSS_WIDTH)
                pygame.draw.line(screen, CROSS_COLOR,
                                 (col * SQUARE_SIZE + SPACE, row * SQUARE_SIZE + SQUARE_SIZE - SPACE),
                                 (col * SQUARE_SIZE + SQUARE_SIZE - SPACE, row * SQUARE_SIZE + SPACE),
                                 CROSS_WIDTH)
            elif board[row][col] == 2:
                pygame.draw.circle(screen, CIRCLE_COLOR,
                                   (col * SQUARE_SIZE + SQUARE_SIZE // 2, row * SQUARE_SIZE + SQUARE_SIZE // 2),
                                   CIRCLE_RADIUS, CIRCLE_WIDTH)

def mark_square(row, col, player_num):
    board[row][col] = player_num

def is_available(row, col):
    return board[row][col] == 0

def check_win(player_num):
    for row in board:
        if row.count(player_num) == 3:
            return True
    for col in range(BOARD_COLS):
        if all(board[row][col] == player_num for row in range(BOARD_ROWS)):
            return True
    if all(board[i][i] == player_num for i in range(BOARD_ROWS)):
        return True
    if all(board[i][BOARD_ROWS - 1 - i] == player_num for i in range(BOARD_ROWS)):
        return True
    return False

def ai_move_easy():
    empty = [(r, c) for r in range(BOARD_ROWS) for c in range(BOARD_COLS) if board[r][c] == 0]
    if empty:
        return random.choice(empty)
    return None

def ai_move_hard(ai_player_num, human_player_num):
    for r in range(BOARD_ROWS):
        for c in range(BOARD_COLS):
            if board[r][c] == 0:
                board[r][c] = ai_player_num
                if check_win(ai_player_num):
                    board[r][c] = 0
                    return (r, c)
                board[r][c] = 0

    for r in range(BOARD_ROWS):
        for c in range(BOARD_COLS):
            if board[r][c] == 0:
                board[r][c] = human_player_num
                if check_win(human_player_num):
                    board[r][c] = 0
                    return (r, c)
                board[r][c] = 0

    return ai_move_easy()

def draw_button(rect, text):
    mouse_pos = pygame.mouse.get_pos()
    color = BUTTON_HOVER if rect.collidepoint(mouse_pos) else BUTTON_COLOR
    pygame.draw.rect(screen, color, rect)
    try:
        label = font.render(text, True, TEXT_COLOR)
        screen.blit(label, (rect.centerx - label.get_width() // 2, rect.centery - label.get_height() // 2))
    except Exception as e:
        print(f"Error rendering button text '{text}': {e}")
        pass

def restart_game():
    global board, player, game_over
    board = create_board()
    player = 1
    game_over = False

def is_board_full():
    return all(board[r][c] != 0 for r in range(BOARD_ROWS) for c in range(BOARD_COLS))

async def select_side(difficulty):
    while True:
        screen.fill(BG_COLOR)
        title = font.render("Виберіть сторону", True, TEXT_COLOR)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 150))

        x_button = pygame.Rect(WIDTH // 2 - 130, 300, 100, 50)
        o_button = pygame.Rect(WIDTH // 2 + 30, 300, 100, 50)

        draw_button(x_button, "X")
        draw_button(o_button, "O")

        try:
            pygame.display.update()
        except Exception as e:
            print(f"Error during select_side display update: {e}")
            sys.exit()
        await asyncio.sleep(0)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if x_button.collidepoint(event.pos):
                    return difficulty, 1
                elif o_button.collidepoint(event.pos):
                    return difficulty, 2

async def select_difficulty():
    while True:
        screen.fill(BG_COLOR)
        title = font.render("Виберіть складність", True, TEXT_COLOR)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 150))

        easy_button = pygame.Rect(WIDTH // 2 - 100, 300, 200, 50)
        hard_button = pygame.Rect(WIDTH // 2 - 100, 380, 200, 50)

        draw_button(easy_button, "Легка")
        draw_button(hard_button, "Складна")

        try:
            pygame.display.update()
        except Exception as e:
            print(f"Error during select_difficulty display update: {e}")
            sys.exit()
        await asyncio.sleep(0)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if easy_button.collidepoint(event.pos):
                    return await select_side("easy")
                elif hard_button.collidepoint(event.pos):
                    return await select_side("hard")

async def main_menu():
    while True:
        screen.fill(BG_COLOR)
        try:
            title = font.render("Хрестики-нулики", True, TEXT_COLOR)
            screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 150))
        except Exception as e:
            print(f"Error rendering title text: {e}")
            pass

        play_button = pygame.Rect(WIDTH // 2 - 100, 300, 200, 50)
        draw_button(play_button, "Почати гру")

        try:
            pygame.display.update()
        except Exception as e:
            print(f"Error during main_menu display update: {e}")
            sys.exit()
        await asyncio.sleep(0)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if play_button.collidepoint(event.pos):
                    return await select_difficulty()

async def run_game(difficulty, player_side):
    global player, game_over, board
    restart_game()
    restart_button = None
    menu_button = None
    player = player_side
    ai_player = 2 if player_side == 1 else 1

    bot_move_delay = 400
    last_move_time = pygame.time.get_ticks()
    bot_thinking = False

    if player_side == 2:
        move = ai_move_easy() if difficulty == "easy" else ai_move_hard(ai_player, player_side)
        if move:
            mark_square(move[0], move[1], ai_player)
            player = player_side
        
    game_over = False

    while True:
        screen.fill(BG_COLOR)
        draw_lines()
        draw_figures()

        if game_over:
            try:
                if check_win(player_side):
                    message = font.render("Ви перемогли!", True, TEXT_COLOR)
                elif check_win(ai_player):
                    message = font.render("Бот переміг!", True, TEXT_COLOR)
                elif is_board_full():
                    message = font.render("Нічия!", True, TEXT_COLOR)
                else:
                    message = font.render("Гру закінчено!", True, TEXT_COLOR)
                screen.blit(message, (WIDTH // 2 - message.get_width() // 2, HEIGHT // 2 - message.get_height() // 2 + 50))
            except Exception as e:
                print(f"Error rendering game over message: {e}")
                pass

            restart_button = pygame.Rect(WIDTH // 2 - 220, HEIGHT - 80, 200, 50)
            menu_button = pygame.Rect(WIDTH // 2 + 20, HEIGHT - 80, 200, 50)
            draw_button(restart_button, "Перезапуск")
            draw_button(menu_button, "В меню")
        else:
            restart_button = None
            menu_button = None

        try:
            pygame.display.update()
        except Exception as e:
            print(f"Error during run_game display update: {e}")
            sys.exit()
        await asyncio.sleep(0)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if not game_over and event.type == pygame.MOUSEBUTTONDOWN:
                mouseX, mouseY = event.pos
                if mouseY < SQUARE_SIZE * 3 and player == player_side:
                    clicked_row = mouseY // SQUARE_SIZE
                    clicked_col = mouseX // SQUARE_SIZE

                    if is_available(clicked_row, clicked_col):
                        mark_square(clicked_row, clicked_col, player)
                        if check_win(player) or is_board_full():
                            game_over = True
                        else:
                            player = ai_player
                            bot_thinking = False
                            last_move_time = pygame.time.get_ticks()

            if game_over and event.type == pygame.MOUSEBUTTONDOWN:
                if restart_button and restart_button.collidepoint(event.pos):
                    return await run_game(difficulty, player_side)
                if menu_button and menu_button.collidepoint(event.pos):
                    return

        if not game_over and player == ai_player:
            if not bot_thinking:
                last_move_time = pygame.time.get_ticks()
                bot_thinking = True
            elif pygame.time.get_ticks() - last_move_time >= bot_move_delay:
                move = ai_move_easy() if difficulty == "easy" else ai_move_hard(ai_player, player_side)
                if move:
                    mark_square(move[0], move[1], ai_player)
                    if check_win(ai_player) or is_board_full():
                        game_over = True
                    else:
                        player = player_side
                bot_thinking = False

async def main():
    try:
        while True:
            selected_difficulty, selected_side = await main_menu()
            await run_game(selected_difficulty, selected_side)
    except Exception as e:
        print(f"Unhandled error in main loop: {e}")
        sys.exit()

try:
    asyncio.run(main())
except Exception as e:
    print(f"Error running asyncio main: {e}")
    sys.exit()