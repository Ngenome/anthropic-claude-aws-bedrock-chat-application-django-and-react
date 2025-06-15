import os

def directory_to_comma_separated_list(directory_path):
    try:
        # List all files in the specified directory
        items = os.listdir(directory_path)

        # Filter only .svg files and remove the .svg extension
        svg_files = [os.path.splitext(item)[0] for item in items if item.endswith('.svg')]

        # Convert the list of .svg files without extensions to a comma-separated string
        comma_separated_list = ', '.join(svg_files)

        return comma_separated_list
    except FileNotFoundError:
        return "The specified directory does not exist."
    except PermissionError:
        return "Permission denied to access the specified directory."
    except Exception as e:
        return f"An error occurred: {e}"

def write_to_file(file_path, content):
    try:
        with open(file_path, 'w') as file:
            file.write(content)
    except Exception as e:
        print(f"An error occurred while writing to the file: {e}")

# Example usage:
if __name__ == "__main__":
    directory_path = input("Enter the path of the directory: ")
    result = directory_to_comma_separated_list(directory_path)

    if "An error occurred" in result or "The specified directory does not exist" in result or "Permission denied" in result:
        print(result)
    else:
        file_path = 'contents.txt'
        write_to_file(file_path, result)
        print(f"The .svg files (without extensions) in the directory have been written to {file_path}")
