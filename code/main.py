import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import cv2
import threading
import queue
from ui_components import GameGrid, KeyGrid
from ocr_handler import OCRHandler
from yolo import GridDetector, KeyDetector

class CodeNamesApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CodeNames Game")
        
        # Initialize role and team variables
        self.role = None
        self.team = None
        
        # Show role selection first
        self.show_role_selection()
    
    def show_role_selection(self):
        # Clear existing widgets
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Create role selection frame
        frame = tk.Frame(self.root, padx=20, pady=20)
        frame.pack(expand=True)
        
        tk.Label(frame, text="Select your role:", font=('Arial', 14, 'bold')).pack(pady=10)
        
        role_var = tk.StringVar(value="field_agent")
        tk.Radiobutton(frame, text="Field Agent", variable=role_var, value="field_agent", font=('Arial', 12)).pack()
        tk.Radiobutton(frame, text="Spymaster", variable=role_var, value="spymaster", font=('Arial', 12)).pack()
        
        tk.Label(frame, text="Select your team:", font=('Arial', 14, 'bold')).pack(pady=(20,10))
        
        team_var = tk.StringVar(value="blue")
        tk.Radiobutton(frame, text="Blue Team", variable=team_var, value="blue", font=('Arial', 12)).pack()
        tk.Radiobutton(frame, text="Red Team", variable=team_var, value="red", font=('Arial', 12)).pack()
        
        tk.Button(frame, text="Continue", 
                 command=lambda: self.handle_role_selection(role_var.get(), team_var.get()),
                 font=('Arial', 12, 'bold')).pack(pady=20)
    
    def handle_role_selection(self, role, team):
        self.role = role
        self.team = team
        
        if role == "spymaster":
            self.show_key_selection()
        else:
            self.initialize_game()
    
    def show_key_selection(self):
        # Clear existing widgets
        for widget in self.root.winfo_children():
            widget.destroy()
        
        frame = tk.Frame(self.root, padx=20, pady=20)
        frame.pack(expand=True)
        
        tk.Label(frame, text="Please select the key image:", font=('Arial', 14, 'bold')).pack(pady=10)
        
        tk.Button(frame, text="Load Key Image", 
                 command=self.load_key_image,
                 font=('Arial', 12, 'bold')).pack(pady=20)


    def load_key_image(self):
        file_path = filedialog.askopenfilename(
            title="Select Key Image",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.gif")]
        )
        
        if file_path:
            try:
                # Process key image
                key_detector = KeyDetector("models/key_model.pt")
                key_grid_values = key_detector.process_key_image(file_path)
                
                self.initialize_game(key_grid_values)
            except Exception as e:
                print(f"Error processing key image: {e}")
                tk.messagebox.showerror("Error", "Could not process key image. Please try again.")
    
    def initialize_game(self, key_grid_values=None):
        # Clear existing widgets
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Initialize components
        self.detector = GridDetector("models/grid_model.pt")
        self.ocr = OCRHandler()
        
        # Create info frame at the top
        info_frame = tk.Frame(self.root, pady=10)
        info_frame.pack(fill=tk.X)
        
        # Create role and team info with box
        role_text = "Spymaster" if self.role == "spymaster" else "Field Agent"
        team_color = "#ff4444" if self.team == "red" else "#4444ff"

        team_frame = tk.Frame(info_frame, bg=team_color, padx=10, pady=5)
        team_frame.pack(side=tk.LEFT)
        tk.Label(team_frame, text=f"Team: {self.team.upper()}", 
                font=('Arial', 12, 'bold'), 
                fg='white', 
                bg=team_color).pack()
        
        tk.Label(info_frame, text=f"Role: {role_text}", font=('Arial', 12, 'bold')).pack(side=tk.LEFT, padx=20)
        
        
        # Create main game frame
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(expand=True)
        
        # Create frame for video display on the left
        self.video_frame = tk.Frame(self.main_frame)
        self.video_frame.pack(side=tk.LEFT, padx=10, pady=10)
        
        self.video_label = tk.Label(self.video_frame)
        self.video_label.pack()
        
        # Create right panel for grids
        self.right_panel = tk.Frame(self.main_frame)
        self.right_panel.pack(side=tk.RIGHT, padx=10, pady=10)
        
        # Create game grid
        self.grid = GameGrid(self.right_panel)
        
        # If spymaster, create and show key grid
        if self.role == "spymaster" and key_grid_values:
            self.key_grid = KeyGrid(self.right_panel)
            # Update key grid with values
            for y in range(5):
                for x in range(5):
                    self.key_grid.update_cell(x, y, key_grid_values[y][x])
        
        # Initialize video processing variables
        self.cap = None
        self.processing_thread = None
        self.is_running = False
        self.frame_queue = queue.Queue(maxsize=1)
        self.detection_queue = queue.Queue(maxsize=1)
        
        # Tracking variables for card changes
        self.change_tracking = {}
        self.CHANGE_THRESHOLD = 3
        self.FRAMES_TO_SKIP = 5
        self.frame_count = 0
        
        # Start the game
        self.start_game()
    
    def start_game(self):
        self.cap = cv2.VideoCapture("resources/game_video.mp4") # Source video file 
        ret, frame = self.cap.read()
        if ret:
            self.initialize_grid_with_cards(frame)
            self.start_video_processing()
        else:
            print("Error: Could not read initial frame")
    
    def initialize_grid_with_cards(self, frame):
        results = self.detector.model(frame)
        
        for result in results:
            img_height, img_width = result.orig_img.shape[:2]
            boxes = result.boxes
            
            for box in boxes:
                x = box.xywh[0][0].item()
                y = box.xywh[0][1].item()
                w = box.xywh[0][2].item()
                h = box.xywh[0][3].item()
                
                x1 = x - w/2
                y1 = y - h/2
                x2 = x + w/2
                y2 = y + h/2
                
                grid_x = int((x / img_width) * 5)
                grid_y = int((y / img_height) * 5)
                
                if 0 <= grid_x < 5 and 0 <= grid_y < 5:
                    text = self.ocr.get_card_text(frame, [x1, y1, x2, y2])
                    if text:
                        self.grid.update_cell(grid_x, grid_y, 0, text)
    
    def start_video_processing(self):
        self.is_running = True
        self.processing_thread = threading.Thread(target=self.process_video)
        self.processing_thread.daemon = True
        self.processing_thread.start()
        self.update_ui()
    
    def process_video(self):
        while self.is_running:
            ret, frame = self.cap.read()
            if not ret:
                break
            
            self.frame_count += 1
            
            # Convert frame for display
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            if not self.frame_queue.full():
                self.frame_queue.put(rgb_frame)
            
            # Skip YOLO processing for smoother video
            if self.frame_count % (self.FRAMES_TO_SKIP + 1) != 0:
                continue
            
            # Process frame with YOLO (but don't use for display)
            results = self.detector.model(frame)
            
            # Process detections
            detections = []
            for result in results:
                img_height, img_width = result.orig_img.shape[:2]
                boxes = result.boxes
                
                for box in boxes:
                    x = box.xywh[0][0].item()
                    y = box.xywh[0][1].item()
                    
                    grid_x = int((x / img_width) * 5)
                    grid_y = int((y / img_height) * 5)
                    cls = int(box.cls[0].item())
                    
                    if 0 <= grid_x < 5 and 0 <= grid_y < 5:
                        detections.append({
                            'grid_x': grid_x,
                            'grid_y': grid_y,
                            'class': cls
                        })
            
            # Update queues
            if not self.frame_queue.full():
                self.frame_queue.put(rgb_frame)
            if not self.detection_queue.full():
                self.detection_queue.put(detections)
    
    def update_ui(self):
        try:
            # Update video frame
            if not self.frame_queue.empty():
                frame = self.frame_queue.get_nowait()
                image = Image.fromarray(frame)
                display_size = (640, 480)
                image = image.resize(display_size, Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(image=image)
                self.video_label.config(image=photo)
                self.video_label.image = photo
            
            # Update grid with detections
            if not self.detection_queue.empty():
                detections = self.detection_queue.get_nowait()
                
                # Process each detection
                for detection in detections:
                    grid_key = f"{detection['grid_x']},{detection['grid_y']}"
                    current_type = self.grid.get_cell_type(detection['grid_x'], detection['grid_y'])
                    new_type = detection['class']
                    
                    # Skip if no change
                    if current_type == new_type:
                        if grid_key in self.change_tracking:
                            del self.change_tracking[grid_key]
                        continue
                    
                    # Initialize or update change tracking
                    if grid_key not in self.change_tracking:
                        self.change_tracking[grid_key] = {
                            'new_type': new_type,
                            'count': 1,
                            'x': detection['grid_x'],
                            'y': detection['grid_y']
                        }
                    else:
                        track = self.change_tracking[grid_key]
                        if track['new_type'] == new_type:
                            track['count'] += 1
                        else:
                            # Reset if detected type changed
                            track['new_type'] = new_type
                            track['count'] = 1
                
                # Check for confirmed changes
                confirmed_changes = []
                keys_to_remove = []
                
                for grid_key, track in self.change_tracking.items():
                    if track['count'] >= self.CHANGE_THRESHOLD:
                        confirmed_changes.append(track)
                        keys_to_remove.append(grid_key)
                
                # Apply confirmed changes
                for change in confirmed_changes:
                    self.grid.update_cell(
                        change['x'],
                        change['y'],
                        change['new_type']
                    )
                
                # Clean up confirmed changes
                for key in keys_to_remove:
                    del self.change_tracking[key]
                
        except Exception as e:
            print(f"Error updating UI: {e}")
        
        if self.is_running:
            self.root.after(1, self.update_ui)
    
    def on_closing(self):
        self.is_running = False
        if self.cap is not None:
            self.cap.release()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = CodeNamesApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()