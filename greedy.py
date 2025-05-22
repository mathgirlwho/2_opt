import argparse
import math
import os

def parse_vrp(vrp_path):
    with open(vrp_path, 'r') as file:
        lines = file.readlines()

    coords = {}
    demands = {}
    depot = None
    dimension = 0
    capacity = 0

    node_section = False
    demand_section = False
    depot_section = False

    for line in lines:
        line = line.strip()
        if line.startswith("DIMENSION"):
            dimension = int(line.split(":")[1].strip())
        elif line.startswith("CAPACITY"):
            capacity = int(line.split(":")[1].strip())
        elif line.startswith("NODE_COORD_SECTION"):
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
        depot = 1  # Default depot

    return {
        "dimension": dimension,
        "capacity": capacity,
        "node_coords": coords,
        "demands": demands,
        "depot": depot
    }

def compute_distance_matrix(coords):
    nodes = sorted(coords.keys())
    dist_matrix = {}
    for i in nodes:
        dist_matrix[i] = {}
        xi, yi = coords[i]
        for j in nodes:
            if i == j:
                dist_matrix[i][j] = 0.0
            else:
                xj, yj = coords[j]
                dist_matrix[i][j] = math.hypot(xi - xj, yi - yj)
    return dist_matrix

def route_cost(route, dist_matrix):
    return sum(dist_matrix[route[i]][route[i+1]] for i in range(len(route) - 1))

def compute_total_cost(vrp_data, routes):
    dist_matrix = compute_distance_matrix(vrp_data["node_coords"])
    total_cost = 0.0
    for route in routes:
        total_cost += route_cost(route, dist_matrix)
    return total_cost, dist_matrix

def greedy_init(vrp_data):
    coords = vrp_data["node_coords"]
    demands = vrp_data["demands"]
    capacity = vrp_data["capacity"]
    depot = vrp_data["depot"]
    dist_matrix = compute_distance_matrix(coords)

    unvisited = set(coords.keys()) - {depot}
    routes = []

    while unvisited:
        route = [depot]
        load = 0
        current = depot

        candidates = sorted(unvisited, key=lambda x: demands.get(x, 0), reverse=True)
        for node in candidates:
            if node in unvisited and load + demands[node] <= capacity:
                route.append(node)
                load += demands[node]
                unvisited.remove(node)
        route.append(depot)
        routes.append(route)

    return routes

def parse_initial_tour(tour_path, depot):
    routes = []
    with open(tour_path, 'r') as f:
        for line in f:
            if line.lower().startswith("route"):
                parts = line.strip().split()[1:]
                route = [depot] + list(map(int, parts)) + [depot]
                routes.append(route)
    return routes

def save_tour(routes, path, total_cost):
    with open(path, 'w') as f:
        for idx, route in enumerate(routes, 1):
            route_nodes = route[1:-1]
            f.write(f"Route {idx}: {' '.join(map(str, route_nodes))}\n")
        f.write(f"Optimal cost: {total_cost:.2f}\n")

def main():
    parser = argparse.ArgumentParser(description="Greedy VRP Solver")
    parser.add_argument('--vrp', type=str, help='Input .vrp file path')
    parser.add_argument('--par', type=str, help='Parameter file path')
    parser.add_argument('--save_tour', type=str, default='greedy_solution.tour', help='Path to save output tour')
    args = parser.parse_args()

    if args.par:
        with open(args.par, 'r') as f:
            for line in f:
                if "PROBLEM_FILE" in line:
                    args.vrp = line.split("=")[1].strip()
                elif "INITIAL_SOLUTION" in line:
                    init_sol_path = line.split("=")[1].strip()

    vrp_data = parse_vrp(args.vrp)

    if 'init_sol_path' in locals() and os.path.exists(init_sol_path):
        print("Using initial solution from .tour file")
        routes = parse_initial_tour(init_sol_path, vrp_data["depot"])
    else:
        print("Generating greedy initial solution")
        routes = greedy_init(vrp_data)

    total_cost, _ = compute_total_cost(vrp_data, routes)
    save_tour(routes, args.save_tour, total_cost)
    print(f"Total cost: {total_cost:.2f}")
    print(f"Saved solution to {args.save_tour}")

if __name__ == "__main__":
    main()
