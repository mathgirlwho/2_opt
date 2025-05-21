import argparse
import random
import math
import copy

# ----------- VRP File Parser -----------
def parse_vrp(vrp_path):
    coords = {}
    demands = {}
    depot = None

    with open(vrp_path, 'r') as file:
        lines = file.readlines()

    node_section = False
    demand_section = False
    depot_section = False

    for line in lines:
        line = line.strip()
        if line.startswith("NODE_COORD_SECTION"):
            node_section = True
            demand_section = depot_section = False
            continue
        elif line.startswith("DEMAND_SECTION"):
            demand_section = True
            node_section = depot_section = False
            continue
        elif line.startswith("DEPOT_SECTION"):
            depot_section = True
            node_section = demand_section = False
            continue
        elif line.startswith("EOF"):
            break

        if node_section:
            parts = line.split()
            if len(parts) >= 3:
                idx = int(parts[0])
                x = float(parts[1])
                y = float(parts[2])
                coords[idx] = (x, y)
        elif demand_section:
            parts = line.split()
            if len(parts) >= 2:
                idx = int(parts[0])
                demand = int(parts[1])
                demands[idx] = demand
        elif depot_section:
            if line == "-1":
                depot_section = False
            else:
                depot = int(line)

    if depot is None:
        depot = 1

    return {
        "coords": coords,
        "demands": demands,
        "depot": depot
    }

# ----------- TOUR File Parser -----------
def parse_tour(tour_path):
    routes = []
    with open(tour_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith("Route"):
                parts = line.split(":")
                if len(parts) > 1:
                    nodes_str = parts[1].strip()
                    if nodes_str:
                        route_nodes = [1] + list(map(int, nodes_str.split())) + [1]
                        routes.append(route_nodes)
    return routes

# ----------- Distance Calculation -----------
def compute_distance(coords, i, j):
    xi, yi = coords[i]
    xj, yj = coords[j]
    return math.hypot(xi - xj, yi - yj)

# ----------- Local Perturbation (Shaking) -----------
def find_nearby_pairs(route, coords, radius=10):
    pairs = []
    nodes = route[1:-1]
    for i in range(len(nodes)):
        for j in range(i+1, len(nodes)):
            if compute_distance(coords, nodes[i], nodes[j]) <= radius:
                pairs.append((nodes[i], nodes[j]))
    return pairs

def random_exchange(routes, coords, m, radius=10):
    all_routes = routes[:]
    n = len(all_routes)

    if n < 2:
        print("Need at least two routes to perform exchanges.")
        return all_routes

    exchanges_done = 0
    attempts = 0
    max_attempts = m * 10

    while exchanges_done < m and attempts < max_attempts:
        attempts += 1
        r1_idx, r2_idx = random.sample(range(n), 2)
        r1 = all_routes[r1_idx]
        r2 = all_routes[r2_idx]

        pairs_r1 = find_nearby_pairs(r1, coords, radius)
        pairs_r2 = find_nearby_pairs(r2, coords, radius)

        if not pairs_r1 or not pairs_r2:
            continue

        pair1 = random.choice(pairs_r1)
        pair2 = random.choice(pairs_r2)

        def swap_pairs(route, old_pair, new_pair):
            new_route = route[:]
            for old_node in old_pair:
                if old_node in new_route:
                    new_route.remove(old_node)
            insert_pos = 1
            for node in new_pair:
                new_route.insert(insert_pos, node)
                insert_pos += 1
            return new_route

        new_r1 = swap_pairs(r1, pair1, pair2)
        new_r2 = swap_pairs(r2, pair2, pair1)

        all_routes[r1_idx] = new_r1
        all_routes[r2_idx] = new_r2
        exchanges_done += 1

    if attempts >= max_attempts:
        print("Reached max attempts during perturbation.")

    return all_routes

# ----------- Total Cost Calculation -----------
def compute_total_cost(vrp_data, routes):
    coords = vrp_data["coords"]
    total_cost = 0
    for route in routes:
        for i in range(len(route)-1):
            total_cost += compute_distance(coords, route[i], route[i+1])
    return total_cost

# ----------- Save Output Tour -----------
def save_tour(routes, path, total_cost):
    with open(path, 'w') as f:
        f.write(f"# Total Cost: {total_cost:.4f}\n")
        for idx, route in enumerate(routes, 1):
            route_nodes = route[1:-1]
            f.write(f"Route {idx}: {' '.join(map(str, route_nodes))}\n")

# ----------- REDUCED VNS Main Loop -----------
def reduced_vns(routes, vrp_data, m, radius, max_iterations=100):
    best_routes = copy.deepcopy(routes)
    best_cost = compute_total_cost(vrp_data, best_routes)
    coords = vrp_data["coords"]

    for i in range(max_iterations):
        shaken_routes = random_exchange(best_routes, coords, m, radius=radius)
        shaken_cost = compute_total_cost(vrp_data, shaken_routes)

        if shaken_cost < best_cost:
            best_cost = shaken_cost
            best_routes = shaken_routes
            print(f"Iteration {i}: Improved cost = {best_cost:.2f}")

    return best_routes, best_cost

# ----------- MAIN FUNCTION -----------
def main():
    parser = argparse.ArgumentParser(description="Reduced VNS for VRP using perturbation as shaking")
    parser.add_argument('--vrp', required=True, type=str, help='Input .vrp file path')
    parser.add_argument('--tour', required=True, type=str, help='Initial .tour solution file')
    parser.add_argument('-m', type=int, default=2, help='Number of node-pair exchanges (shaking strength)')
    parser.add_argument('--radius', type=float, default=10, help='Max distance to consider nodes as "nearby" for exchange')
    parser.add_argument('--output', default='vns_solution.tour', type=str, help='Output file path for final tour')
    args = parser.parse_args()

    vrp_data = parse_vrp(args.vrp)
    initial_routes = parse_tour(args.tour)

    improved_routes, final_cost = reduced_vns(
        routes=initial_routes,
        vrp_data=vrp_data,
        m=args.m,
        radius=args.radius,
        max_iterations=100
    )

    save_tour(improved_routes, args.output, final_cost)
    print(f"✅ Final Cost: {final_cost:.2f}")
    print(f"✅ Output saved to: {args.output}")

if __name__ == "__main__":
    main()
