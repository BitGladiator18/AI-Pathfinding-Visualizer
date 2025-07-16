import pygame
import pygame_gui # Import for processing events during pause
from collections import deque
import heapq
# Removed from queue import PriorityQueue as we are directly using heapq for A*
from utils.heuristics import h

def reconstruct_path(came_from, current, draw_func):
    """
    Reconstructs the path from the end node back to the start node
    and marks path nodes for visualization.
    
    Args:
        came_from (dict): A dictionary mapping a node to the node that preceded it in the shortest path.
        current (Node): The current node, starting from the end node.
        draw_func (function): A function to call for updating the visual display.
    
    Returns:
        list: A list of nodes forming the reconstructed path (excluding the start node).
    """
    path_nodes = []
    while current in came_from:
        current = came_from[current]
        if not current.is_start():
            path_nodes.append(current)
            current.make_path()
        draw_func() # Only draws grid and calls pygame.display.update()
        pygame.time.delay(10) # Small delay for visual effect
    return path_nodes

# --- BFS Algorithm ---
def bfs(draw_func, grid, start, end, delay_ms, paused_ref, manager, window_surface):
    """
    Performs Breadth-First Search (BFS) to find the shortest path.

    Args:
        draw_func (function): Function to draw the grid and update the display.
        grid (list[list[Node]]): The 2D grid of nodes.
        start (Node): The starting node.
        end (Node): The target end node.
        delay_ms (int): Delay in milliseconds between node explorations for visualization.
        paused_ref (list): A mutable reference ([boolean]) to control pause state.
        manager (pygame_gui.UIManager): The GUI manager for processing events.
        window_surface (pygame.Surface): The main window surface for drawing GUI elements during pause.

    Returns:
        tuple: (found_path_boolean, visited_nodes_count, path_length)
    """
    queue = deque()
    queue.append(start)
    visited = {start}
    came_from = {}
    
    visited_nodes_count = 0

    while queue:
        # --- Handle Pause and Quit Events ---
        if paused_ref[0]: # Check if paused
            while paused_ref[0]:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        return False, visited_nodes_count, 0 # Return interrupted status
                    manager.process_events(event) # Process GUI events even when paused
                
                # Draw grid and UI while paused to keep app responsive
                draw_func() # This draws the grid and calls pygame.display.update()
                manager.update(0.01) # Update GUI elements for the pause frame
                manager.draw_ui(window_surface) # Draw GUI elements
                pygame.display.flip() # Update the entire display for pause frame
                
                pygame.time.wait(50) # Small wait to prevent 100% CPU usage while paused
        
        current = queue.popleft()

        if current == end:
            path_nodes = reconstruct_path(came_from, end, draw_func)
            end.make_end()
            start.make_start()
            return True, visited_nodes_count, len(path_nodes) + 1

        for neighbor in current.neighbors:
            if neighbor not in visited and not neighbor.is_barrier():
                visited.add(neighbor)
                came_from[neighbor] = current
                queue.append(neighbor)
                if neighbor != end:
                    neighbor.make_open()
        
        if current != start and current != end:
            current.make_closed()
            visited_nodes_count += 1

        draw_func() # Update visualization after exploring a node's neighbors
        pygame.time.delay(delay_ms) # Use the passed delay

    return False, visited_nodes_count, 0

# --- DFS Algorithm ---
def dfs(draw_func, grid, start, end, delay_ms, paused_ref, manager, window_surface):
    """
    Performs Depth-First Search (DFS) to find a path.

    Args:
        draw_func (function): Function to draw the grid and update the display.
        grid (list[list[Node]]): The 2D grid of nodes.
        start (Node): The starting node.
        end (Node): The target end node.
        delay_ms (int): Delay in milliseconds between node explorations for visualization.
        paused_ref (list): A mutable reference ([boolean]) to control pause state.
        manager (pygame_gui.UIManager): The GUI manager for processing events.
        window_surface (pygame.Surface): The main window surface for drawing GUI elements during pause.

    Returns:
        tuple: (found_path_boolean, visited_nodes_count, path_length)
    """
    stack = [start]
    visited = {start}
    came_from = {}
    
    visited_nodes_count = 0

    while stack:
        # --- Handle Pause and Quit Events ---
        if paused_ref[0]:
            while paused_ref[0]:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        return False, visited_nodes_count, 0
                    manager.process_events(event)
                draw_func()
                manager.update(0.01)
                manager.draw_ui(window_surface)
                pygame.display.flip()
                pygame.time.wait(50)

        current = stack.pop()

        if current == end:
            path_nodes = reconstruct_path(came_from, end, draw_func)
            end.make_end()
            start.make_start()
            return True, visited_nodes_count, len(path_nodes) + 1

        # Only mark as closed if it's not start or end and we haven't already processed it
        # The check for current != start and current != end is applied AFTER checking if current is end
        if current != start and current != end:
            current.make_closed()
            visited_nodes_count += 1

        draw_func()
        pygame.time.delay(delay_ms)

        # Iterate in reverse to push neighbors, making the "leftmost" or "first" neighbor
        # explored first when popped from stack (typical DFS behavior for visualization)
        for neighbor in reversed(current.neighbors): 
            if neighbor not in visited and not neighbor.is_barrier():
                visited.add(neighbor)
                came_from[neighbor] = current
                stack.append(neighbor)
                if neighbor != end:
                    neighbor.make_open()

    return False, visited_nodes_count, 0


# --- Dijkstra's Algorithm ---
def dijkstra(draw_func, grid, start, end, delay_ms, paused_ref, manager, window_surface):
    """
    Performs Dijkstra's Algorithm to find the shortest path.

    Args:
        draw_func (function): Function to draw the grid and update the display.
        grid (list[list[Node]]): The 2D grid of nodes.
        start (Node): The starting node.
        end (Node): The target end node.
        delay_ms (int): Delay in milliseconds between node explorations for visualization.
        paused_ref (list): A mutable reference ([boolean]) to control pause state.
        manager (pygame_gui.UIManager): The GUI manager for processing events.
        window_surface (pygame.Surface): The main window surface for drawing GUI elements during pause.

    Returns:
        tuple: (found_path_boolean, visited_nodes_count, path_length)
    """
    g_score = {node: float("inf") for row in grid for node in row}
    g_score[start] = 0

    count = 0
    # Priority Queue stores (g_score, tie_breaker, node)
    open_set = [(0, count, start)] 

    came_from = {}
    
    # To quickly check if a node is in the open_set without iterating the heap
    open_set_hash = {start} 
    
    visited_nodes_count = 0

    while open_set:
        # --- Handle Pause and Quit Events ---
        if paused_ref[0]:
            while paused_ref[0]:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        return False, visited_nodes_count, 0
                    manager.process_events(event)
                draw_func()
                manager.update(0.01)
                manager.draw_ui(window_surface)
                pygame.display.flip()
                pygame.time.wait(50)

        # Pop the node with the smallest g_score
        current_g_score, tie_breaker, current = heapq.heappop(open_set)
        open_set_hash.remove(current)

        # If we already found a shorter path to this node, skip
        if current_g_score > g_score[current]:
            continue

        if current == end:
            path_nodes = reconstruct_path(came_from, end, draw_func)
            end.make_end()
            start.make_start()
            return True, visited_nodes_count, len(path_nodes) + 1

        for neighbor in current.neighbors:
            if neighbor.is_barrier():
                continue

            temp_g_score = g_score[current] + 1 # Cost to move to neighbor is 1

            if temp_g_score < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = temp_g_score
                
                if neighbor not in open_set_hash:
                    count += 1 # Tie-breaker for nodes with same g_score
                    heapq.heappush(open_set, (g_score[neighbor], count, neighbor))
                    open_set_hash.add(neighbor)
                    if neighbor != end:
                        neighbor.make_open()
        
        if current != start and current != end:
            current.make_closed()
            visited_nodes_count += 1

        draw_func()
        pygame.time.delay(delay_ms)

    return False, visited_nodes_count, 0


# --- A* Search Algorithm ---
def astar(draw_func, grid, start, end, delay_ms, paused_ref, manager, window_surface):
    """
    Performs A* Search Algorithm to find the shortest path using a heuristic.

    Args:
        draw_func (function): Function to draw the grid and update the display.
        grid (list[list[Node]]): The 2D grid of nodes.
        start (Node): The starting node.
        end (Node): The target end node.
        delay_ms (int): Delay in milliseconds between node explorations for visualization.
        paused_ref (list): A mutable reference ([boolean]) to control pause state.
        manager (pygame_gui.UIManager): The GUI manager for processing events.
        window_surface (pygame.Surface): The main window surface for drawing GUI elements during pause.

    Returns:
        tuple: (found_path_boolean, visited_nodes_count, path_length)
    """
    count = 0
    # Using heapq directly for better performance than queue.PriorityQueue for this use case
    open_set = [] # Stores (f_score, tie-breaker, node)
    heapq.heappush(open_set, (0, count, start)) 
    
    came_from = {}

    g_score = {node: float("inf") for row in grid for node in row}
    g_score[start] = 0
    f_score = {node: float("inf") for row in grid for node in row}
    # f_score = g_score + h(node, end)
    f_score[start] = h(start.get_pos(), end.get_pos(), method="manhattan")

    # To quickly check if a node is already in the open_set
    open_set_hash = {start} 
    visited_nodes_count = 0

    while open_set: # While heap is not empty
        # --- Handle Pause and Quit Events ---
        if paused_ref[0]:
            while paused_ref[0]:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        return False, visited_nodes_count, 0
                    manager.process_events(event)
                draw_func()
                manager.update(0.01)
                manager.draw_ui(window_surface)
                pygame.display.flip()
                pygame.time.wait(50)

        # Pop the node with the smallest f_score
        current_f_score, tie_breaker, current = heapq.heappop(open_set)
        open_set_hash.remove(current)

        # If we already processed this node with a better (or equal) f_score, skip
        if current_f_score > f_score[current]:
            continue

        if current == end:
            path_nodes = reconstruct_path(came_from, end, draw_func)
            end.make_end()
            start.make_start()
            return True, visited_nodes_count, len(path_nodes) + 1

        for neighbor in current.neighbors:
            if neighbor.is_barrier():
                continue

            temp_g_score = g_score[current] + 1 # Cost to move from current to neighbor is 1

            if temp_g_score < g_score[neighbor]: # Found a shorter path to neighbor
                came_from[neighbor] = current
                g_score[neighbor] = temp_g_score
                f_score[neighbor] = temp_g_score + h(neighbor.get_pos(), end.get_pos(), method="manhattan")

                if neighbor not in open_set_hash:
                    count += 1 # Tie-breaker for nodes with same f_score
                    heapq.heappush(open_set, (f_score[neighbor], count, neighbor))
                    open_set_hash.add(neighbor)
                    if neighbor != end:
                        neighbor.make_open()
        
        if current != start and current != end:
            current.make_closed()
            visited_nodes_count += 1

        draw_func()
        pygame.time.delay(delay_ms)

    return False, visited_nodes_count, 0