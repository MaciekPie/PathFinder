import pygame as pg
import os
import sys
import math
import heapq
import time

pg.font.init()

TITLE_FONT = pg.font.SysFont("comicsans", 70)
FONT = pg.font.SysFont("comicsans", 40)

WIDTH, HEIGHT = 800, 800
WINDOW = pg.display.set_mode((WIDTH, HEIGHT))
pg.display.set_caption("Path Finder")

BACKGROUND = pg.transform.scale(
    pg.image.load(os.path.join("Static", "background.jpg")),
    (WIDTH, HEIGHT),
)

COLOR_INACTIVE = pg.Color("lightskyblue3")
COLOR_ACTIVE = pg.Color("dodgerblue2")


class InputBox:

    def __init__(self, x, y, w, h, text=""):
        self.rect = pg.Rect(x, y, w, h)
        self.color = COLOR_INACTIVE
        self.text = text
        self.txt_surface = FONT.render(text, True, self.color)
        self.active = False

    def handle_event(self, event):
        if event.type == pg.MOUSEBUTTONDOWN:
            # If the user clicked on the input_box rect.
            if self.rect.collidepoint(event.pos):
                # Toggle the active variable.
                self.active = not self.active
            else:
                self.active = False
            # Change the current color of the input box.
            self.color = COLOR_ACTIVE if self.active else COLOR_INACTIVE
        if event.type == pg.KEYDOWN:
            if self.active:
                if event.key == pg.K_RETURN:
                    print(self.text)
                    self.text = ""
                elif event.key == pg.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    self.text += event.unicode
                # Re-render the text.
                self.txt_surface = FONT.render(self.text, True, self.color)

    def update(self):
        # Resize the box if the text is too long.
        width = max(200, self.txt_surface.get_width() + 10)
        self.rect.w = width

    def draw(self, screen):
        # Blit the text.
        screen.blit(self.txt_surface, (self.rect.x + 5, self.rect.y - 10))  # + 5
        # Blit the rect.
        pg.draw.rect(screen, self.color, self.rect, 2)


class Button:
    def __init__(self, x, y, width, height, text, color, hover_color):
        self.rect = pg.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.font = pg.font.SysFont("comicsans", 40)

    def draw(self, window):
        mouse_pos = pg.mouse.get_pos()
        if self.rect.collidepoint(mouse_pos):
            pg.draw.rect(window, self.hover_color, self.rect)
        else:
            pg.draw.rect(window, self.color, self.rect)

        text_surface = self.font.render(self.text, True, (0, 0, 0))
        window.blit(
            text_surface,
            (
                self.rect.x + (self.rect.width - text_surface.get_width()) / 2,
                self.rect.y + (self.rect.height - text_surface.get_height()) / 2,
            ),
        )

    def is_clicked(self, event):
        if event.type == pg.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                return True
                # change color
        return False


# Creates board displaying maze and path
class Board:
    def __init__(self, table, window_width, window_height, start, destination):
        self.table = table
        self.grid_x_size = len(table[0])
        self.grid_y_size = len(table)
        self.cell_width = window_width // self.grid_x_size
        self.cell_height = window_height // self.grid_y_size
        self.start = start
        self.destination = destination

    def draw(self, window):
        BLACK = (0, 0, 0)
        WHITE = (255, 255, 255)
        GRAY = (128, 128, 128)
        RED = (255, 0, 0)
        GREEN = (0, 255, 0)

        # Check if coordinates are usable
        if (
            not is_valid(self.table, self.start[0], self.start[1])
            or not is_valid(self.table, self.destination[0], self.destination[1])
            or is_blocked(self.table, self.start[0], self.start[1])
            or is_blocked(self.table, self.destination[0], self.destination[1])
        ):
            print("Niepoprawne koordynaty punktow.")
            pg.quit()
            sys.exit()

        # Draw the cube with a small black line around it
        for y in range(self.grid_y_size):
            for x in range(self.grid_x_size):
                cell_x = x * self.cell_width
                cell_y = y * self.cell_height

                # Draw the outline of cube
                pg.draw.rect(
                    window,
                    BLACK,
                    (cell_x, cell_y, self.cell_width, self.cell_height),
                    1,
                )
                cube_color = None
                if self.table[y][x] == 1:
                    cube_color = GRAY
                elif self.start[0] == y and self.start[1] == x:
                    cube_color = RED
                    self.table[y][x] = "S"
                elif self.destination[0] == y and self.destination[1] == x:
                    cube_color = GREEN
                    self.table[y][x] = "P"
                else:
                    cube_color = WHITE

                # Color the inside of cube
                pg.draw.rect(
                    window,
                    cube_color,
                    (cell_x + 1, cell_y + 1, self.cell_width - 2, self.cell_height - 2),
                )

    # Color the path
    def color(self, window, y, x, color):
        if is_blocked(self.table, y, x):
            return
        cell_x = x * self.cell_width
        cell_y = y * self.cell_height
        # ORANGE = (255, 165, 0)
        BLACK = (0, 0, 0)

        # Draw the outline of cube
        pg.draw.rect(
            window,
            BLACK,
            (cell_x, cell_y, self.cell_width, self.cell_height),
            1,
        )

        # Color the inside of cube
        pg.draw.rect(
            window,
            color,
            (cell_x + 1, cell_y + 1, self.cell_width - 2, self.cell_height - 2),
        )


# Check if coordinates are in bounds
def is_valid(table, y, x):
    return 0 <= y < len(table) and 0 <= x < len(table[0])


# Check if a cell is unblocked
def is_blocked(table, y, x):
    return table[y][x] == 1


# Check if reached destination
def is_destination(table, y, x, stop):
    return y == stop[0] and x == stop[1]


# Manages the Dijkstra's algorithm
class Dijkstra:
    def __init__(self, table, board, window, window_width, window_height):
        self.table = table
        self.board = board
        self.window = window
        self.grid_x_size = len(table[0])
        self.grid_y_size = len(table)

        self.window_width = window_width
        self.window_height = window_height
        self.cell_width = window_width // self.grid_x_size
        self.cell_height = window_height // self.grid_y_size

        # Initialize the priority queue as an empty list
        self.queue = []

        # Initialize the list to store tentative distances
        self.distances = [
            [float("inf") for _ in range(self.grid_x_size)]
            for _ in range(self.grid_y_size)
        ]

        # Initialize the set to keep track of visited nodes
        self.visited = set()

        # Initialize the dict to store nodes for backtracking
        self.history = {}

        # Initialize the list to store nodes for coloring the path
        self.path = []

    def highlight_node(self, node, color, delay):
        if not is_blocked(self.table, node[0], node[1]):
            self.board.color(self.window, node[0], node[1], color)
            pg.display.flip()
            time.sleep(delay)
            self.board.color(
                self.window, node[0], node[1], (255, 255, 255)
            )  # Reset to white
            pg.display.flip()

    def find(self, start_node, end_node):

        heapq.heappush(self.queue, (0, start_node))
        self.distances[start_node[0]][start_node[1]] = 0

        while self.queue:
            distance, current_node = heapq.heappop(self.queue)
            if current_node in self.visited:
                continue
            self.visited.add(current_node)

            GREEN = (0, 255, 0)
            """for i in self.history:
                self.color(self.history[i][0], self.history[i][1], GREEN)"""

            if current_node == end_node:
                print(f"Found! {current_node}")
                break

            moves = [
                (-1, 0),
                (-1, 1),
                (0, 1),
                (1, 1),
                (1, 0),
                (1, -1),
                (0, -1),
                (-1, -1),
            ]
            for move in moves:
                dy, dx = move
                new_y = current_node[0] + dy
                new_x = current_node[1] + dx
                new_node = (new_y, new_x)
                if (
                    # 0 <= new_y < self.grid_y_size
                    # and 0 <= new_x < self.grid_x_size
                    is_valid(self.table, new_y, new_x)
                    and not is_blocked(self.table, new_y, new_x)
                ):
                    # Highlight current node
                    # self.highlight_node((new_y, new_x), GREEN, 0.1)

                    if new_node not in self.visited:

                        if dy != 0 and dx != 0:
                            tentative_distance = distance + math.sqrt(2)
                        else:
                            tentative_distance = distance + 1

                        if tentative_distance < self.distances[new_y][new_x]:
                            self.distances[new_y][new_x] = tentative_distance
                            heapq.heappush(self.queue, (tentative_distance, new_node))
                            self.history[new_node] = current_node

        heapq.heapify(self.queue)

    def trace_back(self, start_node, end_node):
        current_node = end_node

        while current_node != start_node:
            self.path.append(current_node)
            current_node = self.history.get(current_node)
            if current_node is None:
                print("Path not found.")
                return []

        self.path.append(start_node)
        self.path.reverse()
        return self.path

    def color(self, y, x, color):
        self.board.color(self.window, y, x, color)
        """cell_x = x * self.cell_width
        cell_y = y * self.cell_height
        # ORANGE = (255, 165, 0)

        pg.draw.rect(
            self.window,
            color,
            (cell_x + 1, cell_y + 1, self.cell_width - 2, self.cell_height - 2),
        )"""


# Manages the A* algorithm
class A_Star:
    def __init__(self, table, board, window, window_width, window_height):
        self.table = table
        self.board = board
        self.window = window
        self.grid_x_size = len(table[0])
        self.grid_y_size = len(table)

        self.window_width = window_width
        self.window_height = window_height
        self.cell_width = window_width // self.grid_x_size
        self.cell_height = window_height // self.grid_y_size

        # Initialize the priority queue as an empty list
        self.queue = []

        # Initialize the list to store tentative distances
        self.distances = [
            [float("inf") for _ in range(self.grid_x_size)]
            for _ in range(self.grid_y_size)
        ]

        # Initialize the set to keep track of visited nodes
        self.visited = set()

        # Initialize the dict to store nodes for backtracking
        self.history = {}

        # Initialize the list to store nodes for coloring the path
        self.path = []

    def find(self, start_node, end_node):
        pass


table = [
    [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0],
    [0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1],
    [0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0],
    [0, 0, 0, 0, 1, 0, 1, 1, 1, 0, 1, 1, 1, 1, 0, 0, 0, 0, 1, 0],
    [0, 0, 0, 1, 1, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0],
    [1, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0],
    [0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0],
    [0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 1, 1, 1, 1],
    [0, 1, 1, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0],
    [0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1],
    [0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 1, 1, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1, 1, 0, 1, 0, 0],
    [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0],
    [1, 1, 0, 0, 1, 1, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0, 1, 0, 0, 0],
    [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0],
    [0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1],
    [0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0],
]

"""for i in table:
    print(i)

print()
print("Enter the coordinates of starting point (0-19):")
s_x = int(input("X: "))
s_y = int(input("Y: "))
print("Enter the coordinates of destination point (0-19):")
d_x = int(input("X: "))
d_y = int(input("Y: "))

S = (s_y, s_x)
D = (d_y, d_x)"""


#######################################################


def main(algorithm, S, D):
    print(S)
    on = True
    # FPS = 60
    how = 0
    # clock = pg.time.Clock()
    alg = ""

    board = Board(table, WIDTH, HEIGHT, S, D)

    while on:
        # clock.tick(FPS)

        # Clear the screen
        WINDOW.fill((0, 0, 0))

        # Return to main menu if 1 algorithm was used more than 180 times ?
        # if how > FPS * 3:
        #    on = False

        for event in pg.event.get():
            if event.type == pg.QUIT:
                quit()
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_SPACE:
                    main_menu()

        if algorithm == "Dijkstra":
            alg = Dijkstra(table, board, WINDOW, WIDTH, HEIGHT)
        elif algorithm == "A*":
            alg = A_Star(table, board, WINDOW, WIDTH, HEIGHT)

        board.draw(WINDOW)

        # Use Dijkstra's algorithm
        if how == 0:
            alg.find(S, D)

            pat = alg.trace_back(S, D)
            if pat:
                print(f"Path of algorithm in format (y,x): {pat}")
                pat.pop(0)
                pat.pop(-1)
                how += 1
            else:
                print("Algorithm couldn't find path")
                how += 1

        ORANGE = (255, 165, 0)

        for i in pat:
            alg.color(i[0], i[1], ORANGE)

        # Update the display
        pg.display.flip()


def main_menu():
    # font = pg.font.SysFont("comicsans", 70)
    running = True

    clock = pg.time.Clock()

    algorithm = ""

    w = 200
    h = 40

    input_x1 = InputBox(WIDTH / 4 - 0.5 * w, 0.5 * HEIGHT - 0.5 * h, w, h)
    input_y1 = InputBox(WIDTH / 4 - 0.5 * w, 0.6 * HEIGHT - 0.5 * h, w, h)
    input_x2 = InputBox(WIDTH / 4 + WIDTH / 2 - 0.5 * w, 0.5 * HEIGHT - 0.5 * h, w, h)
    input_y2 = InputBox(WIDTH / 4 + WIDTH / 2 - 0.5 * w, 0.6 * HEIGHT - 0.5 * h, w, h)
    input_boxes = [input_x1, input_y1, input_x2, input_y2]

    dijkstra_button = Button(
        WIDTH / 4 - 0.5 * w,
        0.3 * HEIGHT - 0.5 * h,
        200,
        60,
        "Dijkstra",
        (255, 0, 0),
        (150, 0, 0),
    )
    astar_button = Button(
        WIDTH / 4 + WIDTH / 2 - 0.5 * w,
        0.3 * HEIGHT - 0.5 * h,
        200,
        60,
        "A*",
        (0, 0, 255),
        (0, 0, 150),
    )

    enter_button = Button(
        WIDTH / 2 - 0.5 * w,
        0.8 * HEIGHT - 0.5 * h,
        200,
        60,
        "Go",
        (130, 60, 255),
        (75, 40, 150),
    )

    while running:
        WINDOW.blit(BACKGROUND, (0, 0))
        title = TITLE_FONT.render("Choose your settings", 1, (255, 255, 255))
        WINDOW.blit(
            title,
            (WIDTH / 2 - title.get_width() / 2, 0.1 * HEIGHT - title.get_height() / 2),
        )

        start = FONT.render("Start:", 1, (255, 255, 255))
        destination = FONT.render("Destination:", 1, (255, 255, 255))

        WINDOW.blit(
            start,
            (WIDTH / 4 - start.get_width() / 2, 0.4 * HEIGHT - start.get_height() / 2),
        )
        WINDOW.blit(
            destination,
            (
                WIDTH / 4 + WIDTH / 2 - destination.get_width() / 2,
                0.4 * HEIGHT - destination.get_height() / 2,
            ),
        )

        # done = False

        # pg.display.update()

        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            if event.type == pg.KEYDOWN:  # change to spacebar
                if event.key == pg.K_SPACE:
                    main()

            if dijkstra_button.is_clicked(event):
                algorithm = "Dijkstra"

            if astar_button.is_clicked(event):
                algorithm = "A*"

            for box in input_boxes:
                box.handle_event(event)

            if enter_button.is_clicked(event):
                s_x = int(input_x1.text)
                s_y = int(input_y1.text)
                d_x = int(input_x2.text)
                d_y = int(input_y2.text)

                S = (s_y, s_x)
                D = (d_y, d_x)

                main(algorithm, S, D)

        for box in input_boxes:
            box.update()

        for box in input_boxes:
            box.draw(WINDOW)

        dijkstra_button.draw(WINDOW)
        astar_button.draw(WINDOW)

        enter_button.draw(WINDOW)

        pg.display.flip()
        clock.tick(60)

    pg.quit()
    sys.exit()


main_menu()
