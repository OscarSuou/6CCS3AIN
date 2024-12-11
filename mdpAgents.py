# mdpAgents.py
# parsons/20-nov-2017
#
# Version 1
#
# The starting point for CW2.
#
# Intended to work with the PacMan AI projects from:
#
# http://ai.berkeley.edu/
#
# These use a simple API that allow us to control Pacman's interaction with
# the environment adding a layer on top of the AI Berkeley code.
#
# As required by the licensing agreement for the PacMan AI we have:
#
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
# 
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).

# The agent here is was written by Simon Parsons, based on the code in
# pacmanAgents.py

from game import Agent
import api
from pacman import Directions

class Grid:
    def __init__(self, width, height):
        '''
        Initialize a Grid object with the given width and height.
        The grid is represented as a 2D list of zeros.
        '''        
        self.width = width
        self.height = height
        self.grid = [[0 for _ in range(width)] for _ in range(height)]

    def setValue(self, x, y, value):
        self.grid[y][x] = value

    def getValue(self, x, y):
        return self.grid[y][x]

    def getHeight(self):
        return self.height

    def getWidth(self):
        return self.width

class MDPAgent(Agent):

    def __init__(self):

        print "Starting up MDPAgent!"

        '''
        Initializes the MDPAgent object.
        This method is called when an instance of the MDPAgent class is created.
        It sets up the initial state of the agent, including the reward dictionary, state dictionary, utility dictionary, walls set, and grid set.
        '''
        self.rewardDict = {}    # Initialize an empty dictionary to store the reward values for each state.
        self.stateDict = {}     # Initialize an empty dictionary to store the state transition probabilities for each state-action pair.
        self.utils = {}         # Initialize an empty dictionary to store the utility values for each state.
        self.walls = set()      # Initialize an empty set to store the positions of the walls in the environment.
        self.grid = set()       # Initialize an empty set to store the positions of the grid cells in the environment.

    def registerInitialState(self, state):
        self.stateMapping(state)        # Map the state to identify the possible actions and next states.
        self.makeMap(state)             # Create a map of the environment based on the initial state.
        self.walls = set(api.walls(state))  # Identify the positions of the walls in the environment and store them in a set.
        corners = api.corners(state)    # Identify the corners of the environment and store them in a list.
        map_width = range(0, corners[1][0])     # Define the width of the map as the range from 0 to the x-coordinate of the second corner.
        map_height = range(0, corners[2][1])    # Define the height of the map as the range from 0 to the y-coordinate of the third corner.
        self.grid = set((x, y) for x in map_width for y in map_height)      # Create a set of grid cells by iterating over the width and height ranges.
        print "Running registerInitialState for MDPAgent!"


    def makeMap(self, state):   # Create a map of the game layout based on the current state.
        corners = api.corners(state)    # Get the corners of the game layout
        height = self.getLayoutHeight(corners)  # Calculate the height of the layout using the corners
        width = self.getLayoutWidth(corners)    # Calculate the width of the layout using the corners
        self.map = Grid(width, height)  # Initialize a Grid object with the calculated width and height

    def getLayoutHeight(self, corners):
        return max(corner[1] for corner in corners) + 1

    def getLayoutWidth(self, corners):
        return max(corner[0] for corner in corners) + 1


    def rewardMapping(self, state):
        self.assignRewardsForFoodAndCapsules(state)
        self.assignRewardsForGhosts(state)

    def assignRewardsForFoodAndCapsules(self, state):
        walls = self.walls
        food = set(api.food(state))
        capsules = set(api.capsules(state))

        self.rewardDict = {key: -0.04 for key in self.grid if key not in walls}
        self.utils = {key: 0 for key in self.grid if key not in walls}
        self.rewardDict.update({k: 2 for k in food})
        self.rewardDict.update({k: 2 for k in capsules})

    def assignRewardsForGhosts(self, state):
        ghostStates = api.ghostStates(state)
        for j in ghostStates:
            if j[0] in self.rewardDict:
                if j[1] == 0:
                    self.rewardDict[j[0]] = -500
                    ghostNeighbours = self.ghostRadius(state, j[0], 2)
                    self.rewardDict.update({k: -20 for k in ghostNeighbours})


    def stateMapping(self, state):
        walls = set(api.walls(state))
        # Initialize a dictionary to store the neighboring states in different directions for each state
        stateDict = {key: {'North': [], 'South': [], 'East': [], 'West': []} for key in self.rewardDict.keys()} 

        for key in stateDict.keys():
            neighbours = self.neighbours(key)
            # Assign the neighboring states to the corresponding directions in the state dictionary
            stateDict[key]['North'] = [neighbours[3], neighbours[0], neighbours[2]]
            stateDict[key]['South'] = [neighbours[1], neighbours[0], neighbours[2]]
            stateDict[key]['East'] = [neighbours[0], neighbours[3], neighbours[1]]
            stateDict[key]['West'] = [neighbours[2], neighbours[3], neighbours[1]]

            # Iterate over each direction in the state dictionary
            for direction, states in stateDict[key].items():
                # Replace any wall positions with the current state's position
                stateDict[key][direction] = [state if state not in walls else key for state in states]

        self.stateDict = stateDict





    def ghostRadius(self, state, ghosts, r):
        def get_neighbors(loc):
            return [i for i in self.neighbours(loc) if i not in api.walls(state) and i not in ghosts]

        def expand_radius(current_radius, current_neighbors):
            if current_radius == r:
                return set(current_neighbors)
            next_neighbors = set()
            for neighbor in current_neighbors:
                # Get the neighbors of the current neighbor and add them to the next neighbors set
                next_neighbors.update(get_neighbors(neighbor))
            return expand_radius(current_radius + 1, next_neighbors)

        return expand_radius(1, [ghosts])

        
    def valueIteration(self, state):
        gamma = 0.6     # The discount factor
        epsilon = 0.001     # The convergence threshold
        states = self.stateDict  
        gridVals = self.rewardDict  
        utilDict = self.utils  

        # Iterate until convergence
        while True:
            delta = 0
            for square, utility in utilDict.items():
                U = utility
                tmp_utils = {}
                for direction, state in states[square].items():
                    U_s = gridVals[square] + gamma * (
                            0.8 * utilDict[state[0]] + 0.1 * utilDict[state[1]] + 0.1 * utilDict[state[2]])
                    tmp_utils[direction] = U_s
                utilDict[square] = max(tmp_utils.values())
                delta = max(delta, abs(utilDict[square] - U))
            if delta < epsilon * (1 - gamma) / gamma:
                return utilDict


    def neighbours(self, id):
        (x, y) = id
        # E, S, W, N
        return [(x + 1, y), (x, y - 1), (x - 1, y), (x, y + 1)]


    def bestMove(self, state, gridVals):
        walls = set(api.walls(state))
        loc = api.whereAmI(state)
        possibleStates = [i for i in self.neighbours(loc) if i not in walls]
        U_states = [gridVals[i] for i in possibleStates]
        bestMove = possibleStates[U_states.index(max(U_states))]
        return bestMove


    def singleMove(self, location, neighbour):
        bearing = tuple(x - y for x, y in zip(location, neighbour))
        if bearing == (-1, 0):
            return Directions.EAST
        elif bearing == (1, 0):
            return Directions.WEST
        elif bearing == (0, -1):
            return Directions.NORTH
        elif bearing == (0, 1):
            return Directions.SOUTH
        
    def final(self, state):
        print "Looks like the game just ended!"

    def getAction(self, state):
        start = api.whereAmI(state)
        self.rewardMapping(state)
        if not self.stateDict:
            self.stateMapping(state)
        gridVals = self.valueIteration(state)
        best_move = self.bestMove(state, gridVals)
        legal = api.legalActions(state)
        return api.makeMove(self.singleMove(start, best_move), legal)

