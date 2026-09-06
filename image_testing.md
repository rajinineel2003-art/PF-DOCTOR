# Image Integration Test Protocol

Testing agents validating PF Doctor Vision OCR must follow these rules:

- Use base64-encoded images for integration tests and requests.
- Accepted formats are JPEG, PNG, and WEBP only.
- Do not use SVG, BMP, HEIC, or other formats.
- Do not upload blank, solid-color, or uniform-variance images.
- Every image must contain real visual features such as text, edges, textures, or shadows.
- Transcode unsupported formats to PNG or JPEG before upload.
- Re-detect and update the MIME type after every conversion or compression.
- For animated GIF, APNG, or WEBP, extract the first frame only.
- Resize large images to reasonable dimensions before testing.
- A Vision test passes only when the backend actually inspects the image and returns extracted text; predefined or injected OCR text is prohibited.