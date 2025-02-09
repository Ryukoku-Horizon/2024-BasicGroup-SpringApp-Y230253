import os

folder = os.path.join("assets", "images")
print("DEBUG: List of files in", folder)
for f in os.listdir(folder):
    print(f)