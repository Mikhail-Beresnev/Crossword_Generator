import sys
import copy

from crossword import *


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
                        w, h = draw.textsize(letters[i][j], font=font)
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
        #Tested
        """
        Updates `self.domains` such that each variable is node-consistent.
        (Removes any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """
        domain = copy.deepcopy(self.domains)
        for variable in domain:
            for word in domain[variable]:
                if len(word) != variable.length:
                    self.domains[variable].remove(word)

    def revise(self, x, y):
        """
        Makes variable `x` arc consistent with variable `y`.
        Removes values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Returns True if a revision was made to the domain of `x`; returns
        False if no revision was made.
        """
        revised = False
        for word in self.domains[x]:
            if self.crossword.overlaps[y,x] is None:
                self.domain[x].remove(word)
                revised = True
        return revised

    def ac3(self, arcs=None):
        """
        Updates `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begins with initial list of all arcs in the problem.
        Otherwise, uses `arcs` as the initial list of arcs to make consistent.

        Returns True if arc consistency is enforced and no domains are empty;
        returns False if one or more domains end up empty.
        """
        if arcs == None:
            arcs = []
            for arc in self.crossword.overlaps:
                if self.crossword.overlaps[arc] != None:
                    arcs.append(arc)
        queue = copy.deepcopy(arcs)
        #list of tuples
        while len(queue) != 0:
            xy = queue.pop(0)
            if self.revise(xy[0],xy[1]):
                if len(self.domains[xy[0]]) == 0:
                    return False
                Xneighbors = self.crossword.neighbors(xy[0])
                Xneighbors.remove(xy[1])
                for z in Xneighbors:
                    queue.append(tuple(z,xy[0]))
        return True
        
    def assignment_complete(self, assignment):
        """
        Returns True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); returns False otherwise.
        """
        for case in assignment:
            if assignment[case] == None:
                return False
        return True

    def consistent(self, assignment):
        """
        Returns True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); returns False otherwise.
        """
        # Check duplicate
        values = list(assignment.values())
        for word in values:
            if values.count(word) > 1 and word != None:
                return False
        for case in assignment:
            if assignment[case] == None:
                continue
            else:
                #Checking length
                if len(assignment[case]) != case.length:
                    return False
                #Checking conflicts
                for neighbor in self.crossword.neighbors(case):
                    if assignment[neighbor] != None and assignment[case] != None:
                        overlap = self.crossword.overlaps[case, neighbor]
                        char1 = assignment[case][overlap[0]]
                        char2 = assignment[neighbor][overlap[1]]
                        if char1 != char2:
                            return False
        return True  

    def order_domain_values(self, var, assignment):
        """
        Returns a list of values in the domain of `var`
        """
        return self.domains[var]

    def select_unassigned_variable(self, assignment):
        """
        Returns an unassigned variable not already part of `assignment`.
        """
        for word in assignment:
            if assignment[word] == None:
                return word
    
    def backtrack(self, assignment):
        """
        Using Backtracking Search, takes as input a partial assignment for the
        crossword and returns a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, returns None.
        """
        if len(assignment) == 0:
            for i in self.domains.keys():
                assignment[i] = None
        #backtrack begins here
        if self.assignment_complete(assignment):
            return assignment
        var = self.select_unassigned_variable(assignment)
        for value in self.order_domain_values(var, assignment):
            if self.consistent(assignment):
                assignment[var] = value
                result = self.backtrack(assignment)
                if result != None and self.consistent(assignment):
                    return result
            assignment[var] = None
        return None

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
