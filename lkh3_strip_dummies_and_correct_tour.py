import argparse

def parse_tour_with_dummies(path, customer_max_index):
    routes = []
    with open(path, 'r') as f:
        lines = f.readlines()

    tour_section = False
    current_route = []

    for line in lines:
        line = line.strip()
        if line == "TOUR_SECTION":
            tour_section = True
            continue
        if not tour_section:
            continue
        if line == "-1" or line == "EOF":
            if current_route:
                routes.append(current_route)
            break

        node = int(line)
        if node > customer_max_index:
            if current_route:
                routes.append(current_route)
                current_route = []
        else:
            current_route.append(node)

    return routes

def write_clean_tour(path, routes, name="cleaned_tour"):
    with open(path, 'w') as f:
        f.write(f"NAME : {name}\n")
        f.write("TYPE : TOUR\n")
        f.write(f"DIMENSION : {sum(len(r) for r in routes)}\n")
        f.write("TOUR_SECTION\n")
        for route in routes:
            for node in route:
                f.write(f"{node}\n")
        f.write("-1\nEOF\n")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, required=True, help="Input .tour with dummy nodes")
    parser.add_argument("--output", type=str, required=True, help="Output cleaned .tour file")
    parser.add_argument("--max_customer", type=int, required=True, help="Maximum customer index (before dummy nodes)")
    args = parser.parse_args()

    routes = parse_tour_with_dummies(args.input, args.max_customer)
    write_clean_tour(args.output, routes)

if __name__ == "__main__":
    main()
