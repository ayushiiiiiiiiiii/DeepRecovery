
file_path = "input/testfile.txt"

with open(file_path, "rb") as file:
    
    data = file.read()

    print("File opened successfully!")
    print("File content:")
    print(data)