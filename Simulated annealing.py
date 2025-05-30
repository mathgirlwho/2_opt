import argparse
import math
import random
import copy

# ----------- VRP Parsing Utilities -----------
def parse_vrp(vrp_path):
    with open(vrp_path, 'r') as file:
        lines = file.readlines()

    coords = {}
    demands = {}
    depot = None
    dimension = 0
    capacity = 0

    node_section = demand_section = depot_section = False

    for line in lines:
        line = line.strip()
        if line.startswith("DIMENSION"):
            dimension = int(line.split(":")[1].strip())
        elif line.startswith("CAPACITY"):
            capacity = int(line.split(":")[1].strip())
        elif line.startswith("NODE_COORD_SECTION"):
            node_section, demand_section, depot_section = True, False, False
            continue
        elif line.startswith("DEMAND_SECTION"):
            demand_section, node_section, depot_section = True, False, False
            continue
        elif line.startswith("DEPOT_SECTION"):
            depot_section, node_section, demand_section = True, False, False
            continue
        elif line.startswith("EOF"):
            break

        if node_section:
            idx, x, y = map(float, line.split())
            coords[int(idx)] = (x, y)
        elif demand_section:
            idx, demand = map(int, line.split())
            demands[idx] = demand
        elif depot_section and line != "-1":
            depot = int(line)

    return {
        "dimension": dimension,
        "capacity": capacity,
        "node_coords": coords,
        "demands": demands,
        "depot": depot or 1
    }

# ----------- Distance and Cost Utilities -----------
def compute_distance(coords, a, b):
    xa, ya = coords[a]
    xb, yb = coords[b]
    return math.hypot(xa - xb, ya - yb)

def route_cost(route, coords):
    return sum(compute_distance(coords, route[i], route[i+1]) for i in range(len(route)-1))

def compute_total_cost(vrp_data, routes):
    coords = vrp_data["node_coords"]
    return sum(route_cost(r, coords) for r in routes)

# ----------- Initial Solution (Nearest Neighbor) -----------
def nearest_neighbor_init(vrp_data):
    coords, demands = vrp_data["node_coords"], vrp_data["demands"]
    capacity, depot = vrp_data["capacity"], vrp_data["depot"]

    visited = {node: False for node in coords}
    visited[depot] = True

    dist = lambda a, b: compute_distance(coords, a, b)

    routes = []
    while not all(visited.values()):
        route, load, current = [depot], 0, depot
        while True:
            candidates = [node for node in coords if not visited[node] and load + demands.get(node, 0) <= capacity]
            if not candidates:
                break
            next_node = min(candidates, key=lambda j: dist(current, j))
            route.append(next_node)
            visited[next_node] = True
            load += demands.get(next_node, 0)
            current = next_node
        route.append(depot)
        routes.append(route)
    return routes

# ----------- Local Search (2-Opt) -----------
def two_opt_route(route, coords):
    best = route[:]
    improved = True
    while improved:
        improved = False
        for i in range(1, len(best)-2):
            for j in range(i+1, len(best)-1):
                if j - i == 1:
                    continue
                new = best[:i] + best[i:j][::-1] + best[j:]
                if route_cost(new, coords) < route_cost(best, coords):
                    best = new
                    improved = True
    return best

def two_opt_vrp(vrp_data, routes):
    coords = vrp_data["node_coords"]
    return [two_opt_route(r, coords) for r in routes]

# ----------- Perturbation (Shaking) -----------
def find_nearby_pairs(route, coords, radius=10):
    pairs = []
    nodes = route[1:-1]
    for i in range(len(nodes)):
        for j in range(i+1, len(nodes)):
            if compute_distance(coords, nodes[i], nodes[j]) <= radius:
                pairs.append((nodes[i], nodes[j]))
    return pairs

def random_exchange(routes, coords, m, radius=10):
    all_routes = copy.deepcopy(routes)
    n = len(all_routes)
    if n < 2:
        return all_routes

    exchanges_done = 0
    attempts = 0
    max_attempts = m * 10

    while exchanges_done < m and attempts < max_attempts:
        attempts += 1
        r1_idx, r2_idx = random.sample(range(n), 2)
        r1, r2 = all_routes[r1_idx], all_routes[r2_idx]

        pairs_r1 = find_nearby_pairs(r1, coords, radius)
        pairs_r2 = find_nearby_pairs(r2, coords, radius)

        if not pairs_r1 or not pairs_r2:
            continue

        p1 = random.choice(pairs_r1)
        p2 = random.choice(pairs_r2)

        def swap(route, old, new):
            route = [x for x in route if x not in old]
            return [route[0]] + list(new) + route[1:]

        all_routes[r1_idx] = swap(r1, p1, p2)
        all_routes[r2_idx] = swap(r2, p2, p1)
        exchanges_done += 1

    return all_routes

# ----------- Simulated Annealing -----------
def simulated_annealing(vrp_data, initial_temp=100, cooling_rate=0.95, min_temp=0.01, max_iter=100, radius=10):
    coords = vrp_data["node_coords"]
    
    # Step 1: Initial solution
    current_routes = nearest_neighbor_init(vrp_data)
    current_cost = compute_total_cost(vrp_data, current_routes)
    best_routes = copy.deepcopy(current_routes)
    best_cost = current_cost
    
    temperature = initial_temp
    iteration = 0
    
    print(f"Initial solution cost: {current_cost:.2f}")
    
    # Main SA loop
    while temperature > min_temp and iteration < max_iter:
        iteration += 1
        
        # Step 2: Generate neighbor solution
        neighbor_routes = random_exchange(current_routes, coords, m=1, radius=radius)
        
        # Step 3: Local Search (optional in pure SA, but can improve results)
        neighbor_routes = two_opt_vrp(vrp_data, neighbor_routes)
        neighbor_cost = compute_total_cost(vrp_data, neighbor_routes)
        
        # Step 4: Decide whether to accept the new solution
        delta = neighbor_cost - current_cost
        
        # Accept if better, or with probability e^(-delta/T) if worse
        if delta < 0 or random.random() < math.exp(-delta / temperature):
            current_routes = copy.deepcopy(neighbor_routes)
            current_cost = neighbor_cost
            
            # Update best solution if needed
            if current_cost < best_cost:
                best_routes = copy.deepcopy(current_routes)
                best_cost = current_cost
                print(f"Iteration {iteration}: New best cost = {best_cost:.2f}, T = {temperature:.2f}")
        
        # Step 5: Cool down temperature
        temperature *= cooling_rate
        
        # Optional: Print progress every few iterations
        if iteration % 10 == 0:
            print(f"Iteration {iteration}: Current cost = {current_cost:.2f}, Best = {best_cost:.2f}, T = {temperature:.2f}")
    
    print(f"SA completed after {iteration} iterations")
    print(f"Final temperature: {temperature:.6f}")
    return best_routes, best_cost

# ----------- Save Tour -----------
def save_tour(routes, path, total_cost):
    with open(path, 'w') as f:
        for i, route in enumerate(routes):
            f.write(f"Route {i+1}: {' '.join(map(str, route[1:-1]))}\n")
        f.write(f"Total cost: {total_cost:.2f}\n")

# ----------- Main -----------
def main():
    parser = argparse.ArgumentParser(description="Simulated Annealing for VRP")
    parser.add_argument('--vrp', type=str, required=True, help='Path to .vrp file')
    parser.add_argument('--save_tour', type=str, default='sa_solution.tour', help='Output tour file')
    parser.add_argument('--initial_temp', type=float, default=100.0, help='Initial temperature')
    parser.add_argument('--cooling_rate', type=float, default=0.95, help='Cooling rate')
    parser.add_argument('--min_temp', type=float, default=0.01, help='Minimum temperature')
    parser.add_argument('--max_iter', type=int, default=100, help='Maximum iterations')
    parser.add_argument('--radius', type=float, default=10, help='Radius for pairwise perturbation')
    args = parser.parse_args()

    print(" Loading VRP...")
    vrp_data = parse_vrp(args.vrp)

    print(" Starting Simulated Annealing...")
    best_routes, best_cost = simulated_annealing(
        vrp_data, 
        initial_temp=args.initial_temp,
        cooling_rate=args.cooling_rate,
        min_temp=args.min_temp,
        max_iter=args.max_iter,
        radius=args.radius
    )

    print(f" Final cost: {best_cost:.2f}")
    save_tour(best_routes, args.save_tour, best_cost)
    print(f" Tour saved to {args.save_tour}")

if __name__ == "__main__":
    main()
