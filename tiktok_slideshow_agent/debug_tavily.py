try:
    import langchain_tavily
    print("langchain_tavily found.")
    print("Attributes:", dir(langchain_tavily))
except ImportError as e:
    print(f"Error importing langchain_tavily: {e}")
except Exception as e:
    print(f"Other error: {e}")
