import tkinter as tk
from PIL import Image, ImageTk

class GameGrid:
    def __init__(self, root):
        self.frame = tk.Frame(root)
        self.frame.pack(pady=10, padx=10)
        
        # Load and resize card images
        cell_width, cell_height = 140, 90
        self.card_images = self._load_card_images(cell_width, cell_height)
        
        self.CARD_TYPES = {
            0: {"type": "color", "value": "#FFF"},                      # Codename card
            1: {"type": "image", "value": self.card_images["red"]},     # Red agent
            2: {"type": "image", "value": self.card_images["blue"]},    # Blue agent
            3: {"type": "image", "value": self.card_images["neutral"]}, # Neutral bystander
            4: {"type": "image", "value": self.card_images["assassin"]} # Assassin
        }
        
        self.cells = []
        self.cell_states = {}
        self._initialize_grid(cell_width, cell_height)

    def _load_card_images(self, width, height):
        images = {
            "red": Image.open("resources/red_agent.png"),
            "blue": Image.open("resources/blue_agent.png"),
            "assassin": Image.open("resources/assassin.png"),
            "neutral": Image.open("resources/innocent_bystander.png")
        }
        return {key: ImageTk.PhotoImage(img.resize((width, height))) 
                for key, img in images.items()}

    def _initialize_grid(self, cell_width, cell_height):
        for row in range(5):
            cell_row = []
            for col in range(5):
                cell = GridCell(self.frame, width=cell_width, height=cell_height)
                cell.frame.grid(row=row, column=col, padx=2, pady=2)
                cell.frame.grid_propagate(False)
                cell_row.append(cell)
                self.cell_states[f"{col},{row}"] = {"type": 0, "text": ""}
            self.cells.append(cell_row)

    def get_cell_type(self, x, y):
        return self.cell_states[f"{x},{y}"]["type"]
    
    def update_cell(self, x, y, card_type, text=None):
        cell = self.cells[y][x]
        cell_state = self.cell_states[f"{x},{y}"]
        
        if text is not None:
            cell_state["text"] = text
        cell_state["type"] = card_type
        
        card_style = self.CARD_TYPES[card_type]
        cell.reset_appearance()
        
        if card_style["type"] == "color":
            cell.set_color_background(card_style["value"])
        else:
            cell.set_image_background(card_style["value"])
        
        if card_type == 0 and cell_state["text"]:
            cell.set_text(cell_state["text"].upper())

class GridCell:
    def __init__(self, parent, width, height):
        self.frame = tk.Frame(
            parent,
            width=width,
            height=height,
            bg='white',
            relief='solid',
            borderwidth=1
        )
        
        self.label = tk.Label(
            self.frame,
            text="",
            wraplength=width-20,
            justify='center',
            bg='white',
            font=('Arial', 12, 'bold')
        )
        self.label.place(relx=0.5, rely=0.5, anchor='center')
    
    def set_color_background(self, color):
        self.frame.configure(bg=color)
        self.label.configure(bg=color)
    
    def set_image_background(self, image):
        self.label.configure(image=image)
        self.label.place(relx=0, rely=0, relwidth=1, relheight=1, anchor='nw')
    
    def set_text(self, text, color='black'):
        self.label.configure(text=text, fg=color)
    
    def reset_appearance(self):
        self.label.configure(image='', text='')
        self.label.place(relx=0.5, rely=0.5, anchor='center')

class KeyGrid:
    TEAM_COLORS = {
        0: "#FF4444",   # Red team
        1: "#4444FF",   # Blue team
        2: "#000000",   # Assassin
        3: "#CCCCCC"    # Neutral
    }

    def __init__(self, parent):
        self.frame = tk.Frame(parent)
        self.frame.pack(pady=(0, 10))
        
        self.title = tk.Label(self.frame, text="Key Grid", font=('Arial', 12, 'bold'))
        self.title.pack(pady=(0, 5))
        
        self.grid_frame = tk.Frame(self.frame)
        self.grid_frame.pack()
        
        cell_width, cell_height = 90, 60
        self.cells = self._create_key_grid(cell_width, cell_height)
    
    def _create_key_grid(self, cell_width, cell_height):
        cells = []
        for row in range(5):
            cell_row = []
            for col in range(5):
                cell = GridCell(self.grid_frame, width=cell_width, height=cell_height)
                cell.frame.grid(row=row, column=col, padx=1, pady=1)
                cell.frame.grid_propagate(False)
                cell_row.append(cell)
            cells.append(cell_row)
        return cells
    
    def update_cell(self, x, y, cell_type):
        if not (0 <= x < 5 and 0 <= y < 5):
            return
            
        cell = self.cells[y][x]
        color = self.TEAM_COLORS[cell_type]
        
        cell.reset_appearance()
        cell.set_color_background(color)
        
        # Set indicator text color based on background
        text_color = 'white' if cell_type in [0, 1, 2] else 'black'
        cell.label.configure(fg=text_color, font=('Arial', 14, 'bold'))