
def extract_connected_traceback(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            
        # Find the last occurrence of "Traceback"
        last_traceback_idx = -1
        for i, line in enumerate(lines):
            if "Traceback (most recent call last)" in line:
                last_traceback_idx = i
                
        if last_traceback_idx != -1:
            print(f"Found traceback at line {last_traceback_idx + 1}")
            # Print up to 50 lines after
            for j in range(last_traceback_idx, min(last_traceback_idx + 50, len(lines))):
                print(lines[j], end='')
        else:
            print("No traceback found.")
            # Print last 20 lines just in case
            print("\nLast 20 lines:")
            for line in lines[-20:]:
                print(line, end='')
                
    except Exception as e:
        print(f"Error reading file: {e}")

if __name__ == "__main__":
    extract_connected_traceback("debug_api_logs.txt")
