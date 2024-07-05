import pygame as pg
import sys
import math
import heapq


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
    def color(self, window, y, x):
        cell_x = x * self.cell_width
        cell_y = y * self.cell_height
        ORANGE = (255, 165, 0)
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
            ORANGE,
            (cell_y + 1, cell_x + 1, self.cell_width - 2, self.cell_height - 2),
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

    def find(self, start_node, end_node):

        heapq.heappush(self.queue, (0, start_node))
        self.distances[start_node[0]][start_node[1]] = 0

        while self.queue:
            distance, current_node = heapq.heappop(self.queue)
            if current_node in self.visited:
                continue
            self.visited.add(current_node)

            """GREEN = (0, 255, 0)
            for i in self.history:
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
                    0 <= new_y < self.grid_y_size
                    and 0 <= new_x < self.grid_x_size
                    and not is_blocked(self.table, new_y, new_x)
                ):
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
        cell_x = x * self.cell_width
        cell_y = y * self.cell_height
        # ORANGE = (255, 165, 0)

        pg.draw.rect(
            self.window,
            color,
            (cell_x + 1, cell_y + 1, self.cell_width - 2, self.cell_height - 2),
        )


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

for i in table:
    print(i)

print()
print("Enter the coordinates of starting point (0-19):")
s_x = int(input("X: "))
s_y = int(input("Y: "))
print("Enter the coordinates of destination point (0-19):")
d_x = int(input("X: "))
d_y = int(input("Y: "))

S = (s_y, s_x)
D = (d_y, d_x)


pg.init()

window_width = 800
window_height = 800
window = pg.display.set_mode((window_width, window_height))
pg.display.set_caption("Path Finder")

board = Board(table, window_width, window_height, S, D)

how = 0

running = True

while running:
    for event in pg.event.get():
        if event.type == pg.QUIT:
            running = False

    # Clear the screen
    window.fill((0, 0, 0))

    alg = Dijkstra(table, board, window, window_width, window_height)

    board.draw(window)

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


pg.quit()
sys.exit()
