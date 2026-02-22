import sys
from src.apps.space_trader.world.location_graph import LocationGraph
from src.apps.space_trader.world.encounter import EncounterSystem
from src.apps.space_trader.economy.price_model import PriceModel
from src.apps.space_trader.economy.market import Market
from src.apps.space_trader.player.ship import PlayerShip

def print_status(ship: PlayerShip, graph: LocationGraph):
    loc = graph.get(ship.location_id)
    print("\n" + "="*40)
    print(f" LOCATION : {loc.name} ({loc.faction.title()})")
    print(f" DESC     : {loc.description}")
    print(f" CREDITS  : {ship.credits} cr")
    print(f" FUEL     : {ship.fuel} / {ship.max_fuel}")
    print(f" CARGO    : {ship.cargo.space_used()} / {ship.cargo.capacity}")
    if ship.cargo.contents:
        for item, qty in ship.cargo.contents.items():
            print(f"            - {qty}x {item}")
    print("="*40)

def print_market(ship: PlayerShip, market: Market):
    listings = market.get_listings(ship.location_id)
    if not listings:
        print("\n [ Market Closed / No Goods Available ]")
        return
        
    print("\n--- LOCAL MARKET ---")
    print(f"{'GOOD':<10} | {'BUY FOR':<10} | {'SELL FOR':<10}")
    print("-" * 35)
    for l in listings:
        print(f"{l['good'].title():<10} | {l['buy_price']:<10} | {l['sell_price']:<10}")
        
def print_travel(ship: PlayerShip, graph: LocationGraph):
    loc = graph.get(ship.location_id)
    print("\n--- NAV COMPUTER ---")
    print("Available Jumps (Requires 1 Fuel):")
    for conn in loc.connections:
        n = graph.get(conn)
        print(f"  - {n.id} ({n.name})")

def main():
    print("Initializing Space Trader REPL...")
    graph = LocationGraph()
    price_model = PriceModel(graph)
    market = Market(price_model)
    encounter_system = EncounterSystem()
    ship = PlayerShip()

    print("\n[ SYSTEM ONLINE ]")

    while True:
        print_status(ship, graph)
        print("\nCOMMANDS: [status, market, buy <good> <qty>, sell <good> <qty>, travel <node_id>, refuel, quit]")
        cmd_input = input(">> ").strip().lower()
        
        parts = cmd_input.split()
        if not parts:
            continue
            
        cmd = parts[0]
        
        if cmd == "quit":
            print("Shutting down... Fly safe.")
            break
        elif cmd == "status":
            continue
        elif cmd == "market":
            print_market(ship, market)
        elif cmd == "refuel":
            cost = (ship.max_fuel - ship.fuel) * 5
            if cost == 0:
                print("Fuel tanks already full.")
            elif ship.credits >= cost:
                ship.credits -= cost
                ship.fuel = ship.max_fuel
                print(f"Refueled for {cost} cr.")
            else:
                print(f"Cannot afford fuel (need {cost} cr).")
        elif cmd == "buy" and len(parts) == 3:
            good = parts[1]
            try:
                qty = int(parts[2])
                res = market.buy(ship.location_id, good, qty, ship.cargo, ship.credits)
                ship.credits = res["credits"]
                print("\n-> " + res["message"])
            except ValueError:
                print("Invalid quantity.")
        elif cmd == "sell" and len(parts) == 3:
            good = parts[1]
            try:
                qty = int(parts[2])
                res = market.sell(ship.location_id, good, qty, ship.cargo, ship.credits)
                ship.credits = res["credits"]
                print("\n-> " + res["message"])
            except ValueError:
                print("Invalid quantity.")
        elif cmd == "travel" and len(parts) == 2:
            target = parts[1]
            res = ship.travel(target, graph, encounter_system)
            print("\n-> " + res["message"])
            if res.get("encounter"):
                print("!!! ALERT !!! " + res["encounter"]["message"])
            
            # Reseed economy params on travel
            price_model.update_daily()
        else:
            print("Unknown command format.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nShutting down... Fly safe.")
        sys.exit(0)
