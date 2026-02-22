import sys
from src.tools.apj.journal import Journal

def main():
    journal = Journal()
    
    if len(sys.argv) < 2:
        print("Usage: python -m src.tools.apj [status|update|handoff]")
        return

    cmd = sys.argv[1].lower()

    if cmd == "status":
        print(journal.load())
    
    elif cmd == "handoff":
        print(journal.get_handoff())

    elif cmd == "update":
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
    else:
        print(f"Unknown command: {cmd}")

if __name__ == "__main__":
    main()
