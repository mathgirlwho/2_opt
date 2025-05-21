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

# ----------- Basic VNS -----------
def basic_vns(vrp_data, k_max=1, max_iter=50, radius=10):
    coords = vrp_data["node_coords"]
    best_routes = nearest_neighbor_init(vrp_data)
    best_cost = compute_total_cost(vrp_data, best_routes)

    for it in range(max_iter):
        k = 1
        while k <= k_max:
            shaken = random_exchange(best_routes, coords, m=k, radius=radius)
            local_opt = two_opt_vrp(vrp_data, shaken)
            local_cost = compute_total_cost(vrp_data, local_opt)

            if local_cost < best_cost:
                best_routes = local_opt
                best_cost = local_cost
                k = 1  # restart neighborhood
            else:
                k += 1

    return best_routes, best_cost

# ----------- Save Tour -----------
def save_tour(routes, path, total_cost):
    with open(path, 'w') as f:
        for i, route in enumerate(routes):
            f.write(f"Route {i+1}: {' '.join(map(str, route[1:-1]))}\n")
        f.write(f"Total cost: {total_cost:.2f}\n")

# ----------- Main -----------
def main():
    parser = argparse.ArgumentParser(description="Basic VNS for VRP")
    parser.add_argument('--vrp', type=str, required=True, help='Path to .vrp file')
    parser.add_argument('--save_tour', type=str, default='vns_solution.tour', help='Output tour file')
    parser.add_argument('--max_iter', type=int, default=50, help='Max iterations for VNS')
    parser.add_argument('--k_max', type=int, default=1, help='Max neighborhood size k')
    parser.add_argument('--radius', type=float, default=10, help='Radius for pairwise perturbation')
    args = parser.parse_args()

    print("📦 Loading VRP...")
    vrp_data = parse_vrp(args.vrp)

    print("🚀 Starting Basic VNS...")
    best_routes, best_cost = basic_vns(vrp_data, k_max=args.k_max, max_iter=args.max_iter, radius=args.radius)

    print(f"✅ Final cost: {best_cost:.2f}")
    save_tour(best_routes, args.save_tour, best_cost)
    print(f"📄 Tour saved to {args.save_tour}")

if __name__ == "__main__":
    main()
