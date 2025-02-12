import cv2
from ultralytics import YOLO
import numpy as np

class GridDetector:
    def __init__(self, model_path):
        self.model = YOLO(model_path)
    
    def process_image(self, game_image):
        model_predictions = self.model(game_image)
        card_detections = []
        
        for prediction_batch in model_predictions:
            image_height, image_width = prediction_batch.orig_img.shape[:2]
            detected_boxes = prediction_batch.boxes
            
            for detected_box in detected_boxes:
                # Extract center coordinates and dimensions
                center_x = detected_box.xywh[0][0].item()
                center_y = detected_box.xywh[0][1].item()
                box_width = detected_box.xywh[0][2].item()
                box_height = detected_box.xywh[0][3].item()
                
                # Convert to grid coordinates (5x5 grid)
                grid_position_x = int((center_x / image_width) * 5)
                grid_position_y = int((center_y / image_height) * 5)
                card_class = int(detected_box.cls[0].item())
                
                # Only add valid grid positions
                if 0 <= grid_position_x < 5 and 0 <= grid_position_y < 5:
                    card_detections.append({
                        'grid_x': grid_position_x,
                        'grid_y': grid_position_y,
                        'class': card_class,
                    })
        
        return card_detections
    
class KeyDetector:
    def __init__(self, model_path):
        self.model = YOLO(model_path)
        self.team_class_mapping = {
            'red': 0,     # Red agent
            'blue': 1,    # Blue agent
            'black': 2,   # Assassin
            'white': 3    # Neutral bystander
        }
    
    def process_key_image(self, key_image_path):
        # Read key image
        key_image = cv2.imread(key_image_path)
        if key_image is None:
            raise ValueError("Could not read key image file")
        
        # Get model predictions for key image
        model_predictions = self.model(key_image)
        
        # Initialize 5x5 grid with neutral positions (3)
        key_position_grid = [[3 for _ in range(5)] for _ in range(5)]
        
        # Collect all valid key positions
        valid_key_positions = []
        for prediction_batch in model_predictions:
            detected_boxes = prediction_batch.boxes
            for detected_box in detected_boxes:
                class_index = int(detected_box.cls[0])
                class_name = self.model.names[class_index]
                confidence_score = float(detected_box.conf[0])
                
                # Only process valid team colors with high confidence
                if class_name in self.team_class_mapping and confidence_score > 0.5:
                    position_x, position_y = detected_box.xywh[0][:2]
                    valid_key_positions.append((
                        float(position_x),
                        float(position_y),
                        class_name,
                        confidence_score
                    ))
        
        # Sort positions by vertical coordinate (rows)
        valid_key_positions.sort(key=lambda pos: pos[1])
        
        # Split into 5 rows
        row_positions = [[] for _ in range(5)]
        positions_per_row = len(valid_key_positions) // 5
        
        # Distribute positions into rows
        for position_index, key_position in enumerate(valid_key_positions):
            row_index = position_index // positions_per_row
            if row_index < 5:  # Ensure we don't exceed grid size
                row_positions[row_index].append(key_position)
        
        # Process each row and assign team colors
        for row_index, row_key_positions in enumerate(row_positions):
            # Sort positions in row by horizontal coordinate
            row_key_positions.sort(key=lambda pos: pos[0])
            
            # Assign team colors to grid positions
            for col_index, (_, _, team_color, _) in enumerate(row_key_positions):
                if col_index < 5:  # Ensure we don't exceed grid size
                    key_position_grid[row_index][col_index] = self.team_class_mapping[team_color]
        
        return key_position_grid