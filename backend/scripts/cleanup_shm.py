import multiprocessing.shared_memory as shared_memory


def cleanup():
    print("Cleaning up Shared Memory segments...", flush=True)
    for name in ["market_data_v2", "trading_intents_v2"]:
        try:
            # Try to attach
            probs_shm = shared_memory.SharedMemory(name=name)
            # If successful, close and unlink
            probs_shm.close()
            probs_shm.unlink()
            print(f"[OK] Unlinked '{name}'", flush=True)
        except FileNotFoundError:
            print(f"[INFO] '{name}' not found (already clean)", flush=True)
        except Exception as e:
            print(f"[ERR] Failed to unlink '{name}': {e}", flush=True)


if __name__ == "__main__":
    cleanup()
