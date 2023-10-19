import random
import tkinter as tk

from tkinter import messagebox, filedialog
from PIL import Image, ImageTk

import os

os.environ['TK_SILENCE_DEPRECATION'] = '1'


UP = "up"
DOWN = "down"
LEFT = "left"
RIGHT = "right"
DIRECTIONS = (UP, DOWN, LEFT, RIGHT,
              f"{UP}-{LEFT}", f"{UP}-{RIGHT}",
              f"{DOWN}-{LEFT}", f"{DOWN}-{RIGHT}")
POKEMON = "☺"
FLAG = "@"
UNEXPOSED = "~"
TASK_ONE = "(1)"
TASK_TWO = "(2)"
NUMBERS = ('zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight')
POKEMONS = ('charizard', 'cyndaquil', 'pikachu', 'psyduck', 'togepi', 'umbreon')

class BoardModel(object):
    """
    Model used to store and manage the internal game state.
    """
    def __init__(self, grid_size, num_pokemon):
        """
        Constructs the internal game state.

        Parameters:
            grid_size (int): Size of game.
            num_pokemon (int): Number of hidden Pokemon.
        """
        self._grid_size = grid_size
        self._num_pokemon = num_pokemon
        self._pokemon_locations = ()
        self.generate_pokemons() #Generate Pokemon locations
        self._num_attempted_catches = 0
        self._game = UNEXPOSED * grid_size ** 2

    def get_game(self):
        """
        (str): Returns string representation of the current state of game board.
        """
        return self._game
    
    def get_pokemon_locations(self):
        """
        (tuple<int, ...>): Returns the indices describing all pokemon locations.
        """
        return self._pokemon_locations
    
    def get_num_attempted_catches(self):
        """
        (int): Returns the number of pokeballs currently placed on the board.
        """
        return self._num_attempted_catches
    
    def get_num_pokemon(self):
        """
        (int): Returns the number of pokemon hidden in the game (not caught).
        """
        return self._num_pokemon
        
    def check_win(self):
        """
        (bool): Returns True if the game has been won, else False.
        """
        return UNEXPOSED not in self._game and self._game.count(FLAG) == len(self._pokemon_locations)
    
    def check_loss(self):
        """
        (bool): Returns True if the game has been lost, else False.
        """
        return POKEMON in self._game

    def index_to_position(self, index):
        """
        Converts the game string index to the row, column coordinate on the game grid.
        
        Parameters:
            index (int): The index of the cell in the game string.
            
        Returns:
            (tuple<int, int>): The row, column position of a cell.
        """
        return index // self._grid_size, index % self._grid_size

    def position_to_index(self, position):
        """
        Converts the row, column coordinate on the game grid to the corresponding index
        in the game string.

        Parameters:
            position(tuple<int, int>): The row, column position of a cell.
            
        Returns:
            (int): The index of the cell in the game string.
        """
        row, col = position
        return row * self._grid_size + col

    def generate_pokemons(self):
        """
        Pokemons will be generated and assigned a random index within the game string.
        """
        self._pokemon_locations = ()
        cell_count = self._grid_size ** 2

        for _ in range(self._num_pokemon):
            if len(self._pokemon_locations) >= cell_count:
                break
            index = random.randint(0, cell_count-1)

            while index in self._pokemon_locations:
                index = random.randint(0, cell_count-1)

            self._pokemon_locations += (index,)


    def _replace_character_at_index(self, index, character):
        """
        Updates the game string with a new character at a specified index.
        
        Parameters:
            index (int): The index of the cell where the character is replaced.
            character (str): The new character that will replace the old character.
        """
        self._game = self._game[:index] + character + self._game[index + 1:]

    def flag_cell(self, index):
        """
        Toggle Flag on or off at the selected index and updates the game string.
        Does nothing if the selected index is already revealed.

        Parameters:
            index (int): The index of the cell being flagged or unflagged.
        """
        if self._game[index] == FLAG:
            self._replace_character_at_index(index, UNEXPOSED)
            self._num_attempted_catches -= 1
            self._num_pokemon += 1

        elif self._game[index] == UNEXPOSED:
            self._replace_character_at_index(index, FLAG)
            self._num_attempted_catches += 1
            self._num_pokemon -= 1

    def _index_in_direction(self, index, direction):
        """
        Returns the index of a cell adjacent to the selected cell at a given direction.

        Parameters:
            index (int): Index of the selected cell.
            direction (str): String specifying the direction.

        Returns:
            (int): Index of the adjacent cell.
        """
        row, col = self.index_to_position(index)
        if RIGHT in direction:
            col += 1
        elif LEFT in direction:
            col -= 1
        if UP in direction:
            row -= 1
        elif DOWN in direction:
            row += 1
        if not (0 <= col < self._grid_size and 0 <= row < self._grid_size):
            return None
        return self.position_to_index((row, col))

    def _neighbour_directions(self, index):
        """
        Seek out all the neighbouring cell indices of selected cell.

        Parameters:
            index (int): Index of a selected cell

        Returns:
            (list<int, ...>): List of all neighbouring cell indices.
        """
        neighbours = []
        for direction in DIRECTIONS:
            neighbour = self._index_in_direction(index, direction)
            if neighbour is not None:
                neighbours.append(neighbour)
        return neighbours

    def number_at_cell(self, index):
        """
        Calculates the number to be displayed at the specified index in the game.

        Parameters:
            index (int): Index of a selected cell.
        """
        if self._game[index] != UNEXPOSED:
            return int(self._game[index])
        return len(set(self._pokemon_locations) & set(self._neighbour_directions(index)))

    def _big_fun_search(self, index):
        """
        When the cell being revealed has a zero value, all the neighbouring cells of this
        cell is revealed. This is repeated until all neighbouring cells have a non-zero
        value. This method calculates all the cells to be revealed in this situation.

        Parameters:
            index (int): Index of the cell being revealed

        Returns:
            (list<int, ...>): List of all the indices to be revealed.
        """
        queue = [index]
        discovered = [index]
        visible = []

        if self._game[index] == FLAG:
            return queue

        number = self.number_at_cell(index)
        if number != 0:
            return queue

        while queue:
            node = queue.pop()
            for neighbour in self._neighbour_directions(node):
                if neighbour in discovered:
                    continue

                discovered.append(neighbour)
                if self._game[neighbour] != FLAG:
                    number = self.number_at_cell(neighbour)
                    if number == 0:
                        queue.append(neighbour)
                visible.append(neighbour)
        return visible

    def reveal_cells(self, index):
        """
        Reveals all neighbouring cells at index and repeats for all cells that have a zero
        value. Updates the game string.

        Parameters:
            index (int): Index of the cell being revealed
        """
        if index in self._pokemon_locations:
            for location in self._pokemon_locations:
                self._replace_character_at_index(location, POKEMON)
        elif self._game[index] == FLAG:
            pass
        else:
            number = self.number_at_cell(index)
            self._replace_character_at_index(index, str(number))
            clear = self._big_fun_search(index)
            for i in clear:
                if self._game[i] != FLAG:
                    number = self.number_at_cell(i)
                    self._replace_character_at_index(i, str(number))

class PokemonGame(object):
    """
    Control class that manages communication between the board model, board view and
    status bar.
    """
    def __init__(self, master, grid_size=10, num_pokemon=15, task=TASK_TWO):
        """
        Constructs the game within a master widget.

        Parameters:
            master (tk.Widget): Widget within which the game board is placed
            grid_size (int): Size of the game grid.
            num_pokemon (int): Number of Pokemons to be hidden.
            task (str): Defines the task number of the assignment, which would
                        produce different functionality in the game.
        """
        master.title('Pokemon: Got 2 Find Them All!')
        self._master = master
        self._grid_size = grid_size
        self._num_pokemon = num_pokemon
        
        self._task = task
        
        #Create and pack board label
        self._board_label = tk.Label(self._master, text='Pokemon: Got 2 Find Them All!',
                                     bg='indian red', fg='white', font='Courier 20 bold')
        self._board_label.pack(side=tk.TOP, fill=tk.X)
                
        #Initialise board model and status bar. Board view is initalise in self.draw().
        self._board_model = BoardModel(grid_size, num_pokemon)
        self._status_bar = StatusBar(self._master, self)

        #Only include status bar and file menu for Task 2
        if self._task == TASK_TWO:
            self._status_bar.pack(side=tk.BOTTOM, fill=tk.BOTH)
            
            # File menu
            menubar = tk.Menu(self._master)
            self._master.config(menu=menubar)
            filemenu = tk.Menu(menubar)
            menubar.add_cascade(label="File", menu=filemenu)
            filemenu.add_command(label="Save game", command=self.save_game)
            filemenu.add_command(label="Load game", command=self.load_game)
            filemenu.add_command(label="Restart game", command=self.restart_game)
            filemenu.add_command(label="New game", command=self.new_game)
            filemenu.add_command(label="Quit", command=self.quit)      
            self._filename = None
        
        self.check_num_pokemon()
        self.draw()        

    def check_num_pokemon(self):
        """
        Ensures the number of Pokemon is within the total number of cells. Game would not
        start otherwise.
        """
        if self._num_pokemon not in range(self._grid_size ** 2 + 1):
            messagebox.showinfo("Error", "Too many pokemons")
            self._master.destroy()

    def reveal(self, position):
        """
        Reveal cell or cells at the specified position.

        Parameters:
            position (tuple<int, int>): The row, column coordinate of the selected cell.
        """
        index = self._board_model.position_to_index(position)
        self._board_model.reveal_cells(index)
        self._status_bar.update_attempts()
        self.redraw()
        self.check_game_over()
        

    def flag(self, position):
        """
        Flag or unflag a cell at the specified position.

        Parameters:
            position (tuple<int, int>): The row, column coordinate of the selected cell.
        """
        index = self._board_model.position_to_index(position)
        self._board_model.flag_cell(index)
        if self.get_num_pokemon() >= 0:
            self._status_bar.update_attempts()
            self.redraw()
            self.check_game_over()
        else:
            self._board_model.flag_cell(index)
            self._board_model._num_pokemon -= self.get_num_pokemon()
            messagebox.showinfo("Error", "You got no more pokeballs!")
        
    def draw(self):
        """
        Draw the board view to the master widget.
        """        
        if self._task == TASK_ONE:
            self._board_view = BoardView(self._master, self._grid_size, reveal=self.reveal, flag=self.flag)
        elif self._task == TASK_TWO:
            self._board_view = ImageBoardView(self._master, self._grid_size, reveal=self.reveal, flag=self.flag)
        self._board_view.draw_board(self._board_model.get_game())
        self._board_view.pack(side=tk.TOP)
        
    def redraw(self):
        """
        Redraw the board view.
        """
        self._board_view.destroy()
        self.draw()

    def check_game_over(self):
        """
        Check if the game is over and allow player to play again if they wish to do so,
        exit otherwise. Stop timer when the game is over.
        """
        ans = 'hi'
        if self._board_model.check_win():
            ans = messagebox.askyesno("Game Over", "You win! Would you like to play again?")
            self._status_bar.stop_time()
        if self._board_model.check_loss():
            ans = messagebox.askyesno("Game Over", "You lose! Would you like to play again?")
            self._status_bar.stop_time()
        if ans != 'hi':
            if ans:
                self.new_game()
            else:
                self._master.destroy()
          
    def get_num_attempted_catches(self):
        """
        (int): Returns the number of attempted catches.
        """
        return self._board_model.get_num_attempted_catches()

    def get_num_pokemon(self):
        """
        (int): Returns the number of hidden(uncaught) Pokemon.
        """
        return self._board_model.get_num_pokemon()

    def save_game(self):
        """
        Saves necessary game information into a Text file if the player wishes to do so.
        """
        save_content = [self._board_model.get_game(), self._board_model.get_pokemon_locations(),
                        self.get_num_attempted_catches(), self.get_num_pokemon(), self._status_bar.get_time()]
        if self._filename is None:
            filename = filedialog.asksaveasfilename(filetypes=[("Text file (please add .txt when saving)", "txt")])
            if filename:
                self._filename = filename
        if self._filename:
            fd = open(self._filename, 'w')
            #The items in save_content are converted to strings and joined together with '#' separators
            fd.write("#".join(map(str, save_content)))
            fd.close()

    def load_game(self):
        """
        Load a previously saved game.
        """
        filename = filedialog.askopenfilename(filetypes=[("Text file", "txt")])
        if filename:
            self._status_bar.destroy()
            self._filename = filename
            fd = open(filename, 'r')
            string = fd.read()
            fd.close()
            content = string.split("#")
            try:
                self._board_model._game = content[0]
                #Conversion of a string to a tuple
                self._board_model._pokemon_locations = tuple(map(int, content[1].strip()[1:-1].split(',')))
                self._board_model._num_attempted_catches = int(content[2])
                self._board_model._num_pokemon = int(content[3])
                saved_time = tuple(map(int, content[4].strip()[1:-1].split(',')))
                self._status_bar = StatusBar(self._master, self, saved_time)
                self._status_bar.pack(side=tk.BOTTOM, fill=tk.BOTH)
                self.redraw()
            except Exception:
                messagebox.showinfo("Cannot load file", "The file used is incorrect")
            
    
    def restart_game(self):
        """
        Restarts the game with same Pokemon locations.
        """
        self._status_bar.destroy()
        self._board_model._game = UNEXPOSED * self._grid_size ** 2
        self._board_model._num_pokemon = self._num_pokemon
        self._board_model._num_attempted_catches = 0
        self._status_bar = StatusBar(self._master, self)
        self._status_bar.pack(side=tk.BOTTOM, fill=tk.BOTH)
        self.redraw()

    def new_game(self):
        """
        Restarts to a new game.
        """
        self._status_bar.destroy()
        self._board_model = BoardModel(self._grid_size, self._num_pokemon)
        self._status_bar = StatusBar(self._master, self)
        if self._task == TASK_TWO:
            self._status_bar.pack(side=tk.BOTTOM, fill=tk.BOTH)
        self.redraw()

    def quit(self):
        """
        If the player wishes to quit the game, ask whther they are sure. Continues the game
        or end it depending on their response.
        """
        ans = messagebox.askyesno("Quit game", "Are you sure?")
        if ans:
            self._master.destroy()

class BoardView(tk.Canvas):
    """
    View of the game board.
    """
    def __init__(self, master, grid_size, board_width=600, reveal=None, flag=None):
        """
        Constructs the board view of the game.

        Parameters:
            master (tk.Widget): Widget within which the board is placed.
            grid_size (int): Size of the game grid
            board_width (int): The game board width in number of pixels.
            reveal (callable): Callable to call when a cell is being revealed.
            flag (callable): Callable to call when a cell is being flagged or unflagged.
        """
        super().__init__(master, width=board_width, height=board_width)
        self._master = master
        self._grid_size = grid_size
        self._board_width = board_width
        self._cell_width = board_width // grid_size
        
        self.reveal = reveal
        self.flag = flag

        #PhotoImages are stored in a dictionary to provide reference to them
        self._images = {}
        
        #Bind left and right clicks on Canvas
        self.bind("<Button-1>", self._left_click)
        for i in range(2,4):
            self.bind(f"<Button-{i}>", self._right_click)          
   
    def draw_board(self, board):
        """
        Draws the current state of the game board that reflects the game state.

        Parameters:
            board (str): The game string from BoardModel that reflects the internal
                         game state
        """
        self.delete(tk.ALL)
        for index, cell_type in enumerate(board):
            x1 = index % self._grid_size * self._cell_width
            y1 = index // self._grid_size * self._cell_width
            x2 = x1 + self._cell_width
            y2 = y1 + self._cell_width
            if cell_type == UNEXPOSED:
                self.create_rectangle(x1, y1, x2, y2, fill='dark green')
            elif cell_type.isdigit():
                self.create_rectangle(x1, y1, x2, y2, fill='pale green')
                text_position = (x1 + x2) / 2, (y1 + y2) / 2
                self.create_text(text_position, text=f"{cell_type}")
            elif cell_type == POKEMON:
                self.create_rectangle(x1, y1, x2, y2, fill='yellow')
            elif cell_type == FLAG:
                self.create_rectangle(x1, y1, x2, y2, fill='red')

    def _left_click(self, event):
        """
        Handles left clicks on a cell and calls the reveal method.
        """
        pixel = event.x, event.y
        position = self.pixel_to_position(pixel)
        self.reveal(position)
        
    def _right_click(self, event):
        """
        Handles right clicks on a cell and calls the flag method.
        """
        pixel = event.x, event.y
        position = self.pixel_to_position(pixel)
        self.flag(position)
        
    def pixel_to_position(self, pixel):
        """
        Converts the supplied pixel to the position of the cell it is contained within.
        """
        x, y = pixel
        row = y // self._cell_width
        col = x // self._cell_width
        return (row, col)

class ImageBoardView(BoardView):
    """
    Extends from the BoardView that uses images to construct the game board.
    """
    def draw_board(self, board):
        """
        Draws the current state of the game board that reflects the game state. Uses images
        from the "images" folder in the directory.

        Parameters:
            board (str): The game string from BoardModel that reflects the internal
                         game state
        """
        self.delete(tk.ALL)
        for index, cell_type in enumerate(board):
            x = index % self._grid_size * self._cell_width + self._cell_width * 0.5
            y = index // self._grid_size * self._cell_width + self._cell_width * 0.5           
            if cell_type == UNEXPOSED:
                photo_image = self._retrieve_image("unrevealed")
            elif cell_type.isdigit():
                num = int(cell_type)
                photo_image = self._retrieve_image(f"{NUMBERS[num]}_adjacent")
            elif cell_type == POKEMON:
                pokemon = random.choice(POKEMONS)
                photo_image = self._retrieve_image("pokemon_sprites/" + pokemon)
            elif cell_type == FLAG:
                photo_image = self._retrieve_image("pokeball")
            self.create_image(x, y, image=photo_image)

    def _retrieve_image(self, image_name):
        """
        Retrieve the PhotoImage from self._images.

        Parameters:
            image_name (str): The assigned name of the PhotoImage.
        """
        if image_name not in self._images:
            self._add_image(image_name)
        return self._images[image_name]

    def _add_image(self, image_name):
        """
        Add a PhotoImage to self._images by opening and resizing an image file.

        Parameters:
            image_name (str): The assigned name of the PhotoImage.
        """
        image = Image.open("images/" + image_name + ".gif")
        image = image.resize((self._cell_width, self._cell_width))
        photo_image = ImageTk.PhotoImage(image)
        self._images[image_name] = photo_image
        
class StatusBar(tk.Frame):
    """
    Sidebar display of the number of Pokeballs, timer and buttons to restart or play a new game.
    """
    def __init__(self, master, parent, time=(0,0)):
        """
        Contructs the status bar of the game.

        Parameters:
            master (tk.Widget): Widget within which to place the status bar.
            parent (PokemonGame): The control class of the game.
            time (tuple<int, int>): The starting time (minutes, seconds) for the timer.
        """
        super().__init__(master, bg="white", pady=5)
        self._min, self._sec = time
        self._parent = parent
        self._timer_on = True

        #Buttons Frame
        buttons_frame = tk.Frame(self, bg="white") 
        tk.Button(buttons_frame, text="New game", command=parent.new_game,
                  bg="white").pack(side=tk.TOP, pady=5)
        tk.Button(buttons_frame, text="Restart game", command=parent.restart_game,
                  bg="white").pack(side=tk.TOP, pady=5)
        buttons_frame.pack(side=tk.RIGHT, padx=40)

        #Timer Frame
        timer_frame = tk.Frame(self, bg="white")
        tk.Label(timer_frame, text="Time elapsed", bg="white").pack(side=tk.TOP)
        self._timer = tk.Label(timer_frame, text=f"0m 0s", bg="white")
        self._timer.pack(side=tk.TOP)
        self.start_time()
        timer_frame.pack(side=tk.RIGHT)

        #Clock image
        clock = ImageTk.PhotoImage(Image.open("images/clock.gif"))
        clock_img = tk.Label(self, image=clock, bg="white")
        clock_img.image = clock
        clock_img.pack(side=tk.RIGHT)
        
        #Catch Attempt Frame
        attempt_frame = tk.Frame(self, bg="white")
        self._attempts = tk.Label(attempt_frame, text=f"{parent.get_num_attempted_catches()} attempted catches",
                                  bg="white")
        self._attempts.pack(side=tk.TOP)
        self._pokeballs = tk.Label(attempt_frame, text=f"{parent.get_num_pokemon()} pokeballs left",
                                   bg="white")
        self._pokeballs.pack(side=tk.TOP)
        attempt_frame.pack(side=tk.RIGHT, padx=(0,40))
        
        #Pokeball image
        self._full_pokeball = ImageTk.PhotoImage(Image.open("images/full_pokeball.gif"))
        self._empty_pokeball = ImageTk.PhotoImage(Image.open("images/empty_pokeball.gif"))
        self._pokeball_img = tk.Label(self, image=self._full_pokeball, bg="white")
        self._pokeball_img.image = self._full_pokeball
        self._pokeball_img.pack(side=tk.RIGHT)

    def get_time(self):
        """
        (tuple<int, int>): Returns the current time on the timer.
        """
        return (self._min, self._sec)
    
    def start_time(self):
        """
        Starts the timer.
        """
        self._timer.config(text=f"{self._min}m {self._sec}s")
        self._sec += 1
        if self._sec == 60:
            self._sec = 0
            self._min += 1
        self._after = self.after(1000, self.start_time)

    def stop_time(self):
        """
        Stops the timer
        """
        self._after = self.after_cancel(self._after)

    def update_attempts(self):
        """
        Updates the number of Pokeballs and catch attempts after each right-click to flag a cell.
        """
        self._attempts.config(text=f"{self._parent.get_num_attempted_catches()} attempted catches")
        self._pokeballs.config(text=f"{self._parent.get_num_pokemon()} pokeballs left")
        self._pokeball_img.config(image=self._full_pokeball)
        self._pokeball_img.image = self._full_pokeball
        if self._parent.get_num_pokemon() <= 0:
           self._pokeball_img.config(image=self._empty_pokeball)
           self._pokeball_img.image = self._empty_pokeball

        
def main():
    """
    Creates the main window which the game is runned in.
    """
    root = tk.Tk()
    PokemonGame(root)
    root.mainloop()
    
if __name__ == "__main__":
    main()
