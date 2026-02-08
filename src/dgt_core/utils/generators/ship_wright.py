from src.dgt_core.kernel.state import ShipGenome
from src.dgt_core.kernel.fleet_roles import FleetRole, ROLE_MAP

class ShipWright:
    """Binds neuro-genetic traits to physical Newtonian bodies."""
    
    @staticmethod
    def apply_genetics(genome: ShipGenome, role: FleetRole) -> dict:
        """
        Convert genetic traits into physical ship attributes.
        
        Args:
            genome: The genetic makeup (traits 0.0-1.0)
            role: The tactical role (Interceptor, Heavy, Scout)
            
        Returns:
            Dictionary of physical attributes for the physics engine
        """
        modifiers = ROLE_MAP[role]
        
        # Calculate derived physics attributes
        # Based on TurboShells traits (0.0 - 1.0)
        # Default to 0.5 if trait missing
        base_thrust = genome.traits.get("aggression", 0.5) * 500.0
        base_armor = genome.traits.get("armor", 0.5)
        base_mass = 10.0
        
        return {
            "max_thrust": base_thrust * modifiers.thrust_mult,
            "render_thickness": max(1, int(base_armor * modifiers.armor_mult * 5)),
            "mass": base_mass * modifiers.mass_mult,
            "bounding_dim": 15 * modifiers.scale,
            "turn_rate": 3.0 * (1.0 / modifiers.mass_mult) # Heuristic: Heavier turns slower
        }
