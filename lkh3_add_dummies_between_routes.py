import argparse

def load_routes(tour_path):
    routes = []
    current_route = []
    with open(tour_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("DIMENSION") or line.startswith("NAME") or line.startswith("TYPE"):
                continue
            if line.startswith("Route") or line.startswith("TOUR_SECTION"):
                continue
            if line == "EOF" or line == "-1":
                if current_route:
                    routes.append(current_route)
                break
            if line.isdigit():
                node = int(line)
                if node == 1:
                    if current_route:
                        routes.append(current_route)
                        current_route = []
                else:
                    current_route.append(node)
    return routes

def insert_dummy_nodes(routes, starting_index):
    tour = []
    dummy = starting_index
    for route in routes:
        tour.extend(route)
        tour.append(dummy)
        dummy += 1
    return tour

def write_tour_with_dummies(output_path, tour, dimension, name="dummy_added_result"):
    with open(output_path, 'w') as f:
        f.write(f"NAME : {name}\n")
        f.write("TYPE : TOUR\n")
        f.write(f"DIMENSION : {dimension}\n")
        f.write("TOUR_SECTION\n")
        for node in tour:
            f.write(f"{node}\n")
        f.write("-1\nEOF\n")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, required=True, help="Input .tour file with route format")
    parser.add_argument("--output", type=str, required=True, help="Output .tour file with dummy nodes")
    parser.add_argument("--start_dummy", type=int, default=33, help="Starting index for dummy nodes")
    args = parser.parse_args()

    routes = load_routes(args.input)
    dummy_tour = insert_dummy_nodes(routes, args.start_dummy)
    total_nodes = max(max(r) for r in routes) + len(routes)
    write_tour_with_dummies(args.output, dummy_tour, dimension=total_nodes)

if __name__ == "__main__":
    main()
