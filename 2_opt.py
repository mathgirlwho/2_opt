# import argparse
# import math
# import matplotlib.pyplot as plt
# import numpy as np

# def parse_vrp(vrp_path):
#     with open(vrp_path, 'r') as file:
#         lines = file.readlines()

#     coords = {}
#     demands = {}
#     depot = None
#     dimension = 0
#     capacity = 0

#     node_section = False
#     demand_section = False
#     depot_section = False

#     for line in lines:
#         line = line.strip()
#         if line.startswith("DIMENSION"):
#             dimension = int(line.split(":")[1].strip())
#         elif line.startswith("CAPACITY"):
#             capacity = int(line.split(":")[1].strip())
#         elif line.startswith("NODE_COORD_SECTION"):
#             node_section = True
#             demand_section = depot_section = False
#             continue
#         elif line.startswith("DEMAND_SECTION"):
#             demand_section = True
#             node_section = depot_section = False
#             continue
#         elif line.startswith("DEPOT_SECTION"):
#             depot_section = True
#             node_section = demand_section = False
#             continue
#         elif line.startswith("EOF"):
#             break

#         if node_section:
#             parts = line.split()
#             if len(parts) >= 3:
#                 idx = int(parts[0])
#                 x = float(parts[1])
#                 y = float(parts[2])
#                 coords[idx] = (x, y)
#         elif demand_section:
#             parts = line.split()
#             if len(parts) >= 2:
#                 idx = int(parts[0])
#                 demand = int(parts[1])
#                 demands[idx] = demand
#         elif depot_section:
#             if line == "-1":
#                 depot_section = False
#             else:
#                 depot = int(line)

#     if depot is None:
#         depot = 1  # Default depot

#     return {
#         "dimension": dimension,
#         "capacity": capacity,
#         "node_coords": coords,
#         "demands": demands,
#         "depot": depot
#     }

# def compute_distance_matrix(coords):
#     nodes = sorted(coords.keys())
#     dist_matrix = {}
#     for i in nodes:
#         dist_matrix[i] = {}
#         xi, yi = coords[i]
#         for j in nodes:
#             if i == j:
#                 dist_matrix[i][j] = 0.0
#             else:
#                 xj, yj = coords[j]
#                 dist_matrix[i][j] = math.hypot(xi - xj, yi - yj)
#     return dist_matrix

# def nearest_neighbor_init(vrp_data):
#     coords = vrp_data["node_coords"]
#     demands = vrp_data["demands"]
#     capacity = vrp_data["capacity"]
#     depot = vrp_data["depot"]
#     num_customers = len(coords)

#     visited = {node: False for node in coords}
#     visited[depot] = True

#     dist_matrix = compute_distance_matrix(coords)

#     routes = []
#     while not all(visited.values()):
#         route = [depot]
#         load = 0
#         current = depot

#         while True:
#             candidates = [node for node in coords if not visited[node] and load + demands.get(node, 0) <= capacity]
#             if not candidates:
#                 break

#             next_node = min(candidates, key=lambda j: dist_matrix[current][j])
#             route.append(next_node)
#             visited[next_node] = True
#             load += demands.get(next_node, 0)
#             current = next_node

#         route.append(depot)
#         routes.append(route)
#     return routes

# def route_cost(route, dist_matrix):
#     cost = 0.0
#     for i in range(len(route) - 1):
#         cost += dist_matrix[route[i]][route[i+1]]
#     return cost

# def compute_total_cost(vrp_data, routes):
#     dist_matrix = compute_distance_matrix(vrp_data["node_coords"])
#     total_cost = 0.0
#     for route in routes:
#         total_cost += route_cost(route, dist_matrix)
#     return total_cost, dist_matrix

# def two_opt_route(route, dist_matrix):
#     best = route[:]
#     improved = True
#     while improved:
#         improved = False
#         for i in range(1, len(best) - 2):
#             for j in range(i + 1, len(best) -1):
#                 if j - i == 1:  # consecutive nodes, no improvement
#                     continue
#                 new_route = best[:i] + best[i:j][::-1] + best[j:]
#                 if route_cost(new_route, dist_matrix) < route_cost(best, dist_matrix):
#                     best = new_route
#                     improved = True
#         route = best
#     return best

# def two_opt_vrp(vrp_data, routes, max_iterations=100):
#     dist_matrix = compute_distance_matrix(vrp_data["node_coords"])
#     improved_routes = routes[:]
#     for iteration in range(max_iterations):
#         improvement_made = False
#         for idx, route in enumerate(improved_routes):
#             new_route = two_opt_route(route, dist_matrix)
#             if route_cost(new_route, dist_matrix) < route_cost(improved_routes[idx], dist_matrix):
#                 improved_routes[idx] = new_route
#                 improvement_made = True
#         if not improvement_made:
#             break
#     final_cost = sum(route_cost(r, dist_matrix) for r in improved_routes)
#     return improved_routes, final_cost

# def save_tour(routes, path, total_cost):
#     with open(path, 'w') as f:
#         for idx, route in enumerate(routes, 1):
#             # Remove depot at start/end for cleaner display
#             route_nodes = route[1:-1]
#             f.write(f"Route {idx}: {' '.join(map(str, route_nodes))}\n")
#         f.write(f"Optimal cost: {total_cost:.2f}\n")


# import os





# def main():
#     parser = argparse.ArgumentParser(description="2-opt VRP Solver")
#     parser.add_argument('--vrp', type=str, required=True, help='Input .vrp file path')
#     parser.add_argument('--par', type=str, help='Optional .par file with parameters')
#     parser.add_argument('--save_tour', type=str, default='solution.tour', help='Path to save tour')
#     parser.add_argument('--plot', type=str, default='routes.png', help='Path to save plot')
#     args = parser.parse_args()

#     print("📦 Parsing .vrp file...")
#     vrp_data = parse_vrp(args.vrp)

#     # Parameters defaults
#     max_iter = 100
#     init_strategy = "nearest"

#     if args.par:
#         print("⚙️ Loading parameters from .par file...")
#         with open(args.par, 'r') as f:
#             for line in f:
#                 line = line.strip()
#                 if "=" in line:
#                     key, val = line.split("=")
#                     key = key.strip().upper()
#                     val = val.strip()
#                     if key == "MAX_ITERATIONS":
#                         max_iter = int(val)
#                     elif key == "INIT_STRATEGY":
#                         init_strategy = val.lower()

#     print(f"🧠 Generating initial solution using strategy: {init_strategy}")
#     if init_strategy == "nearest":
#         routes = nearest_neighbor_init(vrp_data)
#     else:
#         raise ValueError(f"Unknown INIT_STRATEGY: {init_strategy}")

#     init_cost, _ = compute_total_cost(vrp_data, routes)
#     print(f"➡ Initial cost: {init_cost:.2f}")

#     print(f"🚀 Running 2-opt for max {max_iter} iterations...")
#     improved_routes, final_cost = two_opt_vrp(vrp_data, routes, max_iterations=max_iter)
#     print(f"✅ Final cost: {final_cost:.2f}")

#     save_tour(improved_routes, args.save_tour, final_cost)
#     print(f"📄 Saved improved tour to: {args.save_tour}")

#     plot_routes(vrp_data, improved_routes, args.plot)
#     print(f"🖼️  Saved route plot to: {args.plot}")

# if __name__ == "__main__":
#     main()




import argparse
import math

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

def nearest_neighbor_init(vrp_data):
    coords = vrp_data["node_coords"]
    demands = vrp_data["demands"]
    capacity = vrp_data["capacity"]
    depot = vrp_data["depot"]

    visited = {node: False for node in coords}
    visited[depot] = True

    dist_matrix = compute_distance_matrix(coords)

    routes = []
    while not all(visited.values()):
        route = [depot]
        load = 0
        current = depot

        while True:
            candidates = [node for node in coords if not visited[node] and load + demands.get(node, 0) <= capacity]
            if not candidates:
                break

            next_node = min(candidates, key=lambda j: dist_matrix[current][j])
            route.append(next_node)
            visited[next_node] = True
            load += demands.get(next_node, 0)
            current = next_node

        route.append(depot)
        routes.append(route)
    return routes

def route_cost(route, dist_matrix):
    cost = 0.0
    for i in range(len(route) - 1):
        cost += dist_matrix[route[i]][route[i+1]]
    return cost

def compute_total_cost(vrp_data, routes):
    dist_matrix = compute_distance_matrix(vrp_data["node_coords"])
    total_cost = 0.0
    for route in routes:
        total_cost += route_cost(route, dist_matrix)
    return total_cost, dist_matrix

def two_opt_route(route, dist_matrix):
    best = route[:]
    improved = True
    while improved:
        improved = False
        for i in range(1, len(best) - 2):
            for j in range(i + 1, len(best) -1):
                if j - i == 1:
                    continue
                new_route = best[:i] + best[i:j][::-1] + best[j:]
                if route_cost(new_route, dist_matrix) < route_cost(best, dist_matrix):
                    best = new_route
                    improved = True
        route = best
    return best

def two_opt_vrp(vrp_data, routes, max_iterations=100):
    dist_matrix = compute_distance_matrix(vrp_data["node_coords"])
    improved_routes = routes[:]
    for iteration in range(max_iterations):
        improvement_made = False
        for idx, route in enumerate(improved_routes):
            new_route = two_opt_route(route, dist_matrix)
            if route_cost(new_route, dist_matrix) < route_cost(improved_routes[idx], dist_matrix):
                improved_routes[idx] = new_route
                improvement_made = True
        if not improvement_made:
            break
    final_cost = sum(route_cost(r, dist_matrix) for r in improved_routes)
    return improved_routes, final_cost

def save_tour(routes, path, total_cost):
    with open(path, 'w') as f:
        for idx, route in enumerate(routes, 1):
            # Remove depot at start/end for cleaner display
            route_nodes = route[1:-1]
            f.write(f"Route {idx}: {' '.join(map(str, route_nodes))}\n")
        f.write(f"Optimal cost: {total_cost:.2f}\n")

def main():
    parser = argparse.ArgumentParser(description="2-opt VRP Solver")
    parser.add_argument('--vrp', type=str, required=True, help='Input .vrp file path')
    parser.add_argument('--par', type=str, help='Optional .par file with parameters')
    parser.add_argument('--save_tour', type=str, default='solution.tour', help='Path to save tour')
    parser.add_argument('--plot', type=str, default='routes.png', help='Path to save plot (ignored here)')
    args = parser.parse_args()

    print(" Parsing .vrp file...")
    vrp_data = parse_vrp(args.vrp)

    max_iter = 100
    init_strategy = "nearest"

    if args.par:
        print(" Loading parameters from .par file...")
        with open(args.par, 'r') as f:
            for line in f:
                line = line.strip()
                if "=" in line:
                    key, val = line.split("=")
                    key = key.strip().upper()
                    val = val.strip()
                    if key == "MAX_ITERATIONS":
                        max_iter = int(val)
                    elif key == "INIT_STRATEGY":
                        init_strategy = val.lower()

    print(f" Generating initial solution using strategy: {init_strategy}")
    if init_strategy == "nearest":
        routes = nearest_neighbor_init(vrp_data)
    else:
        raise ValueError(f"Unknown INIT_STRATEGY: {init_strategy}")

    init_cost, _ = compute_total_cost(vrp_data, routes)
    print(f"➡ Initial cost: {init_cost:.2f}")

    print(f" Running 2-opt for max {max_iter} iterations...")
    improved_routes, final_cost = two_opt_vrp(vrp_data, routes, max_iterations=max_iter)
    print(f" Final cost: {final_cost:.2f}")

    save_tour(improved_routes, args.save_tour, final_cost)
    print(f" Saved improved tour to: {args.save_tour}")

if __name__ == "__main__":
    main()
