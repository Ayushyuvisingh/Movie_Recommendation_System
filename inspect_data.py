import pickle

file_path = "data/movie_dict.pkl"

with open(file_path, "rb") as f:
    data = pickle.load(f)

print("TYPE:", type(data))
print("KEYS:", data.keys())
print()

for key, value in data.items():
    print(f"--- {key} ---")
    print("TYPE:", type(value))
    
    if hasattr(value, "__len__"):
        print("LENGTH:", len(value))

    if isinstance(value, dict):
        print("FIRST 3:")
        for item in list(value.items())[:3]:
            print(item)
    else:
        print("FIRST 3:", value[:3])

    print()