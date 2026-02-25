import sys
import argparse
from loguru import logger
from src.tools.apj.journal import Journal


def _run_session_start() -> None:
    """Run the Archivist and print the Coherence Report to the console."""
    from src.tools.apj.agents.archivist import Archivist

    print("\n[*] APJ Archivist initializing...\n")
    archivist = Archivist(model_name="llama3.2:3b")
    report = archivist.run()

    # Print structured report to console
    print("=" * 60)
    print("  ARCHIVIST COHERENCE REPORT")
    print("=" * 60)

    print("\n📋 SESSION PRIMER")
    print(f"  {report.session_primer}")

    print("\n🎯 QUEUED FOCUS")
    print(f"  → {report.queued_focus}")

    if report.open_risks:
        print("\n⚠  OPEN RISKS")
        for risk in report.open_risks:
            print(f"  • {risk}")
    else:
        print("\n✅ OPEN RISKS — None detected.")

    if report.constitutional_flags:
        print("\n🚨 CONSTITUTIONAL FLAGS")
        for flag in report.constitutional_flags:
            print(f"  ⚠️  {flag}")
    else:
        print("\n✅ CONSTITUTIONAL FLAGS — No violations detected.")

    print(f"\n🔑 Corpus hash: {report.corpus_hash[:16]}...")
    print("=" * 60)
    print("  Session log saved to docs/session_logs/")
    print("=" * 60 + "\n")


def main():
    journal = Journal()

    if len(sys.argv) < 2:
        print("Usage: python -m src.tools.apj [status|update|handoff|boot|tasks|goals|milestones|session]")
        return

    cmd = sys.argv[1].lower()

    if cmd == "status":
        print(journal.load())
    
    elif cmd == "handoff":
        print(journal.get_handoff())
        
    elif cmd == "boot":
        print(journal.get_boot_block())

    elif cmd == "goals":
        content = journal.load(journal.goals_path)
        print(content)

    elif cmd == "milestones":
        parser = argparse.ArgumentParser(description="rpgCore APJ Milestones")
        parser.add_argument("command") # consume 'milestones'
        parser.add_argument("--done", help="Mark a milestone as completed (matches text)")
        
        args, _ = parser.parse_known_args()
        
        if args.done:
            success = journal.complete_milestone(args.done)
            if success:
                print(f"Milestone matching '{args.done}' moved to Completed.")
            else:
                print(f"Milestone matching '{args.done}' not found.")
        else:
            content = journal.load(journal.milestones_path)
            print(content)

    elif cmd == "tasks":
        parser = argparse.ArgumentParser(description="rpgCore APJ Tasks")
        parser.add_argument("command") # consume 'tasks'
        parser.add_argument("--next", action="store_true", help="Print top 5 queued tasks")
        parser.add_argument("--add", help="Add a new task to Queued section")
        parser.add_argument("--done", help="Mark a task as completed (matches text)")
        
        args, _ = parser.parse_known_args()
        
        if args.next:
            print("QUEUED TASKS (top 5):")
            print(journal.get_next_tasks(5))
        elif args.add:
            journal.add_task(args.add)
            print(f"Added task: {args.add}")
        elif args.done:
            success = journal.complete_task(args.done)
            if success:
                print(f"Task matching '{args.done}' moved to Completed.")
            else:
                print(f"Task matching '{args.done}' not found.")
        else:
            # Print full TASKS.md
            content = journal.load(journal.tasks_path)
            print(content)

    elif cmd == "update":
        # Use argparse for update flags
        parser = argparse.ArgumentParser(description="rpgCore APJ Update")
        parser.add_argument("command") # consume 'update'
        parser.add_argument("--current", help="New content for Current State")
        parser.add_argument("--inflight", help="New content for In Flight")
        parser.add_argument("--next", help="New content for Next Priority")
        
        args, _ = parser.parse_known_args()
        
        # Mapping for flags to section names
        flag_map = {
            "current": ("Current State", args.current),
            "inflight": ("In Flight", args.inflight),
            "next": ("Next Priority", args.next)
        }
        
        # If any flags provided, skip interactive loop
        if any([args.current, args.inflight, args.next]):
            for section_key in ["current", "inflight", "next"]:
                name, content = flag_map[section_key]
                if content:
                    journal.update_section(name, content)
                    print(f"Section '{name}' updated via flag.")
            return

        # Interactive Mode fallback
        sections = ["Current State", "In Flight", "Next Priority"]
        for section in sections:
            current = journal.get_section(section)
            print(f"\n--- {section} ---")
            print(current)
            
            choice = input(f"\nUpdate '{section}'? (y/n): ").lower()
            if choice == 'y':
                print("Enter new content (type 'DONE' on a new line to finish):")
                lines = []
                while True:
                    line = sys.stdin.readline()
                    if line.strip() == "DONE":
                        break
                    lines.append(line)
                
                new_content = "".join(lines)
                journal.update_section(section, new_content)
                print(f"Section '{section}' updated.")
    elif cmd == "session":
        sub = sys.argv[2].lower() if len(sys.argv) > 2 else ""
        if sub == "start":
            _run_session_start()
        elif sub == "end":
            print("Scribe not yet implemented (v3). Session end recorded.")
            logger.info("APJ: session end stub invoked (Scribe v3 pending)")
        else:
            print("Usage: python -m src.tools.apj session [start|end]")

    else:
        print(f"Unknown command: {cmd}")

if __name__ == "__main__":
    main()
