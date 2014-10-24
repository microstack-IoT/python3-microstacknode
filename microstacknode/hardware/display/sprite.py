"""Sprites are two dimensional drawings/characters/letters."""

class Sprite(object):
    """A two dimensional sprite."""

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.clear()

    def clear(self):
        # inner list is y so we can access it like: pixel_state[x][y]
        self.pixel_state = [[0x00 for i in range(self.height)]
                            for j in range(self.width)]

    def set_pixel(self, x, y, state):
        self.pixel_state[x][y] = state

    def get_pixel(self, x, y):
        return self.pixel_state[x][y]

    def set_row(self, y, row):
        """Sets an entire row to be the value contained in line."""
        for x in range(self.width):
            state = (row >> (self.width - 1 - x)) & 1
            self.set_pixel(x, y, state)

    def get_row(self, y):
        """Returns an entire row as a number."""
        row_state = 0
        for x in range(self.width):
            row_state |= (self.get_pixel(x, y) & 1) << (self.width - 1 - x)
        return row_state;

    def set_col(self, x, line):
        """Sets an entire column to be the value contained in line."""
        for y in range(self.height):
            state = (line >> (self.height - 1 - y)) & 1
            self.set_pixel(x, y, state)

    def get_col(self, x):
        """Returns an entire column as a number."""
        col_state = 0
        for y in range(self.height):
            col_state |= (self.get_pixel(y, x) & 1) << (self.height - 1 - y)
        return col_state

    def render_sprite(self, x, y, sprite_to_draw):
        """Renders the sprite given as an argument on this sprite at (x, y)."""
        for j in range(sprite_to_draw.height):
            for i in range(sprite_to_draw.width):
                new_x = x + i
                new_y = y + j
                we_can_draw_x = 0 <= new_x < self.width
                we_can_draw_y = 0 <= new_y < self.height
                if we_can_draw_x and we_can_draw_y:
                    self.set_pixel(new_x,
                                   new_y,
                                   sprite_to_draw.get_pixel(i, j))

    def get_sprite(self, x, y, width, height):
        """Returns a new sprite of dimensions width x height from the
        given location (x, y) from this sprite.
        """
        new_sprite = Sprite(width, height)
        for j in range(height):
            for i in range(width):
                new_x = x + i
                new_y = y + j
                we_can_get_x = 0 <= new_x < self.width
                we_can_get_y = 0 <= new_y < self.height
                if we_can_get_x and we_can_get_y:
                    new_sprite.set_pixel(i, j, self.get_pixel(new_x, new_y))
        return new_sprite


    def draw_rectangle(self,x,y,width,height,line_weight=0):
        """Draw a rectangle on this sprite.
        """
        if not line_weight: 
            for j in range(height):
                for i in range(width):
                    self.set_pixel(x+i, y+j)
        else:
            for i in range(height):
                for j in range(line_weight):
                    self.set_pixel(x+j, y+i)
                    self.set_pixel(x+height-j, y+i)

            for i in range(width):
                for j in range(line_weight):
                    self.set_pixel(x+i, y+j)
                    self.set_pixel(x+i, y+width-j)              



class CharSprite(Sprite):
    """Character sprite displays an alphanumerical character using a Font."""

    def __init__(self, character, font):
        super().__init__(font.char_width, font.char_height)
        self.font = font
        self.render_char(character)

    def render_char(self, character):
        for i in range(self.height):
            self.set_row(i, self.font.get_char_map(character)[i])


class StringSprite(Sprite):
    """String Sprite displays an alphanumerical string of characters
    using a Font.
    """

    def __init__(self, string, direction, font):
        # make sure str is string
        string = str(string)
        self.direction = direction
        self.font = font

        # calculate this sprites width and height
        if self.direction == 'R' or self.direction == 'L':
            # R:"Hello, World!" or L:"!dlroW ,olleH"
            spr_width = (font.char_width+1) * len(string)
            spr_height = font.char_height
        elif self.direction == 'U' or self.direction == 'D':
            """U:"!  or D:"H
                  d        e
                  l        l
                  r        l
                  o        o
                  W        ,

                  ,        W
                  o        o
                  l        r
                  l        l
                  e        d
                  H"       !"
            """
            spr_width = font.char_width
            spr_height = font.char_height + 1 * len(string)

        super().__init__(spr_width, spr_height)

        self.render_str(string)

    def render_str(self, string):
        for i, c in enumerate(string):
            character = CharSprite(c, self.font)
            # width and height with 1 pixel space
            chr_width_sp = self.font.char_width + 1;
            chr_height_sp = self.font.char_height + 1;
            if self.direction == 'R':
                self.render_sprite(i * chr_width_sp, 0, character)
            elif self.direction == 'U':
                self.render_sprite(0, i * chr_height_sp, character)
            elif self.direction == 'D':
                # put the space before each letter (-1 to y)
                y = self.height-self.font.char_height-(i*chr_height_sp)-1
                self.render_sprite(0, y, character)
            elif self.direction == 'L':
                x = self.width - chr_width_sp - (i*chr_width_sp)
                self.render_sprite(x, 0, character)
