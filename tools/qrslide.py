import qrcode
import qrcode.image.svg
import os

def generate_qr_code(text, filepath="qrcode.svg"):
    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(text)
    qr.make(fit=True)

    # Create an SVG image
    factory = qrcode.image.svg.SvgPathImage
    img = qr.make_image(fill_color="black", back_color="white", image_factory=factory)

    # Ensure the filepath has .svg extension
    if not filepath.lower().endswith('.svg'):
        filepath += '.svg'

    # Save the image
    img.save(filepath)

    # Get the absolute filepath
    absolute_filepath = os.path.abspath(filepath)

    return absolute_filepath

if __name__ == "__main__":
    generate_qr_code("https://github.com/octaflop/new-year-new-data")

# Example usage
# text_to_encode = "https://example.com"
# result_filepath = generate_qr_code(text_to_encode)
# print(f"QR code saved at: {result_filepath}")
