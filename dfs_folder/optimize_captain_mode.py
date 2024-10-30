import pandas as pd
from pulp import LpMaximize, LpProblem, LpVariable, lpSum, LpSolverDefault

# Load data
dk_data = pd.read_csv('DK_single_game.csv')
fd_data = pd.read_csv('FD_single_game.csv')


def optimize_team(data, budget, num_players, multiplier_on_first_player=False, dk_mode=False):
    # Create the problem
    prob = LpProblem("Optimal_Team", LpMaximize)

    # Define decision variables for each player (1 if chosen, 0 otherwise)
    player_vars = {i: LpVariable(f"player_{i}", cat="Binary") for i in range(len(data))}

    # Add constraint for budget
    if dk_mode:
        # First player gets both points and salary multipliers
        prob += lpSum([player_vars[i] * (data.loc[i, 'salary_y'] * 1.5 if i == 0 else data.loc[i, 'salary_y']) for i in
                       range(len(data))]) <= budget
    else:
        prob += lpSum([player_vars[i] * data.loc[i, 'salary_y'] for i in range(len(data))]) <= budget

    # Add constraint for number of players
    prob += lpSum(player_vars[i] for i in range(len(data))) == num_players

    # Objective function: maximize total points
    if multiplier_on_first_player:
        prob += lpSum([player_vars[i] * (data.loc[i, 'points'] * 1.5 if i == 0 else data.loc[i, 'points']) for i in
                       range(len(data))])
    else:
        prob += lpSum(player_vars[i] * data.loc[i, 'points'] for i in range(len(data)))

    # Solve the problem without verbose output
    LpSolverDefault.msg = False  # Suppress solver messages
    prob.solve()

    # Gather selected players in a DataFrame
    selected_players = []
    total_points = 0
    total_budget = 0

    for i in range(len(data)):
        if player_vars[i].value() == 1:
            player_info = data.loc[i, ['first_initial', 'last_name', 'team', 'position', 'points', 'salary_y']].copy()
            # Adjust points and salary if it's the first player and mode requires multipliers
            if i == 0:
                player_info['points'] *= 1.5
                if dk_mode:
                    player_info['salary_y'] *= 1.5
            total_points += player_info['points']
            total_budget += player_info['salary_y']
            selected_players.append(player_info)

    # Calculate remaining budget
    remaining_budget = budget - total_budget

    # Create DataFrame for selected players
    selected_df = pd.DataFrame(selected_players)

    return selected_df, remaining_budget, total_points


# FD: FanDuel Optimization
fd_team_df, fd_budget_remaining, fd_total_points = optimize_team(fd_data, budget=60000, num_players=5,
                                                                 multiplier_on_first_player=True)
print("FanDuel Optimal Team:")
print(fd_team_df)
print(f"\nBudget Remaining: {fd_budget_remaining}")
print(f"Total Points Projected: {fd_total_points}\n")

# DK: DraftKings Optimization
dk_team_df, dk_budget_remaining, dk_total_points = optimize_team(dk_data, budget=50000, num_players=6,
                                                                 multiplier_on_first_player=True, dk_mode=True)
print("DraftKings Optimal Team:")
print(dk_team_df)
print(f"\nBudget Remaining: {dk_budget_remaining}")
print(f"Total Points Projected: {dk_total_points}")
