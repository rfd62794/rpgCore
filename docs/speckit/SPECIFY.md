# rpgCore System Specifications
**Spec-Driven Development Specifications v1.0**

---

## 🌍 World System Specifications

### 1. Hexagon World Geography System

#### 1.1 Core Components
```python
@dataclass
class HexagonWorld:
    """Six-culture hexagonal world with garden center"""
    cultures: Dict[str, CultureRegion]
    garden: GardenRegion
    intersections: Dict[str, IntersectionZone]
    world_state: WorldState

@dataclass 
class CultureRegion:
    """One of six cultural territories"""
    culture_type: CultureType  # EMBER, CRYSTAL, TUNDRA, etc.
    position: HexPosition
    resources: ResourceInventory
    diplomatic_standing: Dict[str, float]  # Relationship with player
    territory_map: GridMap
```

#### 1.2 Position System
- **Coordinate System**: Hexagonal grid with axial coordinates
- **Scale**: Each culture region = 10x10 tiles (48px per tile)
- **Garden Position**: Center coordinate (0, 0) - neutral ground
- **Intersection Zones**: Between neighboring cultures, wilderness areas

#### 1.3 World State Management
- **Fracture State**: Global conflict level (cold war → open conflict)
- **Time Progression**: World events, seasonal changes
- **Cultural Relations**: Dynamic alliances, trade routes, conflicts
- **Player Impact**: Actions affect diplomatic standing across cultures

### 2. Culture System Specifications

#### 2.1 Cultural Attributes
```python
@dataclass
class CultureAttributes:
    """Statistical and behavioral tendencies per culture"""
    primary_stat: StatType      # STRENGTH, DEXTERITY, etc.
    secondary_stat: StatType
    temperament: Temperament    # AGGRESSIVE, CURIOUS, PATIENT, etc.
    elemental_affinity: Element # FIRE, WIND, WATER, EARTH, ICE, LIGHTNING
    resource_specialty: ResourceType
    cultural_bias: Dict[str, float]  # Behavior modifiers
```

#### 2.2 Six Culture Implementations
| Culture | Primary | Secondary | Element | Resource | Temperament |
|---------|---------|-----------|---------|----------|-------------|
| Ember | Strength | Attack | Fire | Scrap | Aggressive |
| Gale | Dexterity | Speed | Wind | Information | Curious |
| Marsh | Constitution | Endurance | Water | Food | Patient |
| Crystal | Defense | Wisdom | Earth | Gems | Cautious |
| Tundra | Intelligence | Perception | Ice | Knowledge | Independent |
| Tide | Charisma | Adaptability | Lightning | Gold | Sociable |

#### 2.3 Cultural Behavior Systems
- **Diplomatic AI**: Each culture has unique personality in negotiations
- **Trade Logic**: Resource exchange rates based on need and relationship
- **Conflict Resolution**: Different approaches to disputes (Ember=force, Tide=trade)
- **Information Flow**: Gale as information brokers, Tide as diplomatic hub

### 3. Garden System Specifications

#### 3.1 Garden Architecture
```python
@dataclass
class GardenRegion:
    """Player home base - neutral convergence point"""
    rooms: Dict[str, GardenRoom]
    ship_state: ShipRepairState
    slime_population: SlimeRegistry
    visitor_log: List[CulturalVisit]
    expansion_progress: Dict[str, float]

@dataclass
class GardenRoom:
    """Expandable garden spaces"""
    room_type: RoomType  # NURSERY, CLINIC, TRAINING, VAULT, etc.
    unlocked: bool
    equipment: List[Equipment]
    slime_capacity: int
```

#### 3.2 Garden Systems
- **Expansion Mechanic**: New rooms unlock through progression
- **Ship Repair**: Visible progress toward original goal
- **Slime Management**: Breeding, training, aging systems
- **Diplomatic Hub**: Cultural emissaries visit garden
- **Resource Processing**: Convert raw resources to usable items

### 4. Void System Specifications

#### 4.1 Void Mechanics
```python
@dataclass
class VoidTraits:
    """Rare genetic traits from original unified culture"""
    trait_level: float  # 0.0 to 1.0, higher = more void influence
    visual_effects: List[VoidEffect]
    cultural_resistance: Dict[str, float]  # Other cultures' reactions
    world_event_flag: bool  # Triggers emissary visits
```

#### 4.2 Void Breeding System
- **Garden Requirement**: Only garden conditions can produce void slimes
- **Multi-Generation**: Requires deep breeding chains, not random chance
- **World Events**: Void slime appearance triggers cultural emissaries
- **Cultural Reactions**: Fear, curiosity, worship based on culture

### 5. Resource System Specifications

#### 5.1 Three Core Resources
```python
@dataclass
class ResourceInventory:
    """World economic resources"""
    gold: int           # Liquid economy (Tide)
    scrap: int          # Material economy (Ember)  
    food: int           # Living economy (Marsh)
    rare_resources: Dict[str, int]  # Culture-specific
```

#### 5.2 Resource Flow Systems
- **Generation**: Each culture produces specialty resource
- **Trade**: Exchange rates based on supply/demand and relationships
- **Processing**: Raw resources → usable items → equipment
- **Consumption**: Slime feeding, equipment crafting, ship repair

### 6. Intersection Zone System Specifications

#### 6.1 Zone Mechanics
```python
@dataclass
class IntersectionZone:
    """Wilderness between two cultures"""
    primary_culture: CultureType
    secondary_culture: CultureType
    elemental_mix: Tuple[Element, Element]
    danger_level: float
    resource_nodes: List[ResourceNode]
    encounter_table: EncounterTable
```

#### 6.2 Zone Types and Characteristics
| Zone | Cultures | Elements | Resources | Danger |
|------|----------|----------|-----------|--------|
| Magma | Ember + Crystal | Fire + Earth | Weapons, Scrap | High |
| Firestorm | Ember + Gale | Fire + Wind | Information | Extreme |
| Squall | Gale + Tide | Wind + Lightning | Contraband | Medium |
| Storm | Tide + Marsh | Lightning + Water | Exotic Food | High |
| Bog | Marsh + Tundra | Water + Ice | Secrets | Variable |
| Frost | Tundra + Crystal | Ice + Earth | Ancient Items | Extreme |

### 7. Narrative System Specifications

#### 7.1 Story Progression
```python
@dataclass
class NarrativeState:
    """Player's journey through the world"""
    phase: StoryPhase  # CRASH, SURVIVAL, UNDERSTANDING, CHOICE
    ship_progress: float  # 0.0 to 1.0 repair completion
    cultural_discovery: Dict[str, float]  # Knowledge per culture
    world_understanding: float  # Overall lore discovery
    relationship_depth: Dict[str, float]  # Bond with slimes
```

#### 7.2 Narrative Systems
- **Discovery Mechanics**: Information revealed through exploration and interaction
- **Relationship Building**: Slime bonds affect cultural diplomacy
- **Choice Consequences**: Actions have lasting world impacts
- **Emotional Arc**: From "want to leave" to "understand why I stay"

### 8. Genetics System Specifications

#### 8.1 Genetic Architecture
```python
@dataclass
class SlimeGenome:
    """Complete genetic profile of a slime"""
    culture: CultureGenes
    stats: StatGenes
    shape: ShapeGenes
    color: ColorGenes
    lineage: LineageRecord

@dataclass
class CultureGenes:
    """Culture inheritance using dominant/recessive alleles"""
    allele_a: tuple[str, float]  # (culture_name, expression_weight)
    allele_b: tuple[str, float]
    expression: dict[str, float]  # Resolved weights (sums to 1.0)
    tier: int  # 1-8 genetic complexity
    tier_name: str  # 'Blooded', 'Bordered', 'Sundered', etc.
```

#### 8.2 Eight-Tier Genetic System
| Tier | Count | Description | Visual Expression |
|------|-------|-------------|-------------------|
| 1 - Blooded | 6 | Single culture heritage | Solid, vivid culture color |
| 2 - Bordered | 6 | Two adjacent cultures | Blended color gradient |
| 3 - Sundered | 3 | Two opposite cultures | Sectional color, hard boundary |
| 4 - Drifted | 6 | Skip-one cultures | Partial blend, soft edges |
| 5 - Threaded | 20 | Three culture heritage | Complex color mixing |
| 6 - Convergent | 15 | Four culture heritage | Void characteristics begin |
| 7 - Liminal | 6 | Five culture heritage | Almost Void, one color missing |
| 8 - Void | 1 | All six cultures unified | Full iridescent spectrum |

#### 8.3 Breeding Mechanics
- **Allele Resolution**: Each parent contributes one allele, dominant expresses more strongly
- **Stat Inheritance**: Weighted average + random variance + mutation chance
- **Visual Inheritance**: Color blend + shape selection + pattern expression
- **Mutation Factors**: Sundered parents, high generation, Void proximity

#### 8.4 ECS Integration
- **GeneticsComponent**: Complete genome + level + experience
- **BreedingComponent**: Fertility + cooldown + offspring history
- **GeneticsSystem**: Inheritance calculations + tier determination
- **BreedingSystem**: Breeding operations + cooldown management

#### 8.5 Performance Specifications
- **Memory**: ~1KB per slime genome
- **Computation**: <1ms breeding calculation, <0.1ms tier calc
- **Storage**: Compact JSON format for save files
- **Rendering**: <2ms visual profile generation

### 9. Integration with Existing Systems

#### 9.1 ECS Integration
- **CultureComponent**: Cultural affiliation and traits
- **ResourceComponent**: Resource inventory and production
- **WorldPositionComponent**: Position in hexagon world
- **RelationshipComponent**: Diplomatic standing data

#### 9.2 Rendering Integration
- **Cultural Visuals**: Color palettes and movement patterns per culture
- **Environmental Rendering**: Different terrain per region
- **Void Effects**: Special rendering for void traits
- **Garden Expansion**: Visual progression as rooms unlock

#### 9.3 Save System Integration
- **World State**: Complete world state persistence
- **Cultural Memory**: Faction relationships saved
- **Player Progress**: Narrative state and achievements
- **Garden State**: Room unlocks and population

---

## 🎯 Implementation Priority

### Phase 1: Core Geography
1. Hexagon coordinate system
2. Basic culture definitions
3. Garden foundation
4. Resource inventory system

### Phase 2: Cultural Systems  
1. Culture-specific behaviors
2. Diplomatic AI
3. Trade mechanics
4. Intersection zones

### Phase 3: Advanced Systems
1. Void breeding mechanics
2. World events
3. Narrative progression
4. Cultural emissaries

---

**Specified**: 2026-03-01  
**Version**: 1.0  
**Status**: READY FOR IMPLEMENTATION  
**Dependencies**: Constitution v1.0
