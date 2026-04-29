import sys

from crossword import *
from collections import deque

class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        _, _, w, h = draw.textbbox((0, 0), letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """

        # loop through each Variable in self.domains
        
        for var in self.domains:
            # only keep those words length match
            self.domains[var] = [word for word in self.domains[var] if len(word) == var.length ]
            #  print(self.domains[var])
        

    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """
        revised = False
        overlap = self.crossword.overlaps[x, y]
        if overlap == None:
            return False
        else:
            xi = overlap[0]
            yi = overlap[1]
            x_words = self.domains[x].copy()
            for word_x in self.domains[x]:
                arc_flag = False
                for word_y in self.domains[y]:
                    if (word_x[xi] == word_y[yi]):
                        arc_flag = True
                        break
                if arc_flag == False:
                    x_words.remove(word_x)
                    revised = True
            self.domains[x] = x_words
        
        return revised


    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """
        # create the default arcs
        if arcs == None:
            arcs = deque()
            for var in self.domains:
                neighbors = self.crossword.neighbors(var)
                if neighbors != None:
                    for v in neighbors:
                        arcs.append((var, v))

        while arcs:
            arc = arcs.popleft()        
            x, y = arc
            revised = self.revise(x, y)
            if revised:
                if not self.domains[x]:
                    return False
                # find out the neighbors of x and add them with respect to x to the queue
                x_neighbors = self.crossword.neighbors(x)
                for x_n in x_neighbors:
                    if x_n != y:
                        arcs.append((x_n, x))
        return True
        

    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
        for var in self.crossword.variables:
            if assignment.get(var) is None:
                return False
                        
        return True
        

    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """
        for x, word_x in assignment.items():
            if word_x is not None:          
                # check length
                if (len(word_x) != x.length):
                    return False            
                # check no comflics with neighbors
                neighbors = self.crossword.neighbors(x)
                for y in neighbors:
                    if y in assignment and assignment[y] is not None:
                        word_y = assignment[y]
                        overlap = self.crossword.overlaps[x, y]
                        if overlap is not None:
                            xi, yi = overlap                    
                            if word_x[xi] != word_y[yi]:
                                return False
        
        # check words are all distict
        assigned_words = [word for word in assignment.values() if word is not None]
        if len(assigned_words) != len(set(assigned_words)):
            return False

        raise NotImplementedError

    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """
        words = self.domains[var]
        ruleout_counts_list = []
        neighbors = self.crossword.neighbors(var)

        for word in words:
            ruleout_counts = 0
            for n in neighbors:
                if assignment.get(n) is None: # only calculate the not-yet-assigned neighbors
                    overlap = self.crossword.overlap[var, n]                
                    if overlap is not None:
                        xi, yi = overlap
                        for word_y in self.domains[n]:
                            if word[xi] != word_y[yi]:
                                ruleout_counts += 1
            ruleout_counts_list.append((ruleout_counts, word))


        raise NotImplementedError

    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """
        raise NotImplementedError

    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """
        raise NotImplementedError


def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()
