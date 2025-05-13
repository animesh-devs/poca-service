import uvicorn
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the POCA service")
    parser.add_argument("--port", type=int, default=8000, help="Port to run the service on")
    args = parser.parse_args()

    try:
        uvicorn.run("app.main:app", host="0.0.0.0", port=args.port, reload=True)
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"Port {args.port} is already in use. Try a different port with --port.")
            # Try a different port automatically
            for port in range(8001, 8100):
                try:
                    print(f"Trying port {port}...")
                    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
                    break
                except OSError:
                    continue
        else:
            raise
