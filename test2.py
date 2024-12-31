def initialize_domain(board):
    domain = {}
    for r in range(9):
        for c in range(9):
            if board[r][c] == 0:  # Unassigned cell
                domain[(r, c)] = set(range(1, 10))  # Start with all possible values
            else:
                domain[(r, c)] = {board[r][c]}  # Already assigned
    return domain

def check_grid(grid, expected_rows, expected_cols, valid_values):
    # Check dimensions
    if len(grid) != expected_rows:
        raise ValueError(f"Grid has {len(grid)} rows, expected {expected_rows}.")
    for row in grid:
        if len(row) != expected_cols:
            raise ValueError(f"Row in grid has {len(row)} columns, expected {expected_cols}.")
    
    # Check values
    for r in range(expected_rows):
        for c in range(expected_cols):
            if grid[r][c] not in valid_values:
                raise ValueError(f"Invalid value {grid[r][c]} found at position ({r}, {c}).")
    return True

def read_input_file(filename):
    with open(filename, 'r') as file:
        # Read the Sudoku board (9x9)
        board = [list(map(int, file.readline().split())) for _ in range(9)]
        file.readline()  # Skip empty line
        
        # Read the horizontal adjacency constraints (9x8)
        horiz_adjacency = [list(map(int, file.readline().split())) for _ in range(9)]
        file.readline()  # Skip empty line
        
        # Read the vertical adjacency constraints (8x9)
        vert_adjacency = [list(map(int, file.readline().split())) for _ in range(8)]

    # Validate the grids using the check_grid function
    check_grid(board, 9, 9, set(range(0, 10)))          # Values should be between 0 and 9
    check_grid(horiz_adjacency, 9, 8, {0, 1, 2})        # Values should be 0, 1, or 2
    check_grid(vert_adjacency, 8, 9, {0, 1, 2})         # Values should be 0, 1, or 2

    return board, horiz_adjacency, vert_adjacency

# Check if the value is consistent with Sudoku rules and Kropki constraints
def is_consistent(board, row, col, value, horiz_adjacency, vert_adjacency, log_file):
    # Check row and column uniqueness
    if value in board[row]:
        log_file.write(f"Inconsistency: Value {value} already exists in row {row}\n")
        return False
    if value in [board[r][col] for r in range(9)]:
        log_file.write(f"Inconsistency: Value {value} already exists in column {col}\n")
        return False

    # Check 3x3 box uniqueness
    box_row, box_col = row // 3 * 3, col // 3 * 3
    for i in range(box_row, box_row + 3):
        for j in range(box_col, box_col + 3):
            if board[i][j] == value:
                log_file.write(f"Inconsistency: Value {value} already exists in box starting at ({box_row}, {box_col})\n")
                return False

    # Check horizontal adjacency constraints
    if col > 0 and horiz_adjacency[row][col - 1] != 0:
        neighbor = board[row][col - 1]
        if neighbor != 0:  # Left neighbor
            if horiz_adjacency[row][col - 1] == 1 and abs(value - neighbor) != 1:
                log_file.write(f"Inconsistency: White Horizontal constraint between {value} and left neighbor {neighbor} at ({row}, {col-1}) not satisfied\n")
                return False
            if horiz_adjacency[row][col - 1] == 2 and (value != 2 * neighbor and neighbor != 2 * value):
                log_file.write(f"Inconsistency: Black Horizontal constraint between {value} and left neighbor {neighbor} at ({row}, {col-1}) not satisfied\n")
                return False
    if col < 8 and horiz_adjacency[row][col] != 0:
        neighbor = board[row][col + 1]
        if neighbor != 0:  # Right neighbor
            if horiz_adjacency[row][col] == 1 and abs(value - neighbor) != 1:
                log_file.write(f"Inconsistency: White Horizontal constraint between {value} and right neighbor {neighbor} at ({row}, {col+1}) not satisfied\n")
                return False
            if horiz_adjacency[row][col] == 2 and (value != 2 * neighbor and neighbor != 2 * value):
                log_file.write(f"Inconsistency: Black Horizontal constraint between {value} and right neighbor {neighbor} at ({row}, {col+1}) not satisfied\n")
                return False

    # Check vertical adjacency constraints
    if row > 0 and vert_adjacency[row - 1][col] != 0:
        neighbor = board[row - 1][col]
        if neighbor != 0:  # Above neighbor
            if vert_adjacency[row - 1][col] == 1 and abs(value - neighbor) != 1:
                log_file.write(f"Inconsistency: White Vertical constraint between {value} and above neighbor {neighbor} at ({row-1}, {col}) not satisfied\n")
                return False
            if vert_adjacency[row - 1][col] == 2 and (value != 2 * neighbor and neighbor != 2 * value):
                log_file.write(f"Inconsistency: Black Vertical constraint between {value} and above neighbor {neighbor} at ({row-1}, {col}) not satisfied\n")
                return False
    if row < 8 and vert_adjacency[row][col] != 0:
        neighbor = board[row + 1][col]
        if neighbor != 0:  # Below neighbor
            if vert_adjacency[row][col] == 1 and abs(value - neighbor) != 1:
                log_file.write(f"Inconsistency: White Vertical constraint between {value} and below neighbor {neighbor} at ({row+1}, {col}) not satisfied\n")
                return False
            if vert_adjacency[row][col] == 2 and (value != 2 * neighbor and neighbor != 2 * value):
                log_file.write(f"Inconsistency: Black Vertical constraint between {value} and below neighbor {neighbor} at ({row+1}, {col}) not satisfied\n")
                return False

    return True

# Find unassigned cell using MRV and DH
def select_unassigned_variable(board, horiz_adjacency, vert_adjacency, log_file):
    best_cell = None
    min_remaining = 10  # Initialize with a value larger than the domain size
    max_degree = -1

    for r in range(9):
        for c in range(9):
            if board[r][c] == 0:  # Unassigned cell
                # Calculate remaining legal values (MRV)
                # legal_values = [val for val in range(1, 10) if is_consistent(board, r, c, val, horiz_adjacency, vert_adjacency, log_file)]
                # num_remaining = len(legal_values)
                num_remaining = len(domain[(r, c)])

                # Calculate degree heuristic
                degree = 0
                for neighbor in [(r, c - 1), (r, c + 1), (r - 1, c), (r + 1, c)]:
                    nr, nc = neighbor
                    if 0 <= nr < 9 and 0 <= nc < 9 and board[nr][nc] == 0:
                        degree += 1

                # Apply MRV and break ties with DH
                if num_remaining < min_remaining or (num_remaining == min_remaining and degree > max_degree):
                    best_cell = (r, c)
                    min_remaining = num_remaining
                    max_degree = degree
    if best_cell:
        log_file.write(f"Selected cell: {best_cell}, MRV: {min_remaining}, Degree: {max_degree}\n")
    
    return best_cell
   

def write_output_file(board, filename):
    with open(filename, 'w') as file:
        for row in board:
            file.write(' '.join(map(str, row)) + '\n')

# Dictionary to track domain changes for each variable
domain_changes = {}

def forward_check(board, row, col, value, horiz_adjacency, vert_adjacency, log_file):
    """
    Updates the domains of neighboring cells after assigning a value to a cell.
    Returns True if forward checking succeeds, False otherwise.
    """
    global domain_changes
    domain_changes[(row, col)] = []  # Initialize changes for this cell
    affected_cells = set()
    
    # Update row and column neighbors
    for i in range(9):
        if i != col:
            affected_cells.add((row, i))  # Same row
        if i != row:
            affected_cells.add((i, col))  # Same column

    # Update 3x3 box neighbors
    box_row, box_col = row // 3 * 3, col // 3 * 3
    for i in range(box_row, box_row + 3):
        for j in range(box_col, box_col + 3):
            if (i, j) != (row, col):
                affected_cells.add((i, j))

    # Update neighbors based on Kropki constraints
    if col > 0 and horiz_adjacency[row][col - 1] != 0:
        affected_cells.add((row, col - 1))  # Left neighbor
    if col < 8 and horiz_adjacency[row][col] != 0:
        affected_cells.add((row, col + 1))  # Right neighbor
    if row > 0 and vert_adjacency[row - 1][col] != 0:
        affected_cells.add((row - 1, col))  # Above neighbor
    if row < 8 and vert_adjacency[row][col] != 0:
        affected_cells.add((row + 1, col))  # Below neighbor

    # Temporarily assign the value to the cell
    board[row][col] = value
    log_file.write(f"Assigned value {value} to cell ({row}, {col}) for forward checking.\n")

    # Update domains of affected cells
    for r, c in affected_cells:
        if board[r][c] == 0:  # Only consider unassigned cells
            if value in domain[(r, c)]:
                domain[(r, c)].remove(value)  # Remove the assigned value from domain
                domain_changes[(row, col)].append((r, c, value))  # Track the change
            # Check if domain becomes empty
            legal_values = [v for v in domain[(r, c)] if is_consistent(board, r, c, v, horiz_adjacency, vert_adjacency, log_file)]
            if not legal_values:
                log_file.write(f"Forward checking failed: No legal values left for cell ({r}, {c}).\n")
                board[row][col] = 0  # Undo the assignment
                return False

    return True

def restore_domains(row, col, value, log_file):
    """
    Restores the domain of affected cells after backtracking.
    """
    global domain_changes
    if (row, col) not in domain_changes:
        return

    for r, c, v in domain_changes[(row, col)]:
        domain[(r, c)].add(v)  # Restore the removed value
        log_file.write(f"Restored value {v} to domain of cell ({r}, {c}).\n")

    # Clear the domain_changes record for this cell
    del domain_changes[(row, col)]

    log_file.write(f"Domains restored after backtracking on cell ({row}, {col}).\n")

def backtrack_with_forward_checking(board, horiz_adjacency, vert_adjacency, log_file):
    """
    Backtracking algorithm with forward checking.
    """
    # Select the next unassigned cell using MRV and DH
    cell = select_unassigned_variable(board, horiz_adjacency, vert_adjacency, log_file)
    if not cell:
        return board  # Solution found

    row, col = cell
    log_file.write(f"Attempting to assign a value to cell ({row}, {col}).\n")

    # Iterate over sorted legal values for the selected cell
    for value in sorted(domain[(row, col)]):
        log_file.write(f"Trying value {value} for cell ({row}, {col}).\n")
        if is_consistent(board, row, col, value, horiz_adjacency, vert_adjacency, log_file):
            # Assign the value and apply forward checking
            if forward_check(board, row, col, value, horiz_adjacency, vert_adjacency, log_file):
                board[row][col] = value
                log_file.write(f"Assigned value {value} to cell ({row}, {col}).\n")
                log_file.write("Current board state:\n")
                for row_state in board:
                    log_file.write(" ".join(map(str, row_state)) + "\n")
                log_file.write("\n")

                # Recur to solve the rest of the board
                result = backtrack_with_forward_checking(board, horiz_adjacency, vert_adjacency, log_file)
                if result:
                    return result  # Solution found

                # Undo the assignment and restore domains
                log_file.write(f"Backtracking on cell ({row}, {col}), resetting value {value}.\n")
                board[row][col] = 0
                restore_domains(row, col, value, log_file)

    # No valid assignment found; return failure
    log_file.write(f"No valid assignments found for cell ({row}, {col}). Backtracking.\n")
    return None

input_filename = "Sample_Input.txt"
    
# Read input data
board, horiz_adjacency, vert_adjacency = read_input_file(input_filename)
board_copy = board

domain = initialize_domain(board)
# print(domain)

with open("Working2.txt", "w") as log_file:    
    solution = backtrack_with_forward_checking(board_copy, horiz_adjacency, vert_adjacency, log_file)
    if solution:
        write_output_file(solution, 'Output2.txt')
        print("Solution2 found and written")
    else:
        print("No solution2 exists.")