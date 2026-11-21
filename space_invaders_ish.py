#!/usr/bin/env python3
"""
Space Invaders for iSH (terminal)
Controls: a/d or arrows to move, space to shoot, q to quit
"""
import curses
import time

def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(0)
    sh, sw = stdscr.getmaxyx()
    if sh < 20 or sw < 40:
        stdscr.addstr(0, 0, "Terminal too small (need 40x20+)")
        stdscr.refresh()
        time.sleep(2)
        return

    # Start screen
    stdscr.clear()
    stdscr.addstr(sh//2 - 2, max(0, sw//2 - 10), "SPACE INVADERS")
    stdscr.addstr(sh//2,     max(0, sw//2 - 12), "Press ENTER to start")
    stdscr.addstr(sh//2 + 2, max(0, sw//2 - 14), "a/d or arrows  space=shoot")
    stdscr.addstr(sh//2 + 3, max(0, sw//2 - 8),  "q = quit")
    stdscr.refresh()
    while True:
        key = stdscr.getch()
        if key in (10, 13):
            break
        if key == ord('q'):
            return

    stdscr.nodelay(1)
    stdscr.timeout(80)   # slower so movement is visible on iSH

    # Game state
    player_x = sw // 2
    player_y = sh - 2
    bullets = []
    invaders = []
    inv_dir = 1
    inv_frame = 0
    frame = 0
    score = 0
    lives = 3
    game_over = False

    # Spawn invaders (3 rows)
    for row in range(3):
        for col in range(7):
            invaders.append([5 + col * 5, 3 + row * 2, True])

    while True:
        stdscr.clear()
        key = stdscr.getch()

        if key == ord('q'):
            break
        if game_over:
            stdscr.addstr(sh//2, max(0, sw//2-5), "GAME OVER")
            stdscr.addstr(sh//2+1, max(0, sw//2-6), f"Score: {score}")
            stdscr.addstr(sh//2+2, max(0, sw//2-8), "q to quit")
            stdscr.refresh()
            continue

        # Input
        if key in (curses.KEY_LEFT, ord('a')) and player_x > 2:
            player_x -= 1
        if key in (curses.KEY_RIGHT, ord('d')) and player_x < sw-3:
            player_x += 1
        if key == ord(' ') and len(bullets) < 3:
            bullets.append([player_x, player_y-1])

        # Move bullets
        for b in bullets[:]:
            b[1] -= 1
            if b[1] < 1:
                bullets.remove(b)

        # Move invaders (every 6 frames so it is visible)
        frame += 1
        if frame % 6 == 0:
            xs = [inv[0] for inv in invaders if inv[2]]
            if xs:
                if max(xs) >= sw-4 or min(xs) <= 2:
                    inv_dir *= -1
                    for inv in invaders:
                        if inv[2]:
                            inv[1] += 1
                else:
                    for inv in invaders:
                        if inv[2]:
                            inv[0] += inv_dir
            inv_frame = 1 - inv_frame

        # Collisions
        for b in bullets[:]:
            for inv in invaders:
                if inv[2] and abs(b[0] - inv[0]) < 2 and abs(b[1] - inv[1]) < 1:
                    inv[2] = False
                    if b in bullets:
                        bullets.remove(b)
                    score += 10
                    break

        # Invader reach player
        for inv in invaders:
            if inv[2] and inv[1] >= player_y - 1:
                lives -= 1
                inv[2] = False
                if lives <= 0:
                    game_over = True

        # Draw
        stdscr.addstr(0, 0, f"Score: {score}  Lives: {lives}  q=quit")
        # Player ship
        stdscr.addstr(player_y, player_x, "^" if player_x < sw-1 else "")
        # Bullets
        for b in bullets:
            if 0 < b[1] < sh-1 and 0 < b[0] < sw-1:
                stdscr.addstr(b[1], b[0], "|")
        # Invaders (simple two-frame ASCII)
        for inv in invaders:
            if inv[2] and 0 < inv[1] < sh-1 and 0 < inv[0] < sw-2:
                char = "M" if inv_frame == 0 else "W"
                stdscr.addstr(inv[1], inv[0], char)

        # Win
        if all(not inv[2] for inv in invaders):
            stdscr.addstr(sh//2, max(0, sw//2-4), "YOU WIN")
            stdscr.refresh()
            time.sleep(2)
            break

        stdscr.refresh()

if __name__ == "__main__":
    curses.wrapper(main)
