from PIL import Image
from pathlib import Path

def convert_dds_to_png(dds_file, png_file):
    """Converts a DDS file to a PNG file.

    Args:
        dds_file: The path to the DDS file.
        png_file: The path to the PNG file.
    """

    image = Image.open(dds_file)
    output_dir = Path.cwd() / "PNG_Images"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / Path(png_file).name  # Use only the filename for saving
    image.save(output_path, "PNG")

if __name__ == "__main__":
    folder_path = Path("SummonedImages")
    file_list = list(folder_path.glob("*"))

    for file_path in file_list:
        dds_file = str(file_path)
        root_name = file_path.stem  # Use the stem of the file (filename without extension)
        png_file = f"{root_name}.png"
        png_file = png_file.replace(" ", "")

        print("DDS File:", dds_file)
        print("PNG File:", png_file)

        convert_dds_to_png(dds_file, png_file)

    print("The DDS files have been converted to PNG files.")
    print("The PNG files are located in the PNG_Images directory.")
