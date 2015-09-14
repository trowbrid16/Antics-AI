  # -*- coding: latin-1 -*-
import random
from Player import *
from Constants import *
from Construction import CONSTR_STATS
from Ant import UNIT_STATS
from Move import Move
from GameState import addCoords
from AIPlayerUtils import *
from random import randint

##
#StudentAIPlayer
#Authors: Kenny Trowbridge, Sean Pierson
#
#
#Description: The responsbility of this class is to interact with the game by
#deciding a valid move based on a given game state. This class has methods that
#will be implemented by students in Dr. Nuxoll's AI course.
#
#Variables:
#   playerId - The id of the player.
#
##
class AIPlayer(Player):

    #__init__
    #Description: Creates a new Player
    #
    #Parameters:
    #   inputPlayerId - The id to give the new player (int)
    ##
    def __init__(self, inputPlayerId):
        super(AIPlayer,self).__init__(inputPlayerId, "KennyAndSeanHW1")

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
    #coordinates (on their opponent�s side of the board) which represent
    #Locations to place the food sources. This is all that is necessary to
    #complete the setup phases.
    #
    #Parameters:
    #   currentState - The current state of the game at the time the Game is
    #       requesting a placement from the player.(GameState)
    #
    #Return: If setup phase 1: list of ten 2-tuples of ints -> [(x1,y1), (x2,y2),�,(x10,y10)]
    #       If setup phase 2: list of two 2-tuples of ints -> [(x1,y1), (x2,y2)]
    ##
    def getPlacement(self, currentState):
        if currentState.phase == SETUP_PHASE_1:
            return [(2,1), (7,1), (0,3), (1,3), (2,3), (3,3), (0,0), (6,3), (7,3), (8,3), (9,3)]

        #this else if is what sets up the food. it only lets us place 2 pieces
        #of food
        elif currentState.phase == SETUP_PHASE_2:
            x = 0
            y = 6
            result = []
            listToCheck = [4,5,3,6,2,7,1,8,0,9]

            for y in [6,7]:

                for num in listToCheck:
                    if(getConstrAt(currentState, (num, y)) == None):
                        result.append((num, y))
                        if(len(result)== 2):
                            return result

        else:
            return None

    ##
    #  HELPER METHODS
    ##

    def getDistance(self, src, dst):
        dist = (-1,-1) #initial value, should never return
        if src[0] < dst[0]:
            dist = (dst[0] - src[0], dist[1])
        else:
            dist = (src[0] - dst[0], dist[1])
        if src[1] < dst[1]:
            dist = (dist[0], dst[1] - src[1])
        else:
            dist = (dist[0], src[1] - dst[1])
        return dist

    #getNextStep
    #
    #Description:
    #The getNextStep method is a helper method used in getMove to calculate
    #a transitionary route to a location when that location is not
    #immeidately adjacent to an ant
    #
    #Parameters:
    #   currentState - The current state of the game at the time the Game is
    #       requesting a move from the player.(GameState)
    #   src - The starting point of the ant
    #   dst - The desired end point of the ant
    #   movement - The number of movement points to be used
    #
    #Return: List of coordinates for the ant to follow
    def getNextStep(self, currentState, src, dst, movement):
        moveList = listAllMovementPaths(currentState, src, movement)

        #calculate total distance between src and dst
        distance = self.getDistance(src, dst)

        #keeps track of result of various paths and see which is best
        path = []
        for m in moveList:
            move = m[-1]#get the last coordinate in move
            #calculate distance reduction
            temp = self.getDistance(move, dst)
            if temp[0] <= distance[0] and temp[1] <= distance[1]:
                path = m
                distance = temp
            #check the validity of that path
            for p in path[1:]:

                if(getAntAt(currentState, p) != None):
                    #bad path, reset to not move
                    path = [src]
        return path


    ##
    #Function: nearestFoodOrHill
    #Parameters(currentState, antCoord, lookingFor)
    #       currentState: the current GameState
    #       antCoord: Where the ant is searching from
    #       lookingFor: What item youre looking for. (ANTHILL, TUNNEL, FOOD) only
    #
    #returns: a coordinate touple of the nearest thing you were looking for
    #
    #
    ##
    def nearestFoodOrHill(self, currentState, antCoord, lookingFor):
        if(lookingFor[0] == -1):
            foodHillLocList = getConstrList(currentState, None, [(FOOD)])
        if(lookingFor[0] == -3):
            foodHillLocList = getConstrList(currentState, PLAYER_TWO, [(TUNNEL)])
        if(lookingFor[0] == -4):
            foodHillLocList = getConstrList(currentState, PLAYER_TWO, [(ANTHILL)])

        shortest = stepsToReach(currentState, antCoord, foodHillLocList[0].coords)
        tester = 0
        for x in range(0, len(foodHillLocList), 1):
            if(shortest > stepsToReach(currentState, antCoord, foodHillLocList[x].coords)):
                shortest = stepsToReach(currentState, antCoord, foodHillLocList[x].coords)
                tester = x
        return foodHillLocList[tester].coords



    #getMove
    #
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
        mergedList = getAntList(currentState, PLAYER_TWO, [(WORKER), (QUEEN), (DRONE)])
        workers = getAntList(currentState, PLAYER_TWO, [(WORKER)])
        drones = getAntList(currentState, PLAYER_TWO, [(DRONE)])
        foodLocList = getConstrList(currentState, None, [(FOOD)])
        homes = getConstrList(currentState, PLAYER_TWO, [(ANTHILL), (TUNNEL)])
        buildMoves = listAllBuildMoves(currentState)

        #For each ant we own
        for ant in mergedList:
            #Ant's current coordinates
            antCoords = ant.coords
            hillCoords = getConstrList(currentState, PLAYER_TWO, [(ANTHILL)])[0].coords
            if(ant.hasMoved == False):
                if(ant.type == QUEEN):
                    #move towards grass piece
                    if(ant.coords != (0,0)):
                        moveList = self.getNextStep(currentState, antCoords, (0,0), 2)
                        return Move(MOVE_ANT, moveList, None)

                if(ant.type == WORKER ):
                    #Movement paths of a worker ant
                    paths = listAllMovementPaths(currentState, antCoords, 2)
                    if(ant.carrying == False):
                        #find the closest food
                        nearestFood = self.nearestFoodOrHill(currentState, antCoords, [(FOOD)])
                        #food not accessible, move towards food
                        moveList = self.getNextStep(currentState, antCoords, nearestFood, 2)
                        return Move(MOVE_ANT, moveList, None)

                    if(ant.carrying == True):
                        #Return home if carrying food
                        #find the closest nest, Tunnel or Hill
                        nearestHill = self.nearestFoodOrHill(currentState, antCoords, [(ANTHILL)])
                        nearestTunnel = self.nearestFoodOrHill(currentState, antCoords, [(TUNNEL)])
                        if(stepsToReach(currentState, antCoords, nearestHill) > stepsToReach(currentState, antCoords, nearestTunnel)):
                            moveList = self.getNextStep(currentState, antCoords, nearestTunnel, 2)
                        else:
                            moveList = self.getNextStep(currentState, antCoords, nearestHill, 2)
                        return Move(MOVE_ANT, moveList, None)

                if(ant.type == DRONE):
                    enemyHill = getConstrList(currentState, PLAYER_ONE, [(ANTHILL)])[0].coords
                    enemyQueen = getAntList(currentState, PLAYER_ONE, [(QUEEN)])[0].coords

                    if(antCoords == enemyHill):
                        pass
                    if(getAntAt(currentState, enemyHill) != None and antCoords != enemyHill):
                        moveList = self.getNextStep(currentState, antCoords, enemyQueen, 3)
                        return Move(MOVE_ANT, moveList, None)
                    elif(getAntAt(currentState, enemyHill) == None):
                        moveList = self.getNextStep(currentState, antCoords, enemyHill, 3)
                        return Move(MOVE_ANT, moveList, None)
                    if(antCoords != enemyHill):
                        moveList = self.getNextStep(currentState, antCoords, enemyHill, 3)
                        return Move(MOVE_ANT, moveList, None)

                #Build Stage
                for b in range(0, len(buildMoves), 1):
                    if(buildMoves[b].buildType == SOLDIER and len(drones) >= 2 and len(soldiers) < 2):
                        return buildMoves[b]
                    if(buildMoves[b].buildType == DRONE):
                        return buildMoves[b]
                    if(len(workers) < 2 and buildMoves[b].buildType == WORKER):
                        return buildMoves[b]
        return Move(END, None, None)

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
        for e in enemyLocations:
            trucktion = getConstrAt(currentState, e)
            if(trucktion == None):
                return e
            elif(trucktion.type == ANTHILL or trucktion.type == QUEEN):
                return e
        return enemyLocations[0]
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
        #method templaste, not implemented
        pass
