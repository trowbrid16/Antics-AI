# -*- coding: latin-1 -*-

##
# 
# Homework 5 - Genetic Algorithm
#
# Author(s): Caleb Piekstra, Kenny Trowbridge
#
import random, time
from Player import *
from Constants import *
from Construction import CONSTR_STATS
from Construction import Construction
from Ant import UNIT_STATS
from Ant import Ant
from Move import Move
from GameState import addCoords
from AIPlayerUtils import *

# representation of inf
INFINITY = 9999

# gene random number range
GENE_RANGE = 1000
MUTATION_THRESHOLD = 0.1

POPULATION_SIZE = 4
GAMES_PER_GENE = 4
                
# establishing weights for the weighted linear equation
queenSafetyWeight = 0.3

# "max" values for determining how good a state is
maxNumAnts = 98.0 # 100 square minus 2 queens
maxDist = 18.0


# a representation of a 'node' in the search tree
treeNode = {
    # the Move that would be taken in the given state from the parent node
    "move"              : None,
    # the state that would be reached by taking the above move
    "potential_state"   : None,
    # an evaluation of the potential_state
    "state_value"       : 0.0,
    # a reference to the parent node
    "parent_node"       : None
}


##
#AIPlayer
#Description: The responsbility of this class is to interact with the game by
#deciding a valid move based on a given game state. This class has methods that
#will be implemented by students in Dr. Nuxoll's AI course.
#
#Variables:
#   playerId - The id of the player.
##
class AIPlayer(Player):

    #__init__
    #Description: Creates a new Player
    #
    #Parameters:
    #   inputPlayerId - The id to give the new player (int)
    ##
    def __init__(self, inputPlayerId):
        # a depth limit for the search algorithm
        self.maxDepth = 1

        ## genetic instance variables
        # population for setup phase 1
        self.genes1 = [] 
        # population for setup phase 2
        self.genes2 = [] 
        # the index in the population of genes of the gene currently being evaluated
        self.curGeneIdx = 0 
        # tracks the number of games that have been played to evaluate the current gene
        self.gamesPlayed = 0 
        # the size of a gene
        self.geneSize = 40
        # keeps track of whether the first move has yet to be made
        self.firstMove = True

        # initialize the two populations
        for i in range(0, POPULATION_SIZE):
            self.genes1.append(self.generateGene(self.geneSize))
            self.genes2.append(self.generateGene(self.geneSize))
            
        self.fitness = [0] * POPULATION_SIZE

        # Eugene - Eugenics
        super(AIPlayer,self).__init__(inputPlayerId, "Eugene") 

        
    ##
    # generateGene
    # Description: Generates a single randomized gene
    #
    # Parameters:
    #   size - the size of the gene to generate
    #
    # Returns: a new gene
    def generateGene(self, size):
        gene = []
        for i in range(0, size):
            gene.append(random.randint(0, GENE_RANGE))

        return gene

        
    ##
    # mate
    # Description: Mates two parent genes and produces 2 child genes
    # 
    # Parameters:
    #   parent1 - first parent
    #   parent2 - second parent
    #
    # Returns: A list of the two children produced by the mating
    def mate(self, parent1, parent2):
        # pick a random pivot point
        pivot = random.randint(0, len(parent1))
        
        # produce offspring via crossover
        child1 = parent1[:pivot] + parent2[pivot:]
        child2 = parent2[:pivot] + parent1[pivot:]
        
        # allow for the chance of a random mutation on each child
        return map(self.randomMutation, [child1, child2])

        
    ##
    # randomMutation
    # Description: Takes a gene and applies a random mutation to it
    #
    # Parameters:
    #   gene - gene to mutate 
    def randomMutation(self, gene):
        # there is only a chance that the gene will actually mutate
        if random.random() < MUTATION_THRESHOLD:         
            # pick a random spot in the gene
            randIdx = random.randint(0, len(gene) - 1)
            # pick a random mutated value to replace the old value at randIdx
            gene[randIdx] = random.randint(0, GENE_RANGE)
        return gene
            
    ##
    # getNextGeneration
    # Description: Produces the next generation of genes from the current population
    #
    # Parameters:
    #   genes - population of genes 
    def getNextGeneration(self, genes):
        # calculate the total fitness across all genes in the population
        totalFitness = float(sum(self.fitness))        
        
        # assign weights to each gene by calculating a percentage 
        # based on the gene's fitness relative to the total fitness
        # of the entire population
        fitnessWeights = [(f / totalFitness) for f in self.fitness] # create weights for genes out of fitness

        # holds the new population of genes
        newPop = []
        # loop through POPULATION_SIZE number of times
        for _ in range(POPULATION_SIZE):
            # generate a random value between 0 and 1
            rand = random.random()
            # choose a single gene from the original population using
            # the genes' weights
            for geneIdx in range(POPULATION_SIZE):
                # this sum allows for the weighted-random selection
                if rand < sum(fitnessWeights[:geneIdx+1]):
                    newPop.append(genes[geneIdx])
                    break
        
        # now that the new population is populated, go through the population
        # two genes at a time and mate them to produce offspring
        for i in range(0, POPULATION_SIZE, 2):
            (newPop[i], newPop[i+1]) = self.mate(newPop[i], newPop[i+1])

        # return the new population
        return newPop

        
    ##
    # geneToCoords
    # Description: very pretty way to concert a gene into a list of coordinates
    #   linearly assigns a coordinate to each index in the gene
    #   sorts the gene by the values from least to greatest
    #   returns the list of coordinates that are associated with the sorted gene
    # Parameters:
    #   gene - gene to convert   
    #   rowOffset - used to allow a shift in row coordinates to opponents side   
    #
    # Returns: a list of coordinates
    def geneToCoords(self, gene, rowOffset):
        return map(lambda x: x[1], sorted([(value, (idx%10, idx/10+rowOffset)) for idx, value in enumerate(gene)]))

        
    ##
    # vectorDistance
    # Description: Given two cartesian coordinates, determines the 
    #   manhattan distance between them (assuming all moves cost 1)
    #
    # Parameters:
    #   self - The object pointer
    #   pos1 - The first position
    #   pos2 - The second position
    #
    # Return: The manhattan distance
    #
    def vectorDistance(self, pos1, pos2):
        return (abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1]))
                    
    
    ##
    # distClosestAnt
    # Description: Determines the distance between a cartesian coordinate
    #   and the coordinates of the enemy ant closest to it.
    #
    # Parameters:
    #   self - The object pointer
    #   currentState - The state to analyze
    #   initialCoords - The positition to check enemy ant distances from
    #
    # Return: The minimum distance between initialCoords and the closest
    #           enemy ant.
    #
    def distClosestAnt(self, currentState, initialCoords):
        # get a list of the enemy player's ants
        closestAntDist = 999
        for ant in currentState.inventories[(currentState.whoseTurn+1)%2].ants:
            tempAntDist = self.vectorDistance(ant.coords, initialCoords)
            if tempAntDist < closestAntDist:
                closestAntDist = tempAntDist
        return closestAntDist
    
    
    ##
    # evaluateNodes
    # Description: The evaluateNodes method evaluates a list of nodes
    # and determines their overall evaluation score.
    #
    # Parameters:
    #   self - The object pointer
    #   nodes - The list of nodes to evaluate
    #
    # Return: An overall evaluation score of the list of nodes
    #
    def evaluateNodes(self, nodes):
        # holds the greatest state_value in the list of nodes
        bestValue = 0.0
        # look through the nodes and find the greatest state_value
        for node in nodes:
            if node["state_value"] > bestValue:
                bestValue = node["state_value"]
        # return the greatest state_value
        return bestValue

        
    ##
    # alpha_beta_search
    # Description: use minimax with alpha beta pruning to determine what move to make
    #
    # Parameters:
    #   self - the object pointer
    #   node - the initial node, before any moves are explored
    #
    # Returns: the move which benefits the opposing player the least.
    #
    ##
    def alpha_beta_search(self, node):
        bestNode = self.max_value(node, -INFINITY, INFINITY, 0)
        while bestNode["parent_node"]["parent_node"] is not None:
            bestNode = bestNode["parent_node"]
        return bestNode["move"]

    
    ##
    # createNode
    # Description: Creates a node with values set based on parameters
    #
    # Parameters:
    #   self - The object pointer
    #   move - The move that leads to the resultingState
    #   resultingState - The state that results from making the move
    #   parent - The parent node of the node being created
    #
    # Returns: A new node with the values initialized using the parameters
    #
    def createNode(self, move, resultingState, parent):
        # Create a new node using treeNode as a model
        newNode = treeNode.copy()
        # set the move
        newNode["move"] = move
        # set the state that results from making the move
        newNode["potential_state"] = resultingState
        # set the value of the resulting state
        newNode["state_value"] = self.evaluateState(resultingState)
        # store a reference to the parent of this node
        newNode["parent_node"] = parent
        return newNode


    ##
    # max_value
    # Description: returns the best move our player can make from the current state
    #
    # Parameters:
    #   self - the object pointer
    #   node - the current node, before any moves are explored
    #   alpha - the alpha value, the value of our best move
    #   beta - the value of the opponent's best move
    #   currentDepth - the current depth of the node from the initial node
    #
    # Returns: the move which benefits the opposing player the least (alpha).
    #
    def max_value(self, node, alpha, beta, currentDepth):
        # base case, maxDepth reached, return the value of the currentState
        if currentDepth == self.maxDepth:
            return node
        state = node["potential_state"]
        v = -INFINITY

        # holds a list of nodes reachable from the currentState
        nodeList = []
        # loop through all legal moves for the currentState
        for move in listAllLegalMoves(state):
            # don't bother doing any move evaluations for the queen
            # unless we need to build a worker (she is in the way!)
            if move.moveType == MOVE_ANT:
                initialCoords = move.coordList[0]
                if ((getAntAt(state, initialCoords).type == QUEEN) and 
                    len(state.inventories[state.whoseTurn].ants) >= 2):
                        continue
            if move.moveType == BUILD:
                # hacky way to speed up the code by forcing building workers
                # over any other ant
                if move.buildType != WORKER:
                    continue
            # get the state that would result if the move is made
            resultingState = self.processMove(state, move)
            #create a newNode for the resulting state
            newNode = self.createNode(move, resultingState, node)
            # if a goal state has been found, stop evaluating other branches
            if newNode["state_value"] == 1.0:
                #we have a goal state, no alpha_beta evaluation is needed
                return newNode
            nodeList.append(newNode)

        #sort nodes from greatest to least
        sortedNodeList = sorted(nodeList, key=lambda k: k['state_value'], reverse=True)
        
        # throw away the last half of the list to minimize the number of nodes
        sortedNodeList = sortedNodeList[:(len(sortedNodeList)+1)/2]
        
        #holds a reference to the current best node to move to
        bestValNode = None
                
        #if it is our players turn
        if (self.playerId == state.whoseTurn):
            for tempNode in sortedNodeList:
                maxValNode = self.max_value(tempNode, alpha, beta, currentDepth+1)
                #if it's our turn and we're in max_value, stay in max_value
                if v < maxValNode["state_value"]:
                        bestValNode = maxValNode
                        v = maxValNode["state_value"]
                if v >= beta:
                    return maxValNode
                alpha = max(alpha, v)
        #else it is the opponents player turn
        else:
            sortedNodeList = sorted(nodeList, key=lambda k: k['state_value'])
            for tempNode in sortedNodeList:
                maxValNode = self.min_value(tempNode, alpha, beta, currentDepth+1)
                #if it's opponent's turn and they're in max_value, to toggle to min_value
                if v < maxValNode["state_value"]:
                       bestValNode = maxValNode
                       v = maxValNode["state_value"]
                if v >= beta:
                    return maxValNode
                alpha = max(alpha, v)

        return bestValNode


    ##
    # min_value
    # Description: returns the best move our opponent can make from the current state
    #
    # Parameters:
    #   self - the object pointer
    #   node - the current node, before any moves are explored
    #   alpha - the alpha value, the value of our best move
    #   beta - the value of the opponent's best move
    #   currentDepth - the current depth of the node from the initial node
    #
    # Returns: the move which benefits the opposing player the least (alpha).
    #
    def min_value(self, node, alpha, beta, currentDepth):
        # base case, maxDepth reached, return the value of the currentState
        if currentDepth == self.maxDepth:
            return node
        state = node["potential_state"]
        v = INFINITY

        # holds a list of nodes reachable from the currentState
        nodeList = []
        # loop through all legal moves for the currentState
        for move in listAllLegalMoves(state):
            # don't bother doing any move evaluations for the queen
            # unless we need to build a worker (she is in the way!)
            if move.moveType == MOVE_ANT:
                initialCoords = move.coordList[0]
                if ((getAntAt(state, initialCoords).type == QUEEN) and 
                    len(state.inventories[state.whoseTurn].ants) >= 2):
                        continue
            if move.moveType == BUILD:
                # hacky way to speed up the code by forcing building workers
                # over any other ant
                if move.buildType != WORKER:
                    continue
            # get the state that would result if the move is made
            resultingState = self.processMove(state, move)
            #create a newNode for the resulting state
            newNode = self.createNode(move, resultingState, node)
            # if a goal state has been found, stop evaluating other branches
            if newNode["state_value"] == 0.0:
                #we have a goal state, no alpha_beta evaluation is needed
                return newNode
            nodeList.append(newNode)
            
        #sort nodes from least to greatest
        sortedNodeList = sorted(nodeList, key=lambda k: k['state_value'])
        
        # throw away the last half of the list to minimize the number of nodes
        sortedNodeList = sortedNodeList[:(len(sortedNodeList)+1)/2]
        
        #holds a reference to the current best node to move to
        bestValNode = None
        
        #if it is our players turn
        if (self.playerId == state.whoseTurn):
            for tempNode in sortedNodeList:
                minValNode = self.max_value(tempNode, alpha, beta, currentDepth+1)
                #if it's our turn and we're in max_value, stay in max_value
                if v > minValNode["state_value"]:
                        bestValNode = minValNode
                        v = minValNode["state_value"]
                if v <= alpha:
                    return minValNode
                beta = min(beta, v)
        #else it is the opponents player turn
        else:
            for tempNode in sortedNodeList:
                minValNode = self.min_value(tempNode, alpha, beta, currentDepth+1)
                #if it's opponent's turn and they're in max_value, to toggle to min_value
                if v > minValNode["state_value"]:
                       bestValNode = minValNode
                       v = minValNode["state_value"]
                if v <= alpha:
                    return minValNode
                beta = min(beta, v)

        return bestValNode
    
    
    ##
    # processMove
    # Description: The processMove method looks at the current state
    # of the game and returns a copy of the state that results from
    # making the move
    #
    # Parameters:
    #   self - The object pointer
    #   currentState - The current state of the game
    #   move - The move which alters the state
    #
    # Return: The resulting state after move is made
    #
    def processMove(self, currentState, move):
        # create a copy of the state (this will be returned
        # after being modified to reflect the move)
        copyOfState = currentState.fastclone()
        
        # get a reference to the player's inventory
        playerInv = copyOfState.inventories[copyOfState.whoseTurn]
        # get a reference to the enemy player's inventory
        enemyInv = copyOfState.inventories[(copyOfState.whoseTurn+1) % 2]
        
        # player is building a constr or ant
        if move.moveType == BUILD:
            # building a constr
            if move.buildType < 0:  
                playerInv.foodCount -= CONSTR_STATS[move.buildType][BUILD_COST]
                playerInv.constrs.append(Construction(move.coordList[0], move.buildType))
            # building an ant
            else: 
                playerInv.foodCount -= UNIT_STATS[move.buildType][COST]
                playerInv.ants.append(Ant(move.coordList[0], move.buildType, copyOfState.whoseTurn))                
        # player is moving an ant
        elif move.moveType == MOVE_ANT:
            # get a reference to the ant
            ant = getAntAt(copyOfState, move.coordList[0])
            # update the ant's location after the move
            ant.coords = move.coordList[-1]
            
            # get a reference to a potential constr at the destination coords
            constr = getConstrAt(copyOfState, move.coordList[-1])
            # check to see if the ant is on a food or tunnel or hill and act accordingly
            if constr:
                # we only care about workers
                if ant.type == WORKER:
                    # if dest is food and can carry, pick up food
                    if constr.type == FOOD:
                        if not ant.carrying:
                            ant.carrying = True
                    # if dest is tunnel or hill and ant is carrying food, ditch it
                    elif constr.type == TUNNEL or constr.type == ANTHILL:
                        if ant.carrying:
                            ant.carrying = False
                            playerInv.foodCount += 1
            # get a list of the coordinates of the enemy's ants                 
            enemyAntCoords = [enemyAnt.coords for enemyAnt in enemyInv.ants]
            # contains the coordinates of ants that the 'moving' ant can attack
            validAttacks = []
            # go through the list of enemy ant locations and check if 
            # we can attack that spot and if so add it to a list of
            # valid attacks (one of which will be chosen at random)
            for coord in enemyAntCoords:
                #pythagoras would be proud
                if UNIT_STATS[ant.type][RANGE] ** 2 >= abs(ant.coords[0] - coord[0]) ** 2 + abs(ant.coords[1] - coord[1]) ** 2:
                    validAttacks.append(coord)
            # if we can attack, pick a random attack and do it
            if validAttacks:
                enemyAnt = getAntAt(copyOfState, random.choice(validAttacks))
                attackStrength = UNIT_STATS[ant.type][ATTACK]
                if enemyAnt.health <= attackStrength:
                    # just to be safe, set the health to 0
                    enemyAnt.health = 0
                    # remove the enemy ant from their inventory (He's dead Jim!)
                    enemyInv.ants.remove(enemyAnt)
                else:
                    # lower the enemy ant's health because they were attacked
                    enemyAnt.health -= attackStrength
        # move ends the player's turn
        elif move.moveType == END:
            # toggle between PLAYER_ONE (0) and PLAYER_TWO (1)
            copyOfState.whoseTurn += 1
            copyOfState.whoseTurn %= 2
        
        # return a copy of the original state, but reflects the move
        return copyOfState
    
    
    ##
    # evaluateState
    # Description: The evaluateState method looks at a state and
    # assigns a value to the state based on how well the game is
    # going for the current player
    #
    # Parameters:
    #   self - The object pointer
    #   currentState - The state to evaluate
    #
    # Return: The value of the state on a scale of 0.0 to 1.0
    # where 0.0 is a loss and 1.0 is a victory and 0.5 is neutral
    # (neither winning nor losing)
    #
    # Direct win/losses are either a technical victory or regicide
    #
    def evaluateState(self, currentState):        
        # get a reference to the player's inventory
        playerInv = currentState.inventories[currentState.whoseTurn]
        # get a reference to the enemy player's inventory
        enemyInv = currentState.inventories[(currentState.whoseTurn+1) % 2]
        # get a reference to the enemy's queen
        enemyQueen = enemyInv.getQueen()
        
        # game over (lost) if player does not have a queen
        #               or if enemy player has 11 or more food
        if playerInv.getQueen() is None or enemyInv.foodCount >= 11:
            return 0.0
        # game over (win) if enemy player does not have a queen
        #              or if player has 11 or more food
        if enemyQueen is None or playerInv.foodCount >= 11:
            return 1.0
        
        # initial state value is neutral ( no player is winning or losing )
        valueOfState = 0.5        
            
        # hurting the enemy queen is a very good state to be in
        valueOfState += 0.025 * (UNIT_STATS[QUEEN][HEALTH] - enemyQueen.health)
        
        # keeps track of the number of ants the player has besides the queen
        numNonQueenAnts = 0   
        enemyDistFromQueen = maxDist         
        
        # loop through the player's ants and handle rewards or punishments
        # based on whether they are workers or attackers
        for ant in playerInv.ants:
            if ant.type == QUEEN:
                enemyDistFromQueen = self.distClosestAnt(currentState, ant.coords)
                queenSafety = enemyDistFromQueen / maxDist
                valueOfState += queenSafety * queenSafetyWeight
            else:
                valueOfState += 0.01
                numNonQueenAnts += 1
                # Punish the AI less and less as its ants approach the enemy's queen
                valueOfState -= 0.005 * self.vectorDistance(ant.coords, enemyQueen.coords)
                            
        # ensure that 0.0 is a loss and 1.0 is a win ONLY
        if valueOfState < 0.0:
            valueOfState = 0.001 + (valueOfState * 0.0001)
        if valueOfState > 1.0:
            valueOfState =  0.999
            
        # return the value of the currentState
        # Value if our turn, otherwise 1-value if opponents turn
        # Doing 1-value is the equivalent of looking at the min value
        # since it is the best move for the opponent, and therefore the worst move
        # for our AI
        if currentState.whoseTurn == self.playerId:
            return valueOfState
        return 1-valueOfState
        
    
    ##
    #getPlacement
    #Description: The getPlacement method corresponds to the 
    #action taken on setup phase 1 and setup phase 2 of the game. 
    #In setup phase 1, the AI player will be passed a copy of the 
    #state as currentState which contains the board, accessed via 
    #currentState.board. The player will then return a list of 10 tuple 
    #coordinates (from their side of the board) that represent Locations 
    #to place the anthill and 9 grass pieces. In setup phase 2, the player 
    #will again be passed the state and needs to return a list of 2 tuple
    #coordinates (on their opponent?s side of the board) which represent
    #Locations to place the food sources. This is all that is necessary to 
    #complete the setup phases.
    #
    #Parameters:
    #   currentState - The current state of the game at the time the Game is 
    #       requesting a placement from the player.(GameState)
    #
    #Return: If setup phase 1: list of ten 2-tuples of ints -> [(x1,y1), (x2,y2),?,(x10,y10)]
    #       If setup phase 2: list of two 2-tuples of ints -> [(x1,y1), (x2,y2)]
    #
    def getPlacement(self, currentState):
        # place stuff on player's side
        if currentState.phase == SETUP_PHASE_1:    
            # get a list of coordinates for placement
            coordList = self.geneToCoords(self.genes1[self.curGeneIdx], 0)
            # return the first 11 coordinates (tunnel+hill+grass)
            return coordList[:11]
        # place stuff on opponent's side
        elif currentState.phase == SETUP_PHASE_2:
            # reset the first move boolean so that the state gets printed out
            # when the first move is made
            self.firstMove = True
            # get a list of coordinates for potential food placement
            coordList = self.geneToCoords(self.genes2[self.curGeneIdx], 6)
            # holds the coordinates for the two foods placed on the opponent's side
            foodCoords = []
            # Find the first two coordinates that are not occupied by constructions
            for c in coordList:
                if getConstrAt(currentState, c) is None:
                    foodCoords.append(c)
                    # as sooon as two valid coordinates are found, return them
                    if len(foodCoords) == 2:
                        return foodCoords
        # this should never be reached                
        return [(0, 0)]
            
    
    ##
    #getMove
    #Description: The getMove method corresponds to the play phase of the game 
    #and requests from the player a Move object. All types are symbolic 
    #constants which can be referred to in Constants.py. The move object has a 
    #field for type (moveType) as well as field for relevant coordinate 
    #information (coordList). If for instance the player wishes to move an ant, 
    #they simply return a Move object where the type field is the MOVE_ANT constant 
    #and the coordList contains a listing of valid locations starting with an Ant 
    #and containing only unoccupied spaces thereafter. A build is similar to a move 
    #except the type is set as BUILD, a buildType is given, and a single coordinate 
    #is in the list representing the build location. For an end turn, no coordinates 
    #are necessary, just set the type as END and return.
    #
    #Parameters:
    #   currentState - The current state of the game at the time the Game is 
    #       requesting a move from the player.(GameState)   
    #
    #Return: Move(moveType [int], coordList [list of 2-tuples of ints], buildType [int]
    #
    def getMove(self, currentState):
        # print the state as ascii on the first move
        if self.firstMove:            
            asciiPrintState(currentState)
            self.firstMove = False
        # save our id
        self.playerId = currentState.whoseTurn
        #create the initial node to analyze
        initNode = self.createNode(None, currentState, None)
        return self.alpha_beta_search(initNode)
    
    
    ##
    #getAttack
    #Description: The getAttack method is called on the player whenever an ant completes 
    #a move and has a valid attack. It is assumed that an attack will always be made 
    #because there is no strategic advantage from withholding an attack. The AIPlayer 
    #is passed a copy of the state which again contains the board and also a clone of 
    #the attacking ant. The player is also passed a list of coordinate tuples which 
    #represent valid locations for attack. Hint: a random AI can simply return one of 
    #these coordinates for a valid attack. 
    #
    #Parameters:
    #   currentState - The current state of the game at the time the Game is requesting 
    #       a move from the player. (GameState)
    #   attackingAnt - A clone of the ant currently making the attack. (Ant)
    #   enemyLocation - A list of coordinate locations for valid attacks (i.e. 
    #       enemies within range) ([list of 2-tuples of ints])
    #
    #Return: A coordinate that matches one of the entries of enemyLocations. ((int,int))
    ##
    def getAttack(self, currentState, attackingAnt, enemyLocations):
        #Attack a random enemy.
        return enemyLocations[random.randint(0, len(enemyLocations) - 1)]
        
        
    ##
    #registerWin
    #Description: The last method, registerWin, is called when the game ends and simply 
    #indicates to the AI whether it has won or lost the game. This is to help with 
    #learning algorithms to develop more successful strategies.
    #
    #Parameters:
    #   hasWon - True if the player has won the game, False if the player lost. (Boolean)
    #
    def registerWin(self, hasWon):        
        # increment the number of completed games
        self.gamesPlayed += 1
        
        # keep track of wins as the fitness evaluation of agene
        if hasWon:
            # increment the fitness value of the gene
            self.fitness[self.curGeneIdx] += 1.0/GAMES_PER_GENE            
        # if the gene has been fully evaluated
        if self.gamesPlayed == GAMES_PER_GENE:
            # move to the next gene
            self.curGeneIdx += 1
            
            # if the entire population has been evaluated
            if self.curGeneIdx == POPULATION_SIZE:
                # generate the next generation of genes for both populations
                self.genes1 = self.getNextGeneration(self.genes1)
                self.genes2 = self.getNextGeneration(self.genes2)
                # reset the fitness scores
                self.fitness = [0] * POPULATION_SIZE
                # reset the gene index
                self.curGeneIdx = 0
                
            # reset the number of completed games
            self.gamesPlayed = 0
