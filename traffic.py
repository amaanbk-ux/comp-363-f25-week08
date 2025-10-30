
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

def turn_direction(approach_direction: str) -> str:
    """Randomly determine car turning direction (left, straight, right)."""
    rand_val: float = rand()  # Generate pseudo-random number
    left_prob: float = TURN_PROBABILITIES[0]  # Probability to turn left
    straight_prob: float = TURN_PROBABILITIES[1]  # Probability to go straight
    turn: str = STRAIGHT  # Default turn is straight
    if rand_val < left_prob:  # Less than left probability
        turn = LEFT  # Turn left
    else:
        if rand_val < left_prob + straight_prob:  # Less than left+straight
            turn = STRAIGHT  # Go straight
        else:  # Otherwise
            turn = RIGHT  # Turn right
    idx: int = CLOCKWISE.index(approach_direction)  # Get index of approach direction
    if turn == LEFT:  # Left turn is counter-clockwise
        idx = (idx - 1) % 4
    elif turn == RIGHT:  # Right turn is clockwise
        idx = (idx + 1) % 4
    new_dir: str = CLOCKWISE[idx]  # Map index to new direction
    return new_dir  # Return chosen direction

def signal_phase(t: int) -> list[str]:
    """Return green signal directions for tick t."""
    if t % CYCLE_TOTAL < CYCLE_NS_GREEN:  # Check if in NS green phase
        return [NORTH, SOUTH]  # N/S green
    else:  # Otherwise
        return [EAST, WEST]  # E/W green

def add_travel_time() -> int:
    """Return travel time for a link."""
    return BASE_TRAVEL_T  # Currently constant

def is_boundary_incoming_link(src: Node, dst: Node) -> bool:
    """Return True if link src->dst is at grid boundary for arrivals."""
    si: int = src.i  # Source row
    sj: int = src.j  # Source column
    di: int = dst.i  # Destination row
    dj: int = dst.j  # Destination column
    boundary: bool = False  # Initialize
    if si == 0 and di == si + 1 and sj == dj:  # North boundary southbound
        boundary = True
    elif si == N - 1 and di == si - 1 and sj == dj:  # South boundary northbound
        boundary = True
    elif sj == 0 and dj == sj + 1 and si == di:  # West boundary eastbound
        boundary = True
    elif sj == N - 1 and dj == sj - 1 and si == di:  # East boundary westbound
        boundary = True
    return boundary  # Return result

# -------------------- Global state --------------------
nodes: list[Node] = []  # List of all nodes
for i in range(N):  # Loop over rows
    for j in range(N):  # Loop over columns
        nodes.append(Node(i, j))  # Add node

links: list[tuple[Node, Node]] = []  # List of all links
in_transit: dict[tuple[int, int], list[tuple[Car, int]]] = {}  # Cars on links with remaining travel time
stopped: dict[tuple[int, int], list[Car]] = {}  # Cars waiting at stop-line queues

def node_key(node: Node) -> tuple[int, int]:  # Helper to get dict key
    return (node.i, node.j)

for u in nodes:  # Initialize links
    for v, _ in outgoing_for(u):  # For each neighbor
        links.append((u, v))  # Add to links list
        in_transit[(node_key(u), node_key(v))] = []  # Empty in-transit list
        stopped[(node_key(u), node_key(v))] = []  # Empty stop-line queue

completed: int = 0  # Total completed trips
sum_tt: int = 0  # Sum of travel times
car_id: int = 0  # Unique car identifier

# -------------------- Link operations --------------------
def enqueue_departure(src: Node, dst: Node, car: Car) -> bool:
    """Place car on link if capacity allows."""
    buf: list[tuple[Car, int]] = in_transit[(node_key(src), node_key(dst))]  # Cars on link
    success: bool = len(buf) < LINK_IN_TRANSIT_CAP  # Check capacity
    if success:  # If room
        buf.append((car, add_travel_time()))  # Add car with travel time
    return success  # Return whether enqueue succeeded

def pop_to_queue_if_arrived(src: Node, dst: Node) -> int:
    """Advance cars along link; move to stop-line if arrived."""
    buf: list[tuple[Car, int]] = in_transit[(node_key(src), node_key(dst))]  # Cars on link
    for k in range(len(buf)):  # Decrement remaining time
        car, remaining = buf[k]
        buf[k] = (car, remaining - 1)
    moved: int = 0  # Cars moved to stop-line
    q: list[Car] = stopped[(node_key(src), node_key(dst))]  # Stop-line queue
    tmp: list[tuple[Car, int]] = []  # Temporary buffer
    while len(buf) > 0:  # Process all cars
        car, remaining = buf.pop(0)  # Pop first
        if remaining <= 0:  # Arrived
            if len(q) < QUEUE_CAP:  # Space in queue
                q.append(car)  # Add to queue
                moved += 1
            else:  # Queue full
                tmp.insert(0, (car, 0))  # Keep at head for next tick
        else:  # Not yet arrived
            tmp.append((car, remaining))  # Keep in buffer
    in_transit[(node_key(src), node_key(dst))] = tmp  # Update in-transit
    return moved  # Return cars moved

# -------------------- Intersection operations --------------------
def record_completion(car: Car, t_now: int) -> None:
    """Record car exiting the grid."""
    global completed, sum_tt
    completed += 1  # Increment completed trips
    sum_tt += t_now - car.t_enter  # Add travel time

def serve_intersection(t: int, node: Node) -> int:
    """Move cars through green approaches at node."""
    served: int = 0  # Number of cars served
    green_dirs: list[str] = signal_phase(t)  # Directions green
    for u, approach_dir in incoming_for(node):  # Check all incoming links
        if approach_dir in green_dirs:  # If green
            q: list[Car] = stopped[(node_key(u), node_key(node))]  # Get queue
            moves_attempted: int = 0  # Cars moved this tick
            stop_processing: bool = False  # Loop control
            while moves_attempted < FLOW_PER_TICK and not stop_processing and len(q) > 0:  # Process cars
                car: Car = q[0]  # Peek first car
                out_dir: str = turn_direction(approach_dir)  # Determine next move
                i: int = node.i
                j: int = node.j
                next_node: Node = None
                car_exits: bool = False
                if out_dir == NORTH and i > 0:  # Move north
                    next_node = Node(i - 1, j)
                elif out_dir == SOUTH and i < N - 1:  # Move south
                    next_node = Node(i + 1, j)
                elif out_dir == WEST and j > 0:  # Move west
                    next_node = Node(i, j - 1)
                elif out_dir == EAST and j < N - 1:  # Move east
                    next_node = Node(i, j + 1)
                else:  # Exiting grid
                    car_exits = True
                if car_exits:  # Car leaves grid
                    q.pop(0)  # Remove from queue
                    record_completion(car, t)  # Record trip
                    served += 1
                    moves_attempted += 1
                else:  # Try moving to next link
                    success: bool = enqueue_departure(node, next_node, car)
                    if success:  # Move succeeded
                        q.pop(0)  # Remove from queue
                        served += 1
                        moves_attempted += 1
                    else:  # Blocked
                        stop_processing = True  # Stop this approach
    return served  # Return number of cars served

# -------------------- Simulator --------------------
def run_simulation() -> None:
    """Run a single simulation and print metrics."""
    global car_id, completed, sum_tt
    car_id = 0  # Reset car counter
    completed = 0  # Reset completed trips
    sum_tt = 0  # Reset total travel time
    queue_samples: int = 0  # Count of queue samples
    sum_queue: int = 0  # Sum of vehicles in system

    for t in range(TOTAL_TICKS):  # Loop over ticks
        for (src, dst) in links:  # Move cars along all links
            pop_to_queue_if_arrived(src, dst)
        for node in nodes:  # Serve each intersection
            serve_intersection(t, node)
        for (src, dst) in links:  # Spawn boundary arrivals
            if is_boundary_incoming_link(src, dst):
                if rand() < ARRIVAL_RATE:  # Bernoulli arrival
                    car = Car(car_id, t)  # Create car
                    car_id += 1  # Increment ID
                    enqueue_departure(src, dst, car)  # Add to link
        total_queued: int = 0  # Count cars in system
        for val in stopped.values():  # Count stop-line cars
            total_queued += len(val)
        for val in in_transit.values():  # Count in-transit cars
            total_queued += len(val)
        sum_queue += total_queued  # Add to sum
        queue_samples += 1  # Increment sample count

    throughput: float = completed / TOTAL_TICKS  # Cars per tick
    mean_tt: float = sum_tt / completed if completed > 0 else 0  # Average travel time
    mean_queued: float = sum_queue / queue_samples if queue_samples > 0 else 0  # Avg cars in system

    # Print report
    print("Simulation Report (Single Run)")
    print(f"Grid size: {N}x{N}")
    print(f"Duration ticks: {TOTAL_TICKS}")
    print(f"NS green: {CYCLE_NS_GREEN}, EW green: {CYCLE_EW_GREEN}")
    print(f"Arrival rate per boundary link: {ARRIVAL_RATE}")
    print(f"Completed trips: {completed}")
    print(f"Throughput per tick: {throughput}")
    print(f"Mean travel time (ticks): {mean_tt}")
    print(f"Mean vehicles in system (sampled): {mean_queued}")

