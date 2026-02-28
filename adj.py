#!/usr/bin/env python3
"""
ADJ System - Top-Level CLI Interface
Primary interface for Robert (Director) and Coding Agent to govern DGT Engine development.

Usage:
    python adj.py status          - Show current DGT Engine status
    python adj.py phase <number>  - Show specific phase status
    python adj.py priorities      - Show top priorities
    python adj.py blockers        - Show current blockers
    python adj.py next            - Show next actions
    python adj.py approve <phase> - Director approval for phase
    python adj.py update          - Update dashboard with current state
    python adj.py strategy <num>  - Phase strategy analysis
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Layer imports
from src.tools.apj.data_loader import DataLoader
from src.tools.apj.analysis import StatusAnalyzer
from src.tools.apj.model_router import ModelRouter


class ADJSystem:
    """Top-level ADJ System CLI - Layer-aware"""
    
    def __init__(self):
        self.root_dir = Path(__file__).parent
        self.docs_dir = self.root_dir / "docs"
        self.dashboard_file = self.docs_dir / "ADJ_DASHBOARD.md"
        self.milestones_file = self.docs_dir / "MILESTONES.md"
        self.tasks_file = self.docs_dir / "TASKS.md"
        
        # Layer 1: Data loader
        self.data_loader = DataLoader(self.root_dir)
        
        # Layer 2: Local analysis
        self.analyzer = StatusAnalyzer(self.data_loader)
        
        # Layer 3+: Model router
        self.router = ModelRouter()
        
        # Track layers used
        self.layers_used = []
    
    def _record_layer(self, layer: str):
        """Track which layers are used"""
        self.layers_used.append(layer)
    
    def _run_tests(self) -> int:
        """Run tests and return count"""
        output = self.run_command(["uv", "run", "pytest", "--tb=no", "-q"])
        if "passed" in output:
            # Extract number from "685 passed, 3 skipped"
            for line in output.split('\n'):
                if "passed" in line:
                    parts = line.split()[0]
                    try:
                        return int(parts)
                    except ValueError:
                        pass
        return 0
    
    def get_test_count(self) -> int:
        """Get test count - try journal first, then run tests"""
        self._record_layer("Layer 1: Data Files")
        
        # Try journal first
        cached = self.data_loader.get_latest_test_floor()
        if cached is not None:
            return cached
        
        # Run tests if no cached value
        return self._run_tests()
    
    def get_current_status(self) -> Dict:
        """Get status - use Layer 1 + 2 only"""
        self._record_layer("Layer 1: Data Files")
        self._record_layer("Layer 2: Local Analysis")
        
        return {
            "test_floor": self.get_test_count(),
            "protected_minimum": 462,
            "phases": self.analyzer.milestones,
            "blockers": self.analyzer.get_blockers(),
            "priorities": self.analyzer.get_priorities()
        }
    
    def show_cost(self):
        """Show which layers were used"""
        print("\n🔧 Layers Used:")
        for layer in self.layers_used:
            cost = self.router.get_layer_cost(layer)
            print(f"  {layer} ({cost})")
    
    def show_strategy(self, phase_number: str):
        """Show phase strategy using available layers"""
        phase_data = self.analyzer.get_phase_status(int(phase_number))
        
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║                    PHASE {phase_number} STRATEGY ANALYSIS           ║
╚══════════════════════════════════════════════════════════════╝

📊 PHASE DATA:
  Name: {phase_data.get('name', 'Unknown')}
  Status: {phase_data.get('status', 'Unknown')}
  Goals: {', '.join(phase_data.get('goals', []))}
""")
        
        # Use Layer 3 if available
        self._record_layer("Layer 1: Data Files")
        self._record_layer("Layer 2: Local Analysis")
        
        result, layer_used = self.router.phase_strategy(int(phase_number), phase_data)
        self._record_layer(layer_used)
        
        if "error" in result:
            print(f"🤖 AI Analysis: {result.get('fallback', 'Local analysis only')}")
            print(f"📋 Local Analysis:")
            print(f"  - Strategic Importance: {phase_data.get('name', 'Unknown')}")
            print(f"  - Current Status: {phase_data.get('status', 'Unknown')}")
            print(f"  - Success Criteria: Complete phase goals")
        else:
            print(f"🤖 AI Analysis (Layer 3):")
            if 'response' in result:
                print(f"  {result['response']}")
        
        self.show_cost()
    
    def show_status(self):
        """Show current DGT Engine status"""
        status = self.get_current_status()
        
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║                    ADJ SYSTEM - DGT ENGINE STATUS              ║
╚══════════════════════════════════════════════════════════════╝

📊 TEST FLOOR: {status['test_floor']} / {status['protected_minimum']} (protected minimum)

🏗️  PHASE STATUS:
  Phase 1: Entity Unification {status['phases']['phase_1']['status']} ({status['phases']['phase_1']['tests']} tests)
  Phase 2: ECS Foundation     {status['phases']['phase_2']['status']} ({status['phases']['phase_2']['tests']} tests)
  Phase 3: Tower Defense     {status['phases']['phase_3']['status']} ({status['phases']['phase_3']['tests']} tests)

🎯 ACTIVE MILESTONE: M_PHASE3

🚫 CURRENT BLOCKERS:""")
        
        if status['blockers']:
            for i, blocker in enumerate(status['blockers'], 1):
                print(f"  {i}. {blocker['description']} ({blocker['fix_time']} fix)")
        else:
            print("  ✅ No blockers identified")
        
        print(f"""
🔥 TOP PRIORITIES:""")
        
        for priority in status['priorities']:
            print(f"  {priority['priority']}. {priority['task']} ({priority['status']})")
        
        print(f"""
📋 NEXT ACTIONS:
  1. Review blockers above
  2. Address highest priority item
  3. Run 'python adj.py next' for detailed next steps
  4. Run 'python adj.py approve phase3' to approve Phase 3

📖 FULL DASHBOARD: {self.dashboard_file}
""")
        self.show_cost()  # Add cost display
    
    def show_phase(self, phase_number: str):
        """Show specific phase status"""
        phases = {
            "1": {
                "name": "Entity Unification",
                "status": "✅ Complete",
                "milestone": "M1",
                "goals": ["G1: Unified Creature System"],
                "achievements": [
                    "Single Creature class across all demos",
                    "Unified genome system",
                    "Consistent creature behavior"
                ],
                "test_count": 545
            },
            "2": {
                "name": "ECS Foundation",
                "status": "✅ Complete", 
                "milestone": "M2",
                "goals": ["G2: ECS Architecture"],
                "achievements": [
                    "KinematicsComponent + System",
                    "BehaviorComponent + System",
                    "ComponentRegistry + SystemRunner",
                    "ECS proven in Garden integration"
                ],
                "test_count": 583
            },
            "3": {
                "name": "Tower Defense Integration",
                "status": "🔄 In Planning",
                "milestone": "M_PHASE3",
                "goals": ["G3: Multi-Genre Support", "G4: Monetizable Platform", "G5: Production Infrastructure"],
                "achievements": [
                    "Architecture locked (8/8 decisions)",
                    "Sprite systems audited",
                    "Multi-tenant strategy defined"
                ],
                "test_count": "Target 785",
                "sub_phases": [
                    "3.0: ECS Rendering Refactor",
                    "3.1: Grid System & Components", 
                    "3.2: Tower Defense Systems",
                    "3.3: TD Session & Persistence",
                    "3.4: TD Scene & Integration",
                    "3.5: Fantasy RPG Tenant",
                    "3.6: Archive & Documentation"
                ]
            }
        }
        
        if phase_number not in phases:
            print(f"❌ Phase {phase_number} not found. Use: 1, 2, or 3")
            return
        
        phase = phases[phase_number]
        
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║                    PHASE {phase_number}: {phase['name']}              ║
╚══════════════════════════════════════════════════════════════╝

📊 STATUS: {phase['status']}
🎯 MILESTONE: {phase['milestone']}
🎯 GOALS: {', '.join(phase['goals'])}

🏆 ACHIEVEMENTS:""")
        
        for achievement in phase['achievements']:
            print(f"  ✅ {achievement}")
        
        if 'test_count' in phase:
            print(f"\n📊 TEST COUNT: {phase['test_count']}")
        
        if 'sub_phases' in phase:
            print(f"\n📋 SUB-PHASES:")
            for sub_phase in phase['sub_phases']:
                print(f"  🔄 {sub_phase}")
        
        print(f"""
📖 MORE INFO: Check {self.dashboard_file} for full details
""")
    
    def show_priorities(self):
        """Show current priorities"""
        priorities = self.get_priorities()
        
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║                        TOP PRIORITIES                          ║
╚══════════════════════════════════════════════════════════════╝
""")
        
        for priority in priorities:
            status_emoji = "✅" if priority['status'] == "✅ Complete" else "🔄"
            print(f"""
{priority['priority']}. {priority['task']}
   Status: {status_emoji} {priority['status']}
   Impact: {priority['impact']}
   Time: {priority['time']}
""")
    
    def show_blockers(self):
        """Show current blockers"""
        blockers = self.get_blockers()
        
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║                          CURRENT BLOCKERS                        ║
╚══════════════════════════════════════════════════════════════╝
""")
        
        if blockers:
            for i, blocker in enumerate(blockers, 1):
                print(f"""
{i}. {blocker['description']}
   Type: {blocker['type']}
   Impact: {blocker['impact']}
   Fix Time: {blocker['fix_time']}
""")
        else:
            print("✅ NO BLOCKERS IDENTIFIED")
            print("All systems operational and ready for development.")
    
    def show_next(self):
        """Show next actions"""
        status = self.get_current_status()
        
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║                          NEXT ACTIONS                            ║
╚══════════════════════════════════════════════════════════════╝

🎯 IMMEDIATE (This Session):
""")
        
        if status['blockers']:
            print("1. Address blockers:")
            for blocker in status['blockers']:
                print(f"   - Fix {blocker['description']} ({blocker['fix_time']})")
        else:
            print("1. ✅ No blockers - proceed with priorities")
        
        print(f"""
2. Review Phase 3 architecture:
   - Check {self.dashboard_file}
   - Verify 8 critical decisions
   - Confirm timeline (6-8 sessions)

3. Director decision needed:
   - Run: python adj.py approve phase3
   - Approve Phase 3 specification
   - Unlock implementation

🚀 SHORT-TERM (Next Session):
""")
        
        if status['priorities'][1]['status'] == "🔄 Awaiting Director":
            print("1. Await Director approval for Phase 3")
            print("2. Once approved, begin Phase 3.0 implementation")
        else:
            print("1. Begin Phase 3.0: ECS Rendering Refactor")
            print("2. Add RenderComponent to ECS system")
            print("3. Create RenderingSystem for ECS pipeline")
        
        print(f"""
📋 COMMANDS TO USE:
  python adj.py status      - Full status overview
  python adj.py phase 3     - Phase 3 details
  python adj.py priorities  - Current priorities
  python adj.py approve 3   - Approve Phase 3 (Director only)
  python adj.py update      - Update dashboard
""")
    
    def approve_phase(self, phase_number: str):
        """Director approval for phase"""
        if phase_number != "3":
            print("❌ Only Phase 3 requires approval at this time")
            return
        
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║                    DIRECTOR APPROVAL REQUEST                   ║
╚══════════════════════════════════════════════════════════════╝

🎯 PHASE 3: Tower Defense Integration
📊 Test Target: 785+ passing tests
⏱️  Timeline: 6-8 sessions (40-60 hours)
🏗️  Architecture: Modular sprite-driven engine
🎮  Tenants: Slime Garden (primary) + Fantasy RPG (proof)

✅ CRITICAL DECISIONS LOCKED (8/8):
  1. RenderComponent: Add NOW (Phase 3.0)
  2. RenderingSystem: FULL ECS pipeline
  3. Enemy Sprites: FREE (OpenGameArt/itch.io)
  4. Animation: FULL Framework
  5. Multi-Tenant Config: Implement NOW
  6. Projectiles: Simple (procedural)
  7. Tower Selection: Existing highlight
  8. Turbo Shells: KEEP alive

🎯 SUCCESS CRITERIA:
  - 785+ tests passing
  - Tower Defense playable with pixel-gen towers + sprite enemies
  - Fantasy RPG playable with same code, different assets
  - Multi-tenant configuration proven
  - Zero breaking changes to existing demos

⚠️  RISK ASSESSMENT: LOW
  - All systems exist (SlimeRenderer, SpriteLoader, ECS)
  - Architecture proven (Phase 1-2 complete)
  - No blockers identified
  - Full test coverage planned

📋 IMPLEMENTATION PHASES:
  3.0: ECS Rendering Refactor (690+ tests)
  3.1: Grid System & Components (710+ tests)
  3.2: Tower Defense Systems (730+ tests)
  3.3: TD Session & Persistence (745+ tests)
  3.4: TD Scene & Integration (755+ tests)
  3.5: Fantasy RPG Tenant (770+ tests)
  3.6: Archive & Documentation (785+ tests)

🤔 DIRECTOR DECISION REQUIRED:
""")
        
        response = input("Approve Phase 3? (yes/no/conditional): ").lower().strip()
        
        if response == "yes":
            self._record_approval("phase3", "APPROVED")
            print("✅ Phase 3 APPROVED!")
            print("🚀 PyPro Architect can now proceed with specification.")
            print("📋 Next: Coding Agent will begin Phase 3.0 implementation.")
        elif response == "conditional":
            conditions = input("Conditions: ").strip()
            self._record_approval("phase3", f"CONDITIONAL: {conditions}")
            print(f"🔄 Phase 3 CONDITIONALLY APPROVED")
            print(f"Conditions: {conditions}")
        elif response == "no":
            self._record_approval("phase3", "REJECTED")
            print("❌ Phase 3 REJECTED")
            print("📋 Please provide feedback for revision.")
        else:
            print("❌ Invalid response. Use: yes, no, or conditional")
    
    def _record_approval(self, phase: str, decision: str):
        """Record director approval"""
        approval_file = self.docs_dir / "approvals.json"
        
        approvals = {}
        if approval_file.exists():
            with open(approval_file, 'r') as f:
                approvals = json.load(f)
        
        approvals[phase] = {
            "decision": decision,
            "timestamp": datetime.now().isoformat(),
            "test_floor": self.get_test_count()
        }
        
        with open(approval_file, 'w') as f:
            json.dump(approvals, f, indent=2)
    
    def update_dashboard(self):
        """Update dashboard with current state"""
        status = self.get_current_status()
        
        # Update the dashboard file
        if self.dashboard_file.exists():
            # Read existing dashboard
            with open(self.dashboard_file, 'r') as f:
                content = f.read()
            
            # Update timestamp and test floor
            content = content.replace(
                f"**Last Updated**: ",
                f"**Last Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n**Test Floor**: {status['test_floor']} / 462 (protected minimum)"
            )
            
            with open(self.dashboard_file, 'w') as f:
                f.write(content)
            
            print(f"✅ Dashboard updated: {self.dashboard_file}")
            print(f"📊 Test floor: {status['test_floor']}")
        else:
            print(f"❌ Dashboard file not found: {self.dashboard_file}")


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description="ADJ System - DGT Engine Governance")
    parser.add_argument("command", choices=["status", "phase", "priorities", "blockers", "next", "approve", "update", "strategy"])
    parser.add_argument("arg", nargs="?", help="Argument for command (phase number, approval target)")
    
    args = parser.parse_args()
    
    adj = ADJSystem()
    
    if args.command == "status":
        adj.show_status()
    elif args.command == "phase":
        if not args.arg:
            print("❌ Phase number required. Use: 1, 2, or 3")
            return
        adj.show_phase(args.arg)
    elif args.command == "priorities":
        adj.show_priorities()
    elif args.command == "blockers":
        adj.show_blockers()
    elif args.command == "next":
        adj.show_next()
    elif args.command == "approve":
        if not args.arg:
            print("❌ Approval target required. Use: phase3")
            return
        adj.approve_phase(args.arg)
    elif args.command == "update":
        adj.update_dashboard()
    elif args.command == "strategy":
        if not args.arg:
            print("❌ Phase number required. Use: 1, 2, or 3")
            return
        adj.show_strategy(args.arg)
    else:
        print("❌ Unknown command")
        parser.print_help()


if __name__ == "__main__":
    main()
