import pygame

# Define some colors for nodes (consistent with main.py)
RED = (255, 0, 0)         # Closed nodes (visited)
GREEN = (0, 255, 0)       # Open nodes (in queue/priority queue)
WHITE = (255, 255, 255)   # Default empty node
BLACK = (0, 0, 0)         # Barriers
PURPLE = (128, 0, 128)    # Path nodes
ORANGE = (255, 165, 0)    # Start node
GREY = (128, 128, 128)    # Grid lines
TURQUOISE = (64, 224, 208) # End node


class Node:
    """
    Represents a single node (square) in the grid for pathfinding.
    """
    def __init__(self, row, col, size, total_rows):
        """
        Initializes a Node object.

        Args:
            row (int): The row index of the node in the grid.
            col (int): The column index of the node in the grid.
            size (int): The pixel size of one side of the square node.
            total_rows (int): The total number of rows in the grid.
        """
        self.row = row
        self.col = col
        # In Pygame, (0,0) is top-left. x corresponds to col, y corresponds to row.
        self.x = col * size
        self.y = row * size
        self.color = WHITE # Default color
        self.neighbors = [] # List to store valid neighbors for pathfinding
        self.size = size # Size of the node (square)
        self.total_rows = total_rows # Total rows in the grid

    def get_pos(self):
        """Returns the (row, col) position of the node."""
        return self.row, self.col

    def is_closed(self):
        """Checks if the node is a closed (visited) node."""
        return self.color == RED

    def is_open(self):
        """Checks if the node is an open node (in consideration by algorithm)."""
        return self.color == GREEN

    def is_barrier(self):
        """Checks if the node is a barrier."""
        return self.color == BLACK

    def is_start(self):
        """Checks if the node is the start node."""
        return self.color == ORANGE

    def is_end(self):
        """Checks if the node is the end node."""
        return self.color == TURQUOISE

    def reset(self):
        """Resets the node's color to default (white)."""
        self.color = WHITE

    def make_start(self):
        """Sets the node's color to represent a start node."""
        self.color = ORANGE

    def make_closed(self):
        """Sets the node's color to represent a closed (visited) node."""
        self.color = RED

    def make_open(self):
        """Sets the node's color to represent an open node."""
        self.color = GREEN

    def make_barrier(self):
        """Sets the node's color to represent a barrier."""
        self.color = BLACK

    def make_end(self):
        """Sets the node's color to represent an end node."""
        self.color = TURQUOISE

    def make_path(self):
        """Sets the node's color to represent a path node."""
        self.color = PURPLE

    def draw(self, win):
        """
        Draws the node as a filled rectangle on the given Pygame surface.

        Args:
            win (pygame.Surface): The surface to draw the node on.
        """
        pygame.draw.rect(win, self.color, (self.x, self.y, self.size, self.size))

    def update_neighbors(self, grid):
        """
        Updates the list of valid (non-barrier) neighbors for this node.

        Args:
            grid (list[list[Node]]): The 2D grid of nodes.
        """
        self.neighbors = []
        # Check Down neighbor
        if self.row < self.total_rows - 1 and not grid[self.row + 1][self.col].is_barrier():
            self.neighbors.append(grid[self.row + 1][self.col])

        # Check Up neighbor
        if self.row > 0 and not grid[self.row - 1][self.col].is_barrier():
            self.neighbors.append(grid[self.row - 1][self.col])

        # Check Right neighbor
        if self.col < self.total_rows - 1 and not grid[self.row][self.col + 1].is_barrier():
            self.neighbors.append(grid[self.row][self.col + 1])

        # Check Left neighbor
        if self.col > 0 and not grid[self.row][self.col - 1].is_barrier():
            self.neighbors.append(grid[self.row][self.col - 1])

    def __lt__(self, other):
        """
        This method is required for Node objects to be compared in a PriorityQueue or heapq.
        It's a placeholder, as actual comparison should be based on f_score/g_score,
        which are handled by the tuple in the priority queue (e.g., (f_score, count, node)).
        Returns False to indicate that no inherent ordering exists for Node objects themselves.
        """
        return False


class Grid:
    """
    Represents the entire grid of nodes for pathfinding visualization.
    """
    def __init__(self, rows, width):
        """
        Initializes a Grid object.

        Args:
            rows (int): The number of rows (and columns, assuming square grid).
            width (int): The total pixel width of the grid drawing area.
        """
        self.rows = rows
        self.width = width # This is the width of the grid drawing area
        self.gap = self.width // self.rows # Calculate gap (size of each node)
        self.grid_nodes = self.make_grid()

    def make_grid(self):
        """
        Creates the 2D list of Node objects that form the grid.

        Returns:
            list[list[Node]]: The 2D grid of Node objects.
        """
        grid = []
        for i in range(self.rows):
            grid.append([])
            for j in range(self.rows):
                node = Node(i, j, self.gap, self.rows)
                grid[i].append(node)
        return grid

    def draw(self, win):
        """
        Draws all nodes in the grid and then draws the grid lines on top.

        Args:
            win (pygame.Surface): The surface to draw the grid on.
        """
        # Draw each node
        for row in self.grid_nodes:
            for node in row:
                node.draw(win)
        
        # Draw grid lines on top of nodes
        for i in range(self.rows):
            # Draw horizontal lines: (start_x, start_y) to (end_x, end_y)
            pygame.draw.line(win, GREY, (0, i * self.gap), (self.width, i * self.gap))
            # Draw vertical lines: (start_x, start_y) to (end_x, end_y)
            pygame.draw.line(win, GREY, (i * self.gap, 0), (i * self.gap, self.width))

    def get_node(self, row, col):
        """
        Retrieves a node from the grid at the specified row and column.

        Args:
            row (int): The row index.
            col (int): The column index.

        Returns:
            Node: The node at the given coordinates.
        """
        return self.grid_nodes[row][col]

    def get_clicked_pos(self, pos):
        """
        Converts a mouse click pixel position to grid (row, col) coordinates.

        Args:
            pos (tuple): A tuple (x, y) representing the pixel coordinates.

        Returns:
            tuple: A tuple (row, col) representing the grid coordinates.
        """
        x, y = pos
        row = y // self.gap
        col = x // self.gap
        return row, col

    def update_all_neighbors(self):
        """
        Updates the neighbors list for every node in the grid.
        This should be called after modifying barriers.
        """
        for row in self.grid_nodes:
            for node in row:
                node.update_neighbors(self.grid_nodes) # Pass the entire grid_nodes for neighbor calculation

    def clear_path_nodes(self, start_node, end_node):
        """
        Resets all nodes that are not start, end, or barrier to white.
        This effectively clears the visualized path and visited nodes.

        Args:
            start_node (Node): The current start node.
            end_node (Node): The current end node.
        """
        for row in self.grid_nodes:
            for node in row:
                if not (node.is_start() or node.is_end() or node.is_barrier()):
                    node.reset()
        # Ensure start and end nodes retain their colors
        if start_node:
            start_node.make_start()
        if end_node:
            end_node.make_end()