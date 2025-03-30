from head import *
from enum import Enum
from collections import deque
import random
import math
import time
import copy

class TimeKeeper:
    def __init__(self, time_threshold):
        self.start_time = time.time()
        self.time_threshold = time_threshold / 1000
    
    def isTimeOver(self):
        current_time = time.time()
        elapsed_time = current_time - self.start_time
        return elapsed_time >= self.time_threshold
        

H = 6
W = 7

class WinningStatus(Enum):
    WIN = 1
    LOSE = 2
    DRAW = 3
    NONE = 4

class State:
    def __init__(self):
        self.is_first = True
        self.my_board = 0
        self.all_board = 0
        self.winning_status = WinningStatus.NONE
        
    def isWinner(self, board):
        tmp_board = board & (board >> 7)
        if (tmp_board & (tmp_board >> 14)) != 0:
            return True
        tmp_board = board & (board >> 6)
        if (tmp_board & (tmp_board >> 12)) != 0:
            return True
        tmp_board = board & (board >> 8)
        if (tmp_board & (tmp_board >> 16)) != 0:
            return True
        tmp_board = board & (board >> 1)
        if (tmp_board & (tmp_board >> 2)) != 0:
            return True
        return False
        
        
    def isDone(self):
        return self.winning_status != WinningStatus.NONE
    
    def advance(self, action):
        self.my_board ^= self.all_board
        self.is_first = not self.is_first
        new_all_board = self.all_board | (self.all_board + (1 << (action * 7)))
        self.all_board = new_all_board
        filled = 0b0111111011111101111110111111011111101111110111111
        if self.isWinner(self.my_board ^ self.all_board):
            self.winning_status = WinningStatus.LOSE
        elif self.all_board == filled:
            self.winning_status = WinningStatus.DRAW
        
    def legalActions(self):
        actions = []
        possible = self.all_board + 0b0000001000000100000010000001000000100000010000001
        filter = 0b0111111
        for x in range(W):
            if (filter & possible) != 0:
                actions.append(x)
            filter <<= 7
        return actions
    
    def getWinningStatus(self):
        return self.winning_status
    
    def __str__(self):
        result = ""
        if self.isDone():
            result = "Game finished\n"
        elif self.is_first:
            result = f"{RED}your turn\n"
        else:
            result = f"{BLUE}bot's turn\n"
            
        for x in range(W):
            result += NUMBERS[x]
        result += '\n'
        for y in range(H - 1, -1, -1):
            for x in range(W):
                index = x * (H + 1) + y
                c = BLACK
                if ((self.my_board >> index) & 1) != 0:
                    c = RED if self.is_first else BLUE
                elif (((self.all_board ^ self.my_board) >> index) & 1) != 0:
                    c = BLUE if self.is_first else RED
                result += c
            result += '\n'
        return result

def randomAction(state):
    legal_actions = state.legalActions()
    return legal_actions[random.randint(0,len(legal_actions)-1)]


def playout(state):
    if state.getWinningStatus() == WinningStatus.WIN:
        return 1.0
    elif state.getWinningStatus() == WinningStatus.LOSE:
        return 0.0
    elif state.getWinningStatus() == WinningStatus.DRAW:
        return 0.5
    else:
        state.advance(randomAction(state))
        return 1.0-playout(state)

C = 1.0
EXPAND_THRESHOLD = 1.0

class Node:
    def __init__(self,state):
        self.state = state
        self.w = 0.0
        self.child_nodes = []
        self.n = 0
    
    def evaluate(self):
        if self.state.isDone():
            value = 0.5
            if self.state.getWinningStatus() == WinningStatus.WIN:
                value = 1.0
            elif self.state.getWinningStatus() == WinningStatus.LOSE:
                value = 0.0
            
            self.w += value
            self.n += 1
            return value
        
        if not self.child_nodes:
            state_copy = copy.deepcopy(self.state)
            value = playout(state_copy)
            self.w += value
            self.n += 1
            
            if self.n == EXPAND_THRESHOLD:
                self.expand()
            
            return value
        else:
            value = 1.0-self.nextChildNode().evaluate()
            self.w += value
            self.n += 1
            return value
        
    def expand(self):
        legal_actions = self.state.legalActions()
        self.child_nodes = []
        for action in legal_actions:
            new_state = copy.deepcopy(self.state)
            new_state.advance(action)
            self.child_nodes.append(Node(new_state))
    
    def nextChildNode(self):
        for child_node in self.child_nodes:
            if child_node.n == 0:
                return child_node
        
        t = sum(child_node.n for child_node in self.child_nodes)
        best_value = float("-inf")
        best_action_index = -1
        for i,child_node in enumerate(self.child_nodes):
            ucb1_value = 1.0-child_node.w/child_node.n+C*math.sqrt(2.0*math.log(t)/child_node.n)
            if ucb1_value > best_value:
                best_action_index = i
                best_value = ucb1_value
        
        return self.child_nodes[best_action_index]
    
def mctsActionsWithTimeThreshold(state,time_threshold):
    root_node = Node(state)
    root_node.expand()
    time_keeper = TimeKeeper(time_threshold)
    cnt = 0
    while True:
        if time_keeper.isTimeOver():
            break
        root_node.evaluate()
        cnt += 1
    
    legal_actions = state.legalActions()
    best_action_searched_number = -1
    best_action_index = -1
    assert len(legal_actions) == len(root_node.child_nodes)
    for i,child_node in enumerate(root_node.child_nodes):
        n = child_node.n
        if n > best_action_searched_number:
            best_action_index = i
            best_action_searched_number = n
    
    return legal_actions[best_action_index]
            
    
            

async def playGame(ctx):
    state = State()
    message = await ctx.send("Wait a moment...")
    for num in NUMBERS:
        await message.add_reaction(num)
            
    await message.edit(content=state)
    
    while not state.isDone():
        reaction = None
        
        legal_emoji = []
        for legal_action in state.legalActions():
            legal_emoji.append(NUMBERS[legal_action])
        
        while True:
            reaction,_ = await bot.wait_for('reaction_add')
            if reaction.emoji in legal_emoji:
                break
            else:
                await message.remove_reaction(reaction.emoji,ctx.author)
        
        await message.remove_reaction(reaction.emoji,ctx.author)
        action = NUMBERS.index(reaction.emoji)
        state.advance(action)
        await message.edit(content=state)
        if state.isDone():
            if state.getWinningStatus() == WinningStatus.WIN:
                await ctx.send("YOU LOSE...")
            elif state.getWinningStatus() == WinningStatus.LOSE:
                await ctx.send("YOU WIN!!")
            else:
                await ctx.send("DRAW")
            break
        
        #action = randomAction(state)
        action = mctsActionsWithTimeThreshold(state,500)
        state.advance(action)
        await message.edit(content=state)
        if state.isDone():
            if state.getWinningStatus() == WinningStatus.WIN:
                await ctx.send("YOU WIN!!")
            elif state.getWinningStatus() == WinningStatus.LOSE:
                await ctx.send("YOU LOSE...")
            else:
                await ctx.send("DRAW")
            break
        
        for num in range(W):
            if not num in state.legalActions():
                await message.remove_reaction(NUMBERS[num],bot.user)