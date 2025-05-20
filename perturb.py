# import argparse
# import random
# import math

# def parse_vrp(vrp_path):
#     coords = {}
#     demands = {}
#     depot = None

#     with open(vrp_path, 'r') as file:
#         lines = file.readlines()

#     node_section = False
#     demand_section = False
#     depot_section = False

#     for line in lines:
#         line = line.strip()
#         if line.startswith("NODE_COORD_SECTION"):
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
#         "coords": coords,
#         "demands": demands,
#         "depot": depot
#     }

# def parse_tour(tour_path):
#     routes = []
#     with open(tour_path, 'r') as f:
#         for line in f:
#             line = line.strip()
#             if line.startswith("Route"):
#                 parts = line.split(":")
#                 if len(parts) > 1:
#                     nodes_str = parts[1].strip()
#                     if nodes_str:
#                         # We add depot at start/end as per your convention
#                         route_nodes = [1] + list(map(int, nodes_str.split())) + [1]
#                         routes.append(route_nodes)
#     return routes

# def compute_distance(coords, i, j):
#     xi, yi = coords[i]
#     xj, yj = coords[j]
#     return math.hypot(xi - xj, yi - yj)

# def find_nearby_pairs(route, coords, radius=10):
#     # Find pairs of nodes in the same route within radius distance
#     pairs = []
#     nodes = route[1:-1]  # exclude depot
#     for i in range(len(nodes)):
#         for j in range(i+1, len(nodes)):
#             if compute_distance(coords, nodes[i], nodes[j]) <= radius:
#                 pairs.append((nodes[i], nodes[j]))
#     return pairs

# def random_exchange(routes, coords, m, radius=10):
#     """
#     Perform m random exchanges of pairs of nearby customers between two different routes
#     """
#     all_routes = routes[:]
#     n = len(all_routes)

#     if n < 2:
#         print("Need at least two routes to perform exchanges.")
#         return all_routes

#     exchanges_done = 0
#     attempts = 0
#     max_attempts = m * 10  # avoid infinite loops

#     while exchanges_done < m and attempts < max_attempts:
#         attempts += 1

#         # Pick two distinct routes randomly
#         r1_idx, r2_idx = random.sample(range(n), 2)
#         r1 = all_routes[r1_idx]
#         r2 = all_routes[r2_idx]

#         # Find nearby pairs in each route
#         pairs_r1 = find_nearby_pairs(r1, coords, radius)
#         pairs_r2 = find_nearby_pairs(r2, coords, radius)

#         if not pairs_r1 or not pairs_r2:
#             continue  # no pairs to swap in one or both routes

#         # Randomly pick one pair from each
#         pair1 = random.choice(pairs_r1)
#         pair2 = random.choice(pairs_r2)

#         # Swap the two pairs between routes
#         # Remove pair1 nodes from r1 and add pair2 nodes, similarly for r2
#         # Implementation detail: swap nodes in route lists

#         def swap_pairs(route, old_pair, new_pair):
#             new_route = route[:]
#             for old_node in old_pair:
#                 if old_node in new_route:
#                     new_route.remove(old_node)
#             insert_pos = 1  # after depot
#             # Insert new nodes at insert_pos
#             for node in new_pair:
#                 new_route.insert(insert_pos, node)
#                 insert_pos += 1
#             return new_route

#         new_r1 = swap_pairs(r1, pair1, pair2)
#         new_r2 = swap_pairs(r2, pair2, pair1)

#         # Update routes
#         all_routes[r1_idx] = new_r1
#         all_routes[r2_idx] = new_r2

#         exchanges_done += 1

#     if attempts >= max_attempts:
#         print("Reached maximum attempts during perturbation.")

#     return all_routes

# def save_tour(routes, path):
#     with open(path, 'w') as f:
#         for idx, route in enumerate(routes, 1):
#             # Remove depot at start/end for cleaner display
#             route_nodes = route[1:-1]
#             f.write(f"Route {idx}: {' '.join(map(str, route_nodes))}\n")




# def main():
#     parser = argparse.ArgumentParser(description="Perturb VRP solution by random exchange")
#     parser.add_argument('--vrp', type=str, help='Input .vrp file path (optional if --tour given)')
#     parser.add_argument('--tour', type=str, help='Input .tour solution file path (optional if --vrp given)')
#     parser.add_argument('-m', type=int, default=1, help='Number of random exchanges')
#     parser.add_argument('--output', type=str, default='perturbed_solution.tour', help='Output .tour file')
#     parser.add_argument('--radius', type=float, default=10, help='Distance radius to consider nearby customers')
#     args = parser.parse_args()

#     if not args.vrp and not args.tour:
#         print("Error: Must provide either --vrp or --tour input")
#         return

#     if args.tour:
#         routes = parse_tour(args.tour)
#         # Need coords for distance calc - so vrp must be provided too
#         if not args.vrp:
#             print("Error: --vrp file required when using --tour to get coordinates")
#             return
#         vrp_data = parse_vrp(args.vrp)
#         coords = vrp_data["coords"]
#     else:
#         # vrp only, generate initial routes (naive nearest neighbor)
#         vrp_data = parse_vrp(args.vrp)
#         coords = vrp_data["coords"]
#         # simple initial route: one route with all nodes + depot (not optimized)
#         depot = vrp_data["depot"]
#         route = [depot] + sorted([node for node in coords if node != depot]) + [depot]
#         routes = [route]

#     perturbed_routes = random_exchange(routes, coords, args.m, radius=args.radius)
#     save_tour(perturbed_routes, args.output)
#     print(f"Perturbed solution saved to {args.output}")

# if __name__ == "__main__":
#     main()





import argparse
import random
import math

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
        depot = 1  # Default depot

    return {
        "coords": coords,
        "demands": demands,
        "depot": depot
    }

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

def compute_distance(coords, i, j):
    xi, yi = coords[i]
    xj, yj = coords[j]
    return math.hypot(xi - xj, yi - yj)

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
        print("Reached maximum attempts during perturbation.")

    return all_routes

def compute_total_cost(vrp_data, routes):
    coords = vrp_data["coords"]
    total_cost = 0
    for route in routes:
        for i in range(len(route)-1):
            total_cost += compute_distance(coords, route[i], route[i+1])
    return total_cost

def save_tour(routes, path, total_cost):
    with open(path, 'w') as f:
        f.write(f"# Total Cost: {total_cost:.4f}\n")
        for idx, route in enumerate(routes, 1):
            route_nodes = route[1:-1]
            f.write(f"Route {idx}: {' '.join(map(str, route_nodes))}\n")

def main():
    parser = argparse.ArgumentParser(description="Perturb VRP solution by random exchange")
    parser.add_argument('--vrp', type=str, help='Input .vrp file path (optional if --tour given)')
    parser.add_argument('--tour', type=str, help='Input .tour solution file path (optional if --vrp given)')
    parser.add_argument('-m', type=int, default=1, help='Number of random exchanges')
    parser.add_argument('--output', type=str, default='perturbed_solution.tour', help='Output .tour file')
    parser.add_argument('--radius', type=float, default=10, help='Distance radius to consider nearby customers')
    args = parser.parse_args()

    if not args.vrp and not args.tour:
        print("Error: Must provide either --vrp or --tour input")
        return

    if args.tour:
        routes = parse_tour(args.tour)
        if not args.vrp:
            print("Error: --vrp file required when using --tour to get coordinates")
            return
        vrp_data = parse_vrp(args.vrp)
        coords = vrp_data["coords"]
    else:
        vrp_data = parse_vrp(args.vrp)
        coords = vrp_data["coords"]
        depot = vrp_data["depot"]
        route = [depot] + sorted([node for node in coords if node != depot]) + [depot]
        routes = [route]

    perturbed_routes = random_exchange(routes, coords, args.m, radius=args.radius)
    total_cost = compute_total_cost(vrp_data, perturbed_routes)
    save_tour(perturbed_routes, args.output, total_cost)
    print(f"Perturbed solution saved to {args.output}")

if __name__ == "__main__":
    main()
