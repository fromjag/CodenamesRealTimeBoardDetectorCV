import easyocr

class OCRHandler:
    def __init__(self):
        # Initialize OCR reader with English language
        self.reader = easyocr.Reader(['en'])
    
    def get_card_text(self, image, bbox):
        """
        Extracts text from a card within the specified bounding box.
        Returns the most prominent text found or empty string if none detected.
        """
        try:
            # Ensure bbox coordinates are within image boundaries
            x1, y1, x2, y2 = bbox
            height, width = image.shape[:2]
            
            safe_bbox = (
                max(0, int(x1)),
                max(0, int(y1)),
                min(width, int(x2)),
                min(height, int(y2))
            )
            
            # Extract the card region and perform OCR
            card_region = image[safe_bbox[1]:safe_bbox[3], safe_bbox[0]:safe_bbox[2]]
            detected_text = self.reader.readtext(card_region)
            
            if detected_text:
                # Sort by vertical position and confidence, return highest confidence text
                detected_text.sort(key=lambda x: (x[0][0][1], x[2]), reverse=True)
                return detected_text[0][1]
                
        except Exception as e:
            print(f"OCR Error: {e}")
            
        return ""