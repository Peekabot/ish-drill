#!/usr/bin/env python3
"""
Asteroids for iSH (terminal)
Controls: a/d rotate, w thrust, space shoot, q quit
"""
import curses
import math
import random
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
    stdscr.addstr(sh//2 - 2, max(0, sw//2 - 8), "ASTEROIDS")
    stdscr.addstr(sh//2,     max(0, sw//2 - 12), "Press ENTER to start")
    stdscr.addstr(sh//2 + 2, max(0, sw//2 - 16), "a/d rotate  w thrust  space shoot")
    stdscr.addstr(sh//2 + 3, max(0, sw//2 - 8),  "q = quit")
    stdscr.refresh()
    while True:
        key = stdscr.getch()
        if key in (10, 13):
            break
        if key == ord('q'):
            return

    stdscr.nodelay(1)
    stdscr.timeout(80)

    # Ship
    sx, sy = sw // 2, sh // 2
    angle = 0.0          # radians, 0 = right
    vx, vy = 0.0, 0.0
    bullets = []         # [x, y, vx, vy, life]
    rocks = []           # [x, y, vx, vy, size]
    score = 0
    lives = 3
    game_over = False
    frame = 0

    # Spawn some rocks
    for _ in range(5):
        rocks.append([
            random.randint(2, sw-3),
            random.randint(2, sh-3),
            random.uniform(-0.4, 0.4),
            random.uniform(-0.2, 0.2),
            random.choice([2, 3])
        ])

    ship_chars = ["^", ">", "v", "<"]

    try:
        while True:
            # Clear play area
            for y in range(1, sh-1):
                stdscr.move(y, 0)
                stdscr.clrtoeol()

            key = stdscr.getch()
            if key == ord('q'):
                break
            if game_over:
                stdscr.addstr(sh//2, max(0, sw//2-5), "GAME OVER")
                stdscr.addstr(sh//2+1, max(0, sw//2-6), f"Score: {score}")
                stdscr.addstr(sh//2+2, max(0, sw//2-8), "q to quit")
                stdscr.refresh()
                time.sleep(0.1)
                continue

            # Controls
            if key == ord('a'):
                angle -= 0.3
            if key == ord('d'):
                angle += 0.3
            if key == ord('w'):
                vx += math.cos(angle) * 0.15
                vy += math.sin(angle) * 0.08
            if key == ord(' ') and len(bullets) < 4:
                bullets.append([
                    sx, sy,
                    math.cos(angle) * 1.2,
                    math.sin(angle) * 0.6,
                    30
                ])

            # Physics
            sx = (sx + vx) % sw
            sy = (sy + vy) % sh
            vx *= 0.98
            vy *= 0.98

            # Bullets
            for b in bullets[:]:
                b[0] = (b[0] + b[2]) % sw
                b[1] = (b[1] + b[3]) % sh
                b[4] -= 1
                if b[4] <= 0:
                    bullets.remove(b)

            # Rocks
            for r in rocks[:]:
                r[0] = (r[0] + r[2]) % sw
                r[1] = (r[1] + r[3]) % sh

            # Collisions: bullets vs rocks
            for b in bullets[:]:
                for r in rocks[:]:
                    if abs(b[0] - r[0]) < r[4] and abs(b[1] - r[1]) < r[4]:
                        if b in bullets:
                            bullets.remove(b)
                        if r in rocks:
                            rocks.remove(r)
                        score += 20 if r[4] > 2 else 10
                        # Split big rocks
                        if r[4] > 2:
                            for _ in range(2):
                                rocks.append([
                                    r[0], r[1],
                                    random.uniform(-0.5, 0.5),
                                    random.uniform(-0.3, 0.3),
                                    1
                                ])
                        break

            # Ship vs rocks
            for r in rocks:
                if abs(sx - r[0]) < r[4]+1 and abs(sy - r[1]) < r[4]+1:
                    lives -= 1
                    sx, sy = sw//2, sh//2
                    vx = vy = 0
                    if lives <= 0:
                        game_over = True
                    break

            # Respawn rocks if none left
            if not rocks and not game_over:
                for _ in range(4 + score // 100):
                    rocks.append([
                        random.randint(2, sw-3),
                        random.randint(2, sh-3),
                        random.uniform(-0.5, 0.5),
                        random.uniform(-0.3, 0.3),
                        random.choice([2, 3])
                    ])

            # Draw
            stdscr.addstr(0, 0, f"Score: {score}  Lives: {lives}  q=quit")
            # Ship direction char
            dir_idx = int(((angle % (2*math.pi)) / (math.pi/2))) % 4
            ship = ship_chars[dir_idx]
            if 0 <= int(sy) < sh-1 and 0 <= int(sx) < sw-1:
                stdscr.addstr(int(sy), int(sx), ship)
            # Bullets
            for b in bullets:
                if 1 <= int(b[1]) < sh-1 and 0 <= int(b[0]) < sw-1:
                    stdscr.addstr(int(b[1]), int(b[0]), ".")
            # Rocks
            for r in rocks:
                if 1 <= int(r[1]) < sh-1 and 0 <= int(r[0]) < sw-1:
                    stdscr.addstr(int(r[1]), int(r[0]), "O" if r[4] > 1 else "o")

            stdscr.refresh()
            time.sleep(0.04)
            frame += 1

    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    curses.wrapper(main)
