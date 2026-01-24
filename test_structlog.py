try:
    import structlog
    print("SUCCESS: structlog is installed")
except ImportError as e:
    print(f"FAILURE: {e}")
except Exception as e:
    print(f"ERROR: {e}")
