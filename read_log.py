try:
    with open("monitor.log", "r", encoding="utf-8", errors="replace") as f_in, open(
        "filtered_log.txt", "w", encoding="utf-8"
    ) as f_out:
        for line in f_in:
            f_out.write(line)

    print("Log filtered successfully to filtered_log.txt")
except Exception as e:
    print(f"Error filtering log: {e}")
