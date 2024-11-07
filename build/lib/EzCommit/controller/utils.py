import os

def find_or_create_readme():
    # Find the root of the repository
    repo_root = find_repo_root()
    if not repo_root:
        print("Repository root not found.")
        return None

    # Define the path for README.md in the repository root
    readme_path = os.path.join(repo_root, "README.md")
    
    # Check if README.md exists, and create it if not
    if not os.path.exists(readme_path):
        with open(readme_path, "w") as file:
            file.write("# New README\n\nThis README file was created automatically.\n")
        print(f"README.md file created at: {readme_path}")
    else:
        print(f"README.md already exists at: {readme_path}")
    
    return readme_path

def find_repo_root(start_path="."):
    current_path = os.path.abspath(start_path)
    
    # Traverse upward until a .git folder is found or root directory is reached
    while current_path != os.path.dirname(current_path):
        if os.path.isdir(os.path.join(current_path, ".git")):
            return current_path
        current_path = os.path.dirname(current_path)
    
    return None

def path_to_readme():
    readme_path = find_or_create_readme()
    if readme_path:
        print(f"Path to README.md: {readme_path}")
        return readme_path
    else:
        print("Failed to create README.md file.")
    
if __name__ == "__main__":
    pass