"""
Discrete-event Monte-Carlo traffic simulator (self-contained, fully commented).

Simulates a N x N city grid with:
- One lane per direction
- Fixed two-phase traffic signals (N/S and E/W)
- Cars in-transit along links and stopped at stop-lines
- Simple turn behavior (left, straight, right)
"""

# -------------------- Configuration --------------------
N: int = 4  # Number of intersections in each grid dimension (NxN)
TOTAL_TICKS: int = 1000  # Total number of simulation time steps
NORTH: str = "N"  # North direction label
SOUTH: str = "S"  # South direction label
EAST: str = "E"  # East direction label
WEST: str = "W"  # West direction label
CLOCKWISE: list[str] = [NORTH, EAST, SOUTH, WEST]  # Directions in clockwise order

STRAIGHT: str = "straight"  # Constant for going straight
LEFT: str = "left"  # Constant for turning left
RIGHT: str = "right"  # Constant for turning right

TURN_PROBABILITIES: list[float] = [0.25, 0.50, 0.25]  # Probabilities [left, straight, right]

CYCLE_NS_GREEN: int = 20  # Number of ticks N/S signal stays green
CYCLE_EW_GREEN: int = 20  # Number of ticks E/W signal stays green
CYCLE_TOTAL: int = CYCLE_NS_GREEN + CYCLE_EW_GREEN  # Total signal cycle length

FLOW_PER_TICK: int = 1  # Cars allowed to move per green light per tick
LINK_IN_TRANSIT_CAP: int = 50  # Max cars allowed on a link
QUEUE_CAP: int = 10  # Max cars allowed in queue at stop-line
BASE_TRAVEL_T: int = 6  # Base travel time on a link (ticks)
ARRIVAL_RATE: float = 0.33  # Probability a new car arrives per tick at boundary

# -------------------- Classes --------------------
class Node:
    """Represents an intersection in the grid."""
    def __init__(self, i: int, j: int) -> None:  # Constructor with grid indices
        self.i: int = i  # E-W index (row)
        self.j: int = j  # N-S index (column)

class Car:
    """Represents a car in the simulation."""
    def __init__(self, car_id: int, t_enter: int) -> None:  # Constructor with ID and entry tick
        self.id: int = car_id  # Unique car identifier
        self.t_enter: int = t_enter  # Tick when car entered the grid

# -------------------- Pseudo-random generator --------------------
seed_value: int = 42  # Seed for deterministic pseudo-random generator
def rand() -> float:  # Return a pseudo-random float between 0 and 1
    global seed_value  # Use the global seed
    seed_value = (1664525 * seed_value + 1013904223) % 4294967296  # Linear congruential generator
    return seed_value / 4294967296  # Normalize to [0,1)

# -------------------- Helper functions --------------------
def outgoing_for(node: Node) -> list[tuple[Node, str]]:
    """Return list of outgoing neighbor nodes and their directions."""
    directions: list[tuple[Node, str]] = []  # Initialize empty list
    i: int = node.i  # Current node row
    j: int = node.j  # Current node column
    if i > 0:  # If not on north boundary
        directions.append((Node(i - 1, j), NORTH))  # Add north neighbor
    if j < N - 1:  # If not on east boundary
        directions.append((Node(i, j + 1), EAST))  # Add east neighbor
    if i < N - 1:  # If not on south boundary
        directions.append((Node(i + 1, j), SOUTH))  # Add south neighbor
    if j > 0:  # If not on west boundary
        directions.append((Node(i, j - 1), WEST))  # Add west neighbor
    return directions  # Return list of outgoing neighbors

def incoming_for(node: Node) -> list[tuple[Node, str]]:
    """Return list of incoming neighbor nodes and approach directions."""
    directions: list[tuple[Node, str]] = []  # Initialize list
    i: int = node.i  # Current node row
    j: int = node.j  # Current node column
    if i < N - 1:  # If not on south boundary
        directions.append((Node(i + 1, j), NORTH))  # South neighbor approaches north
    if j > 0:  # If not on west boundary
        directions.append((Node(i, j - 1), EAST))  # West neighbor approaches east
    if i > 0:  # If not on north boundary
        directions.append((Node(i - 1, j), SOUTH))  # North neighbor approaches south
    if j < N - 1:  # If not on east boundary
        directions.append((Node(i, j + 1), WEST))  # East neighbor approaches west
    return directions  # Return incoming neighbors

de
