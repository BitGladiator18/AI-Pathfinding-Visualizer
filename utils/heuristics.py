import math

def manhattan(p1, p2):
    """Calculates Manhattan distance between two points."""
    x1, y1 = p1
    x2, y2 = p2
    return abs(x1 - x2) + abs(y1 - y2)

def euclidean(p1, p2):
    """Calculates Euclidean distance between two points."""
    x1, y1 = p1
    x2, y2 = p2
    return math.sqrt((x1 - x2)**2 + (y1 - y2)**2)

def diagonal(p1, p2):
    """Calculates Diagonal distance (Chebyshev distance) between two points."""
    x1, y1 = p1
    x2, y2 = p2
    return max(abs(x1 - x2), abs(y1 - y2))

def h(p1, p2, method="manhattan"):
    """
    Generic heuristic function based on the specified method.
    Defaults to Manhattan distance.
    """
    if method == "euclidean":
        return euclidean(p1, p2)
    elif method == "diagonal":
        return diagonal(p1, p2)
    return manhattan(p1, p2)