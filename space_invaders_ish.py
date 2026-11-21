#!/usr/bin/env python3
"""
Space Invaders for iSH (terminal)
Controls: arrows or a/d to move, space to shoot, q to quit
"""
import curses
import time
import random

def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(0)          # blocking until start
    sh, sw = stdscr.getmaxyx()
    if sh < 20 or sw < 40:
        stdscr.addstr(0, 0, "Terminal too small (need 40x20+)")
        stdscr.refresh()
        time.sleep(2)
        return

    # Start screen — wait for Enter
    stdscr.clear()
    stdscr.addstr(sh//2 - 2, sw//2 - 10, "SPACE INVADERS")
    stdscr.addstr(sh//2,     sw//2 - 12, "Press ENTER to start")
    stdscr.addstr(sh//2 + 2, sw//2 - 14, "a/d or arrows  space=shoot")
    stdscr.addstr(sh//2 + 3, sw//2 - 8,  "q = quit")
    stdscr.refresh()
    while True:
        key = stdscr.getch()
        if key in (10, 13):    # Enter
            break
        if key == ord('q'):
            return

    # Now switch to non-blocking game loop
    stdscr.nodelay(1)
    stdscr.timeout(50)

    # Game state
    player_x = sw // 2
    player_y = sh - 2
    bullets = []          # [x, y]
    invaders = []         # [x, y, alive]
    inv_dir = 1
    inv_speed = 8
    frame = 0
    score = 0
    lives = 3
    game_over = False

    # Spawn invaders
    for row in range(3):
        for col in range(8):
            invaders.append([4 + col * 4, 2 + row * 2, True])

    while True:
        stdscr.clear()
        key = stdscr.getch()

        if key == ord('q'):
            break
        if game_over:
            stdscr.addstr(sh//2, sw//2-5, "GAME OVER")
            stdscr.addstr(sh//2+1, sw//2-6, f"Score: {score}")
            stdscr.addstr(sh//2+2, sw//2-8, "q to quit")
            stdscr.refresh()
            continue

        # Input
        if key in (curses.KEY_LEFT, ord('a')) and player_x > 1:
            player_x -= 1
        if key in (curses.KEY_RIGHT, ord('d')) and player_x < sw-2:
            player_x += 1
        if key == ord(' ') and len(bullets) < 3:
            bullets.append([player_x, player_y-1])

        # Move bullets
        for b in bullets[:]:
            b[1] -= 1
            if b[1] < 1:
                bullets.remove(b)

        # Move invaders
        frame += 1
        if frame % inv_speed == 0:
            # Check edges
            xs = [inv[0] for inv in invaders if inv[2]]
            if xs:
                if max(xs) >= sw-3 or min(xs) <= 2:
                    inv_dir *= -1
                    for inv in invaders:
                        if inv[2]:
                            inv[1] += 1
                else:
                    for inv in invaders:
                        if inv[2]:
                            inv[0] += inv_dir

        # Collisions
        for b in bullets[:]:
            for inv in invaders:
                if inv[2] and abs(b[0]-inv[0]) < 2 and abs(b[1]-inv[1]) < 1:
                    inv[2] = False
                    if b in bullets:
                        bullets.remove(b)
                    score += 10
                    break

        # Invader reach bottom or hit player
        for inv in invaders:
            if inv[2] and inv[1] >= player_y-1:
                lives -= 1
                inv[2] = False
                if lives <= 0:
                    game_over = True

        # Draw
        # HUD
        stdscr.addstr(0, 0, f"Score: {score}  Lives: {lives}  q=quit")
        # Player
        stdscr.addstr(player_y, player_x, "A")
        # Bullets
        for b in bullets:
            if 0 < b[1] < sh-1:
                stdscr.addstr(b[1], b[0], "|")
        # Invaders
        for inv in invaders:
            if inv[2] and 0 < inv[1] < sh-1:
                stdscr.addstr(inv[1], inv[0], "W")

        # Win
        if all(not inv[2] for inv in invaders):
            stdscr.addstr(sh//2, sw//2-4, "YOU WIN")
            stdscr.refresh()
            time.sleep(2)
            break

        stdscr.refresh()

if __name__ == "__main__":
    curses.wrapper(main)
