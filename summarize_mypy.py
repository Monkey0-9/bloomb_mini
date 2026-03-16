import sys

def summarize_mypy(file_path):
    errors = {}
    with open(file_path, 'r', encoding='utf-16') as f:
        for line in f:
            if ': error:' in line:
                parts = line.split(':')
                file = parts[0]
                error = ':'.join(parts[3:]).strip()
                if file not in errors:
                    errors[file] = []
                errors[file].append(error)
    
    for file, file_errors in sorted(errors.items()):
        print(f"\n{file} ({len(file_errors)} errors):")
        for e in file_errors[:5]:
            print(f"  - {e}")
        if len(file_errors) > 5:
            print(f"  - ... and {len(file_errors) - 5} more")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        summarize_mypy(sys.argv[1])
