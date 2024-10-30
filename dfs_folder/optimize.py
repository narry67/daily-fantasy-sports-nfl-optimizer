import pandas as pd
from pulp import *


def optimize_lineup(csv_file, budget, team_filter=None, exclude_players=None, mode='classic'):
    # Read the CSV file
    df = pd.read_csv(csv_file)

    # Filter for records where _merge is 'both'
    df = df[df['_merge'] == 'both']

    # Apply team filter if specified
    if team_filter and len(team_filter) > 0:
        df = df[df['Team'].isin(team_filter)]

    # Apply player exclusion filter if specified
    if exclude_players and len(exclude_players) > 0:
        # Convert player names to uppercase for case-insensitive comparison
        exclude_players = [name.upper() for name in exclude_players]
        df = df[~df['Player'].str.upper().isin(exclude_players)]

    # Reset index after filtering
    df = df.reset_index(drop=True)

    if mode == 'classic':
        # Check if we have enough players after filtering for classic mode
        position_counts = df['Position'].value_counts()
        if (('QB' not in position_counts or position_counts['QB'] < 1) or
                ('WR' not in position_counts or position_counts['WR'] < 3) or
                ('RB' not in position_counts or position_counts['RB'] < 2) or
                ('TE' not in position_counts or position_counts['TE'] < 1)):
            return {
                'status': 'Infeasible',
                'error': 'Not enough players available to create a valid lineup after applying filters.'
            }

    # Create the optimization problem
    prob = LpProblem("Fantasy_Lineup_Optimization", LpMaximize)

    # Create binary variables for each player
    player_vars = LpVariable.dicts("players",
                                   ((i) for i in df.index),
                                   cat='Binary')

    # For showdown mode, create captain variables
    if mode == 'showdown':
        captain_vars = LpVariable.dicts("captain",
                                        ((i) for i in df.index),
                                        cat='Binary')

    if mode == 'classic':
        # Classic mode objective: Maximize total points
        prob += lpSum([player_vars[i] * df.iloc[i]['Points'] for i in df.index])

        # Classic mode constraints
        prob += lpSum([player_vars[i] * df.iloc[i]['Salary'] for i in df.index]) <= budget

        # Position constraints
        prob += lpSum([player_vars[i] for i in df.index if df.iloc[i]['Position'] == 'QB']) == 1
        prob += lpSum([player_vars[i] for i in df.index if df.iloc[i]['Position'] == 'WR']) >= 3
        prob += lpSum([player_vars[i] for i in df.index if df.iloc[i]['Position'] == 'RB']) >= 2
        prob += lpSum([player_vars[i] for i in df.index if df.iloc[i]['Position'] == 'TE']) >= 1

        # Total players constraint
        prob += lpSum([player_vars[i] for i in df.index]) <= 8

    else:  # Showdown mode
        # Objective: Maximize total points including captain bonus (1.5x)
        prob += lpSum([captain_vars[i] * df.iloc[i]['Points'] * 1.5 +
                       player_vars[i] * df.iloc[i]['Points'] for i in df.index])

        # Salary constraint including captain cost (1.5x)
        prob += lpSum([captain_vars[i] * df.iloc[i]['Salary'] * 1.5 +
                       player_vars[i] * df.iloc[i]['Salary'] for i in df.index]) <= budget

        # Exactly one captain
        prob += lpSum([captain_vars[i] for i in df.index]) == 1

        # Total players constraint (5 regular + 1 captain = 6)
        prob += lpSum([player_vars[i] for i in df.index]) == 5

        # A player can't be both captain and regular
        for i in df.index:
            prob += captain_vars[i] + player_vars[i] <= 1

    # Solve the problem
    prob.solve()

    # Check if a solution was found
    if LpStatus[prob.status] != 'Optimal':
        return {
            'status': LpStatus[prob.status],
            'error': 'No valid lineup found with given constraints'
        }

    # Get the selected players
    selected_players = []
    total_salary = 0
    total_points = 0

    if mode == 'classic':
        for i in df.index:
            if player_vars[i].value() == 1:
                player = df.iloc[i]
                selected_players.append({
                    'Player': player['Player'],
                    'Team': player['Team'],
                    'Position': player['Position'],
                    'Salary': player['Salary'],
                    'Points': player['Points']
                })
                total_salary += player['Salary']
                total_points += player['Points']
    else:  # Showdown mode
        # First add captain
        for i in df.index:
            if captain_vars[i].value() == 1:
                player = df.iloc[i]
                selected_players.append({
                    'Player': player['Player'],
                    'Team': player['Team'],
                    'Position': f"CPT {player['Position']}",
                    'Salary': int(player['Salary'] * 1.5),
                    'Points': player['Points'] * 1.5
                })
                total_salary += int(player['Salary'] * 1.5)
                total_points += player['Points'] * 1.5

        # Then add regular players
        for i in df.index:
            if player_vars[i].value() == 1:
                player = df.iloc[i]
                selected_players.append({
                    'Player': player['Player'],
                    'Team': player['Team'],
                    'Position': player['Position'],
                    'Salary': player['Salary'],
                    'Points': player['Points']
                })
                total_salary += player['Salary']
                total_points += player['Points']

    # Sort players - in showdown mode, captain will always be first due to "CPT" prefix
    if mode == 'classic':
        position_order = {'QB': 1, 'RB': 2, 'WR': 3, 'TE': 4}
        selected_players.sort(key=lambda x: position_order[x['Position']])

    return {
        'status': LpStatus[prob.status],
        'total_points': total_points,
        'total_salary': total_salary,
        'remaining_budget': budget - total_salary,
        'lineup': selected_players,
        'mode': mode
    }


def print_lineup(result):
    if 'error' in result:
        print("\nError:", result['error'])
        return

    print("\nOptimization Status:", result['status'])
    print(f"Mode: {result['mode'].title()}")
    print(f"\nTotal Projected Points: {result['total_points']:.2f}")
    print(f"Total Salary: ${result['total_salary']:,}")
    print(f"Remaining Budget: ${result['remaining_budget']:,}")

    print("\nOptimal Lineup:")
    print("-" * 80)
    print(f"{'Position':<10}{'Player':<20}{'Team':<8}{'Salary':<12}{'Projected':<10}")
    print("-" * 80)

    for player in result['lineup']:
        print(f"{player['Position']:<10}"
              f"{player['Player']:<20}"
              f"{player['Team']:<8}"
              f"${player['Salary']:<11,}"
              f"{player['Points']:<10.2f}")
    print("-" * 80)


# Example usage
if __name__ == "__main__":
    # Ask for game mode
    mode = input("Select mode (classic/showdown): ").lower()
    while mode not in ['classic', 'showdown']:
        print("Invalid mode. Please enter 'classic' or 'showdown'.")
        mode = input("Select mode (classic/showdown): ").lower()

    budget = int(input("Enter your budget: "))

    # Ask about team filter
    use_team_filter = input("Do you want to filter by specific teams? (yes/no): ").lower()
    team_filter = []

    if use_team_filter == 'yes':
        print("\nEnter up to 4 teams (use team abbreviations, e.g., KC, SF)")
        print("Press Enter without typing anything when you're done.")

        for i in range(4):
            team = input(f"Team {i + 1} (or press Enter to finish): ").upper()
            if not team:
                break
            team_filter.append(team)

        if not team_filter:
            print("No teams specified, using all teams.")

    # Ask about player exclusions
    exclude_players = []
    use_player_exclusions = input("\nDo you want to exclude any players? (yes/no): ").lower()

    if use_player_exclusions == 'yes':
        print("Enter player names to exclude (press Enter after each name, press Enter twice to finish):")
        while True:
            player = input("Player name (or press Enter to finish): ").strip()
            if not player:
                break
            exclude_players.append(player)

    result = optimize_lineup('nfl_fantasy_combined.csv', budget, team_filter, exclude_players, mode)
    print_lineup(result)