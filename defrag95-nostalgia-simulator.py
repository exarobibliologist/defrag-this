import pygame
import random
import sys

# --- CONFIGURATION & COLORS ---
CELL_SIZE = 8  
FPS = 60
UI_HEIGHT = 60 

# Grid Color Palette
COLOR_BG = (0, 0, 0)                 
COLOR_UNFRAGMENTED = (91, 91, 255)   
COLOR_FRAGMENTED = (255, 0, 0)      
COLOR_EMPTY = (25, 25, 25)           
COLOR_READING = (255, 255, 0)        
COLOR_WRITING = (0, 255, 0)          
COLOR_SYSTEM = (128, 0, 128)         

# UI Color Palette
COLOR_UI_BG = (30, 30, 30)
COLOR_BTN = (70, 70, 70)
COLOR_BTN_HOVER = (100, 100, 100)
COLOR_TEXT = (255, 255, 255)
COLOR_INPUT_INACTIVE = (50, 50, 50)
COLOR_INPUT_ACTIVE = (200, 200, 200)
COLOR_INPUT_TEXT_ACTIVE = (0, 0, 0)

# --- CORE APPLICATION ---
class DefragVisualizer:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        pygame.mouse.set_visible(True) 
        
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN | pygame.DOUBLEBUF)
        self.width, self.height = self.screen.get_size()
        
        self.cols = self.width // CELL_SIZE
        self.rows = (self.height - UI_HEIGHT) // CELL_SIZE 
        self.total_cells = self.cols * self.rows
        
        self.font = pygame.font.SysFont("consolas", 15, bold=True)
        self.linear_grid = []
        self.clock = pygame.time.Clock()
        
        # UI State Variables
        self.delay_ms = 1000
        self.speed_text = str(self.delay_ms)
        self.input_speed_active = False
        
        self.frag_percent = 25 
        self.frag_text = str(self.frag_percent)
        self.input_frag_active = False
        
        # Defrag State Variables
        self.is_defragging = False
        self.state = "FIND_TARGETS"
        self.write_index = 0
        self.last_action_time = 0
        
        # Screensaver State Variables
        self.done_time = 0
        self.restart_delay_ms = 60000 
        
        self.active_reads = []
        self.active_writes = []
        
        # Fixed UI Element Coordinates 
        ui_y = self.height - UI_HEIGHT + 10
        self.btn_randomize = pygame.Rect(20, ui_y, 140, 40)
        self.btn_start = pygame.Rect(170, ui_y, 140, 40)
        self.input_frag = pygame.Rect(440, ui_y, 60, 40) 
        self.input_speed = pygame.Rect(660, ui_y, 60, 40) 
        
        self.generate_seed()

    def generate_seed(self):
        self.linear_grid = []
        self.is_defragging = False
        self.state = "FIND_TARGETS"
        self.write_index = 0
        self.last_action_time = 0
        self.done_time = 0  
        self.active_reads = []
        self.active_writes = []
        
        while len(self.linear_grid) < self.total_cells:
            state_choice = random.choices(
                [COLOR_EMPTY, COLOR_UNFRAGMENTED, COLOR_FRAGMENTED], 
                weights=[35, 55, 10], k=1)[0]
            
            if state_choice == COLOR_UNFRAGMENTED:
                chunk_size = random.randint(20, 150) 
            elif state_choice == COLOR_EMPTY:
                chunk_size = random.randint(5, 80)   
            else:
                chunk_size = random.randint(1, 10)   
                
            self.linear_grid.extend([state_choice] * chunk_size)
            
        self.linear_grid = self.linear_grid[:self.total_cells]
        
        chaos_chance = self.frag_percent / 100.0
        
        for i in range(self.total_cells):
            if random.random() < chaos_chance: 
                self.linear_grid[i] = random.choices([COLOR_FRAGMENTED, COLOR_EMPTY], weights=[80, 20])[0]
            elif random.random() < 0.005:
                self.linear_grid[i] = COLOR_SYSTEM

    def defrag_step(self):
        if not self.is_defragging:
            return

        current_time = pygame.time.get_ticks()

        # Screensaver Restart Trigger
        if self.state == "DONE":
            if current_time - self.done_time >= self.restart_delay_ms:
                self.generate_seed()
                self.is_defragging = True 
            return

        if current_time - self.last_action_time < self.delay_ms:
            return

        prev_state = self.state

        if self.state == "FIND_TARGETS":
            while self.write_index < self.total_cells and self.linear_grid[self.write_index] in [COLOR_UNFRAGMENTED, COLOR_SYSTEM]:
                self.write_index += 1
                
            if self.write_index >= self.total_cells:
                self.state = "DONE"
                
            else:
                # BRANCH A: IN-PLACE HEALING (For Fragmented Data)
                if self.linear_grid[self.write_index] == COLOR_FRAGMENTED:
                    chunk_len = random.randint(1, 10)
                    self.active_reads = []
                    self.active_writes = []
                    
                    temp_idx = self.write_index
                    for _ in range(chunk_len):
                        if temp_idx < self.total_cells and self.linear_grid[temp_idx] == COLOR_FRAGMENTED:
                            self.active_reads.append(temp_idx)
                            self.active_writes.append(temp_idx) 
                            temp_idx += 1
                        else:
                            break
                            
                    if self.active_reads:
                        self.state = "READING"
                
                # BRANCH B: GAP FILLING (Scatter-Gather Logic)
                else:
                    chunk_len = random.randint(2, 22)
                    self.active_reads = []
                    self.active_writes = []
                    
                    # 1. Map out the empty gap we want to fill
                    temp_write = self.write_index
                    for _ in range(chunk_len):
                        if temp_write < self.total_cells and self.linear_grid[temp_write] == COLOR_EMPTY:
                            self.active_writes.append(temp_write)
                            temp_write += 1
                        else:
                            break
                            
                    actual_chunk_len = len(self.active_writes)
                    
                    if actual_chunk_len > 0:
                        # 2. True Random Scatter Hunt: Search the entire remaining drive and sample randomly
                        if random.random() < 0.8:
                            # Map out every single fragmented block left on the drive
                            available_fragments = [i for i in range(self.write_index + 1, self.total_cells) 
                                                   if self.linear_grid[i] == COLOR_FRAGMENTED]
                            
                            # If there are any, pick them at random instead of sequentially
                            if available_fragments:
                                num_to_grab = min(actual_chunk_len, len(available_fragments))
                                self.active_reads = random.sample(available_fragments, num_to_grab)
                                self.active_reads.sort() # Sort indices so we process them cleanly
                                
                        # 3. Contiguous Fallback: If no red blocks found (or hit the 20% chance), pull next available data forward
                        if not self.active_reads:
                            temp_read = self.write_index + 1
                            while temp_read < self.total_cells and self.linear_grid[temp_read] in [COLOR_EMPTY, COLOR_SYSTEM]:
                                temp_read += 1
                                
                            if temp_read < self.total_cells:
                                while temp_read < self.total_cells and len(self.active_reads) < actual_chunk_len:
                                    if self.linear_grid[temp_read] not in [COLOR_EMPTY, COLOR_SYSTEM]:
                                        self.active_reads.append(temp_read)
                                        temp_read += 1
                                    else:
                                        break
                                        
                        # Trim writes to match exactly how many reads we successfully secured
                        self.active_writes = self.active_writes[:len(self.active_reads)]
                        
                        if self.active_reads:
                            self.state = "READING"
                        else:
                            self.state = "DONE" 

        elif self.state == "READING":
            for idx in self.active_reads:
                self.linear_grid[idx] = COLOR_READING
            self.state = "WRITING"
            self.last_action_time = current_time 

        elif self.state == "WRITING":
            for idx in self.active_reads:
                if idx not in self.active_writes:
                    self.linear_grid[idx] = COLOR_EMPTY
                    
            for idx in self.active_writes:
                self.linear_grid[idx] = COLOR_WRITING
                
            self.state = "CLEANUP"
            self.last_action_time = current_time 

        elif self.state == "CLEANUP":
            for idx in self.active_writes:
                self.linear_grid[idx] = COLOR_UNFRAGMENTED
            
            # Only track the write_index going forward to prevent skipping bugs
            self.write_index = self.active_writes[-1] + 1
            
            self.state = "FIND_TARGETS"
            self.last_action_time = current_time
            
        # Completion Tracker
        if prev_state != "DONE" and self.state == "DONE":
            self.done_time = current_time

    def draw_text_center(self, text, rect, color):
        text_surface = self.font.render(text, True, color)
        text_rect = text_surface.get_rect(center=rect.center)
        self.screen.blit(text_surface, text_rect)

    def draw_ui(self):
        pygame.draw.rect(self.screen, COLOR_UI_BG, (0, self.height - UI_HEIGHT, self.width, UI_HEIGHT))
        
        mouse_pos = pygame.mouse.get_pos()
        
        color_rand = COLOR_BTN_HOVER if self.btn_randomize.collidepoint(mouse_pos) else COLOR_BTN
        pygame.draw.rect(self.screen, color_rand, self.btn_randomize, border_radius=5)
        self.draw_text_center("Randomize", self.btn_randomize, COLOR_TEXT)
        
        color_start = COLOR_BTN_HOVER if self.btn_start.collidepoint(mouse_pos) else COLOR_BTN
        pygame.draw.rect(self.screen, color_start, self.btn_start, border_radius=5)
        self.draw_text_center("Start Defrag", self.btn_start, COLOR_TEXT)
        
        label_frag = self.font.render("Frag %:", True, COLOR_TEXT)
        self.screen.blit(label_frag, (self.input_frag.x - 85, self.input_frag.y + 10))
        
        frag_bg = COLOR_INPUT_ACTIVE if self.input_frag_active else COLOR_INPUT_INACTIVE
        frag_text_color = COLOR_INPUT_TEXT_ACTIVE if self.input_frag_active else COLOR_TEXT
        
        pygame.draw.rect(self.screen, frag_bg, self.input_frag, border_radius=5)
        self.draw_text_center(self.frag_text, self.input_frag, frag_text_color)
        
        label_speed = self.font.render("Delay(ms):", True, COLOR_TEXT)
        self.screen.blit(label_speed, (self.input_speed.x - 120, self.input_speed.y + 10))
        
        speed_bg = COLOR_INPUT_ACTIVE if self.input_speed_active else COLOR_INPUT_INACTIVE
        speed_text_color = COLOR_INPUT_TEXT_ACTIVE if self.input_speed_active else COLOR_TEXT
        
        pygame.draw.rect(self.screen, speed_bg, self.input_speed, border_radius=5)
        self.draw_text_center(self.speed_text, self.input_speed, speed_text_color)

    def draw_grid(self):
        self.screen.fill(COLOR_BG)
        for i, color in enumerate(self.linear_grid):
            x = (i % self.cols) * CELL_SIZE
            y = (i // self.cols) * CELL_SIZE
            rect = pygame.Rect(x, y, CELL_SIZE - 1, CELL_SIZE - 1)
            pygame.draw.rect(self.screen, color, rect)

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
                    
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.btn_randomize.collidepoint(event.pos):
                        self.generate_seed()
                    if self.btn_start.collidepoint(event.pos):
                        self.is_defragging = True
                    
                    self.input_speed_active = self.input_speed.collidepoint(event.pos)
                    self.input_frag_active = self.input_frag.collidepoint(event.pos)

                if event.type == pygame.KEYDOWN:
                    if self.input_speed_active:
                        if event.key == pygame.K_BACKSPACE:
                            self.speed_text = self.speed_text[:-1]
                        elif event.unicode.isnumeric():
                            if len(self.speed_text) < 4: 
                                self.speed_text += event.unicode
                        self.delay_ms = int(self.speed_text) if self.speed_text else 0
                        
                    elif self.input_frag_active:
                        if event.key == pygame.K_BACKSPACE:
                            self.frag_text = self.frag_text[:-1]
                        elif event.unicode.isnumeric():
                            if len(self.frag_text) < 3: 
                                self.frag_text += event.unicode
                                
                        raw_frag = int(self.frag_text) if self.frag_text else 0
                        self.frag_percent = min(raw_frag, 100)
                        
                        if raw_frag > 100:
                            self.frag_text = "100"

            self.defrag_step()
            self.draw_grid()
            self.draw_ui()
            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    app = DefragVisualizer()
    app.run()