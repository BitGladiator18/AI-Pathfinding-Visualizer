import pygame
import pygame_gui
from grid import Grid, Node
from algorithms import bfs, dfs, dijkstra, astar
import time

# --- Constants & Globals ---
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
ORANGE = (255, 165, 0)
TURQUOISE = (64, 224, 208)
PURPLE = (128, 0, 128) # Path color
GREY = (128, 128, 128) # Grid lines

# ADJUSTED DIMENSIONS for better layout
UI_WIDTH = 200  # Increased UI width for better label fitting
GRID_WIDTH = 600  # Fixed grid area width
TOTAL_WIDTH = GRID_WIDTH + UI_WIDTH
TOTAL_HEIGHT = GRID_WIDTH # Assuming square window matching grid width

# Define the rectangle for the grid area. Used for partial updates.
GRID_RECT = pygame.Rect(0, 0, GRID_WIDTH, TOTAL_HEIGHT)

# Initialize Pygame and Font
pygame.init()
pygame.font.init()
FONT = pygame.font.SysFont("comicsans", 20)
SMALL_FONT = pygame.font.SysFont("comicsans", 16) # For smaller stats text

WIN = pygame.display.set_mode((TOTAL_WIDTH, TOTAL_HEIGHT))
pygame.display.set_caption("AI Pathfinding Visualizer")

# Initialize Pygame GUI manager
manager = pygame_gui.UIManager((TOTAL_WIDTH, TOTAL_HEIGHT))

class PathfindingVisualizer:
    """
    Manages the state and data for the pathfinding visualization.
    Encapsulates grid, start/end nodes, algorithm selection, and statistics.
    """
    def __init__(self, rows, grid_width):
        self.rows = rows
        self.grid_width = grid_width
        self.grid_obj = Grid(self.rows, self.grid_width)
        self.start = None
        self.end = None
        self.selected_algorithm = "A*"  # Default algorithm
        self.last_visited_count = 0
        self.last_path_length = 0
        self.last_time_taken = 0.0
        self.status_message = "Status: Ready"
        self.paused = [False] # Using a list for mutability when passed to algorithms

    def reset_grid(self):
        """Resets the entire grid and all state variables."""
        self.start = None
        self.end = None
        self.grid_obj = Grid(self.rows, self.grid_width)
        self.reset_stats()

    def clear_path(self):
        """Clears only the pathfinding visualization (visited, open, path nodes)."""
        if self.start and self.end:
            self.grid_obj.clear_path_nodes(self.start, self.end)
        self.reset_stats()

    def reset_stats(self):
        """Resets the displayed statistics."""
        self.last_visited_count = 0
        self.last_path_length = 0
        self.last_time_taken = 0.0
        self.status_message = f"Algorithm: {self.selected_algorithm}"
        self.paused[0] = False # Ensure pause is reset
        
    def set_start_node(self, node):
        """Sets the start node."""
        if self.start:
            self.start.reset()
        self.start = node
        self.start.make_start()

    def set_end_node(self, node):
        """Sets the end node."""
        if self.end:
            self.end.reset()
        self.end = node
        self.end.make_end()

    def draw_stats_overlay(self, surface):
        """Draws pathfinding statistics on the given surface."""
        stats_text_surface_1 = FONT.render(f"Visited Nodes: {self.last_visited_count}", 1, BLACK)
        stats_text_surface_2 = FONT.render(f"Path Length: {self.last_path_length}", 1, BLACK)
        stats_text_surface_3 = FONT.render(f"Time Taken: {self.last_time_taken:.4f}s", 1, BLACK)
        stats_text_surface_4 = FONT.render(self.status_message, 1, BLACK)

        surface.blit(stats_text_surface_1, (10, 10))
        surface.blit(stats_text_surface_2, (10, 40))
        surface.blit(stats_text_surface_3, (10, 70))
        surface.blit(stats_text_surface_4, (10, 100))

# --- Draw Function ---
def draw(win, visualizer_state):
    """
    Draws the grid and the statistics overlay.
    This function is ONLY responsible for drawing these elements and updating
    the relevant portion of the display. It should NOT update the GUI manager
    or draw GUI elements.
    """
    # Create a subsurface for the grid area to draw on
    grid_surface = win.subsurface(GRID_RECT)
    grid_surface.fill(WHITE) # Fill only the grid area with white

    visualizer_state.grid_obj.draw(grid_surface) # Draw the grid nodes and lines on this subsurface
    visualizer_state.draw_stats_overlay(grid_surface) # Draw statistics on the grid surface
    
    # IMPORTANT: Update only the grid portion of the display when called from algorithms.
    # This prevents UI elements from flickering or being cleared.
    pygame.display.update(GRID_RECT) 
    # NO manager.update() or manager.draw_ui() here! These are handled in the main loop.


# --- Main Loop ---
def main(win, width):
    visualizer_state = PathfindingVisualizer(ROWS, width)

    run = True
    clock = pygame.time.Clock()

    # --- UI Elements --- (Moved here to use manager directly, still relative to ui_panel)
    # Create a UIPanel for the sidebar UI elements
    ui_panel_rect = pygame.Rect(GRID_WIDTH, 0, UI_WIDTH, TOTAL_HEIGHT)
    ui_panel = pygame_gui.elements.UIPanel(relative_rect=ui_panel_rect, manager=manager,
                                            object_id='#ui_panel')

    # Dropdown for algorithm selection
    algo_dropdown_rect = pygame.Rect(10, 10, UI_WIDTH - 20, 30)
    algo_dropdown = pygame_gui.elements.UIDropDownMenu(
        options_list=["BFS", "DFS", "Dijkstra", "A*"],
        starting_option=visualizer_state.selected_algorithm,
        relative_rect=algo_dropdown_rect,
        manager=manager,
        container=ui_panel
    )

    # Start Button
    start_button_rect = pygame.Rect(10, 50, UI_WIDTH - 20, 30)
    start_button = pygame_gui.elements.UIButton(
        relative_rect=start_button_rect,
        text="Start Algorithm",
        manager=manager,
        container=ui_panel
    )

    # Clear Button (Clear Path only)
    clear_button_rect = pygame.Rect(10, 90, UI_WIDTH - 20, 30)
    clear_button = pygame_gui.elements.UIButton(
        relative_rect=clear_button_rect,
        text="Clear Path",
        manager=manager,
        container=ui_panel
    )

    # Clear All Button (Clear entire grid)
    clear_all_button_rect = pygame.Rect(10, 130, UI_WIDTH - 20, 30)
    clear_all_button = pygame_gui.elements.UIButton(
        relative_rect=clear_all_button_rect,
        text="Clear All",
        manager=manager,
        container=ui_panel
    )

    # Pause Button
    pause_button_rect = pygame.Rect(10, 170, UI_WIDTH - 20, 30)
    pause_button = pygame_gui.elements.UIButton(
        relative_rect=pause_button_rect,
        text="Pause",
        manager=manager,
        container=ui_panel
    )

    # Speed Slider
    speed_slider_rect = pygame.Rect(10, 230, UI_WIDTH - 20, 20)
    speed_slider = pygame_gui.elements.UIHorizontalSlider(
        relative_rect=speed_slider_rect,
        start_value=20,  # Default delay
        value_range=(0, 200), # 0ms to 200ms delay
        manager=manager,
        container=ui_panel
    )

    # Speed Slider Label
    speed_slider_label_rect = pygame.Rect(10, 210, UI_WIDTH - 20, 20)
    speed_slider_label = pygame_gui.elements.UILabel(
        relative_rect=speed_slider_label_rect,
        text=f"Animation Speed ({int(speed_slider.get_current_value())} ms):",
        manager=manager,
        container=ui_panel
    )

    while run:
        # Calculate time_delta for pygame_gui manager update
        time_delta = clock.tick(60)/1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

            # --- Handle Pygame GUI Events ---
            if event.type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
                if event.ui_element == algo_dropdown:
                    visualizer_state.selected_algorithm = event.text
                    visualizer_state.status_message = f"Algorithm: {visualizer_state.selected_algorithm}"
            
            if event.type == pygame_gui.UI_HORIZONTAL_SLIDER_MOVED:
                if event.ui_element == speed_slider:
                    speed_slider_label.set_text(f'Animation Speed ({int(event.current_value)} ms):') 

            if event.type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element == start_button:
                    if visualizer_state.start and visualizer_state.end:
                        visualizer_state.clear_path() # Clear previous path/visited states for a new run
                        
                        # Ensure neighbors are updated, especially after barrier changes
                        visualizer_state.grid_obj.update_all_neighbors()
                        
                        found = False
                        # Pass a lambda to the algorithm for drawing the grid.
                        grid_draw_lambda = lambda: draw(win, visualizer_state)

                        start_time = time.time()
                        
                        # Pass manager and WIN to algorithms for event processing during pause
                        current_grid_nodes = visualizer_state.grid_obj.grid_nodes
                        start_node = visualizer_state.start
                        end_node = visualizer_state.end
                        delay = speed_slider.get_current_value()
                        paused_ref = visualizer_state.paused

                        if visualizer_state.selected_algorithm == "BFS":
                            found, visualizer_state.last_visited_count, visualizer_state.last_path_length = bfs(grid_draw_lambda, current_grid_nodes, start_node, end_node, delay, paused_ref, manager, WIN)
                        elif visualizer_state.selected_algorithm == "DFS":
                            found, visualizer_state.last_visited_count, visualizer_state.last_path_length = dfs(grid_draw_lambda, current_grid_nodes, start_node, end_node, delay, paused_ref, manager, WIN)
                        elif visualizer_state.selected_algorithm == "Dijkstra":
                            found, visualizer_state.last_visited_count, visualizer_state.last_path_length = dijkstra(grid_draw_lambda, current_grid_nodes, start_node, end_node, delay, paused_ref, manager, WIN)
                        elif visualizer_state.selected_algorithm == "A*":
                            found, visualizer_state.last_visited_count, visualizer_state.last_path_length = astar(grid_draw_lambda, current_grid_nodes, start_node, end_node, delay, paused_ref, manager, WIN)
                        
                        end_time = time.time()
                        visualizer_state.last_time_taken = end_time - start_time
                        
                        # Set final status after algorithm completes
                        if found:
                            visualizer_state.status_message = f"Algorithm: {visualizer_state.selected_algorithm} - Path Found!"
                        else:
                            visualizer_state.status_message = f"Algorithm: {visualizer_state.selected_algorithm} - No Path Found!"
                        
                        # A final draw call to update the display with the results and stats
                        draw(win, visualizer_state) # Draw grid and stats for final state
                        manager.update(0.01) # Update UI for immediate refresh of results
                        manager.draw_ui(win) # Draw UI
                        pygame.display.flip() # Final display update

                    else:
                        # Use status_message for feedback
                        if not visualizer_state.start and not visualizer_state.end:
                            visualizer_state.status_message = "Status: Please set Start and End nodes!"
                        elif not visualizer_state.start:
                            visualizer_state.status_message = "Status: Please set Start node!"
                        elif not visualizer_state.end:
                            visualizer_state.status_message = "Status: Please set End node!"

                elif event.ui_element == clear_button: # Clear Path only
                    visualizer_state.clear_path()
                    
                elif event.ui_element == clear_all_button: # Clear All
                    visualizer_state.reset_grid() # Recreate grid to clear all nodes
                
                elif event.ui_element == pause_button:
                    visualizer_state.paused[0] = not visualizer_state.paused[0]
                    if visualizer_state.paused[0]:
                        pause_button.set_text('Resume')
                        if not visualizer_state.status_message.endswith(" (PAUSED)"):
                            visualizer_state.status_message += " (PAUSED)"
                    else:
                        pause_button.set_text('Pause')
                        if visualizer_state.status_message.endswith(" (PAUSED)"):
                            visualizer_state.status_message = visualizer_state.status_message.replace(" (PAUSED)", "")
            
            # Process all events through the GUI manager
            manager.process_events(event)
            
        # --- Handle Mouse Clicks for Setting Start/End/Initial Barrier ---
        mouse_pos = pygame.mouse.get_pos()
        if 0 <= mouse_pos[0] < GRID_WIDTH and 0 <= mouse_pos[1] < TOTAL_HEIGHT:
            if pygame.mouse.get_pressed()[0] and event.type == pygame.MOUSEBUTTONDOWN: # Left click for start/end
                row, col = visualizer_state.grid_obj.get_clicked_pos(mouse_pos)
                if 0 <= row < ROWS and 0 <= col < ROWS:
                    node = visualizer_state.grid_obj.get_node(row, col)
                    if not visualizer_state.start and node != visualizer_state.end:
                        visualizer_state.set_start_node(node)
                    elif not visualizer_state.end and node != visualizer_state.start:
                        visualizer_state.set_end_node(node)
                    # If both start and end are set, this single click will act as a barrier
                    elif node != visualizer_state.start and node != visualizer_state.end:
                        node.make_barrier()
            elif pygame.mouse.get_pressed()[2] and event.type == pygame.MOUSEBUTTONDOWN: # Right click to clear start/end
                 row, col = visualizer_state.grid_obj.get_clicked_pos(mouse_pos)
                 if 0 <= row < ROWS and 0 <= col < ROWS:
                    node = visualizer_state.grid_obj.get_node(row, col)
                    node.reset()
                    if node == visualizer_state.start:
                        visualizer_state.start = None
                    elif node == visualizer_state.end:
                        visualizer_state.end = None
            
            # --- Handle Mouse Dragging for Drawing/Erasing Barriers (continuous) ---
            row, col = visualizer_state.grid_obj.get_clicked_pos(mouse_pos)
            if 0 <= row < ROWS and 0 <= col < ROWS: # Ensure position is within grid bounds
                node = visualizer_state.grid_obj.get_node(row, col)

                # Left mouse button is held down for drawing barriers
                if pygame.mouse.get_pressed()[0]:
                    if node != visualizer_state.start and node != visualizer_state.end and not node.is_barrier():
                        node.make_barrier()
                
                # Right mouse button is held down for erasing barriers/path
                elif pygame.mouse.get_pressed()[2]:
                    if node != visualizer_state.start and node != visualizer_state.end:
                        node.reset()


        # --- Update and Draw ---
        manager.update(time_delta) # Update GUI elements' internal state
        draw(win, visualizer_state) # Draw the grid and stats overlay (updates grid portion of screen)
        manager.draw_ui(win) # Draw the GUI elements on top of the grid and stats
        
        pygame.display.flip() # Update the entire display (more robust for main loop)

    pygame.quit()

if __name__ == "__main__":
    ROWS = 50
    main(WIN, GRID_WIDTH)