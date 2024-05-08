import numpy as np
import matplotlib.pyplot as plt
import modules.koalaCommands as koala
import time

class StagePattern(object):
    def __init__(self, KoalaHost, D: int = None, H: int = None, dD: int = None, dH: int = None, R: int = None, dR: int = None, patternType="snake", liveDisplay=False) -> None:
        """
        Initializes the StagePattern object.

        Args:
            KoalaHost (str): The host name of the Koala.
            D (int, optional): The dimension of the pattern in the y-direction. Defaults to None.
            H (int, optional): The dimension of the pattern in the x-direction. Defaults to None.
            dD (int, optional): The step size in the y-direction. Defaults to None.
            dH (int, optional): The step size in the x-direction. Defaults to None.
            R (int, optional): The radius of the pattern. Defaults to None.
            dR (int, optional): The step size in the radius direction. Defaults to None.
            patternType (str, optional): The type of pattern to generate. Defaults to "snake".
            liveDisplay (bool, optional): Whether to display the pattern live. Defaults to False.
        """
        self.KoalaHost = KoalaHost
        self.D = D
        self.H = H
        self.dD = dD
        self.dH = dH
        if patternType not in ('snake', 'spiral', 'line', 'circleSnake', 'circleLine', "snail"):
            raise ValueError('Invalid pattern type')
        self.patternType = patternType
        #self.position_center = [51000,72000] # or get current position 
        self.position_center = [52219,70746] # or get current position 
        self.pattern = self.createPattern()
        self.patternIndex = 0
        self.maxIndex = len(self.pattern)
        self.liveDisplay = liveDisplay
        self.fig = None
        self.ax = None
        if liveDisplay:
            plt.ion()
            self.plotPattern(currentPosition=0)

    def createPattern(self):
        """
        Creates the pattern based on the specified pattern type.

        Returns:
            list: A list of (x, y) coordinates representing the pattern.
        """
        if self.patternType == 'snake':
            return self.snakePattern()
        elif self.patternType == 'spiral':
            return self.spiralPattern()
        elif self.patternType == 'line':
            return self.linePattern()
        elif self.patternType == 'circleSnake':
            return self.circleSnakePattern()
        elif self.patternType == 'circleLine':
            return self.circleLinePattern()
        elif self.patternType == 'snail':
            return self.snailPattern()
        else:
            raise ValueError('Invalid pattern type')

    def resetPattern(self):
        """
        Resets the pattern index to 0 and moves the stage to the first position in the pattern.
        If live display is enabled, it plots the pattern with the current position highlighted.
        """
        self.patternIndex = 0
        self.moveto(self.pattern[self.patternIndex])
        if self.liveDisplay:
            self.plotPattern(currentPosition=self.patternIndex)

    def isRunning(self):
        """
        Checks if the pattern manager is currently running.

        Returns:
            bool: True if the pattern manager is running, False otherwise.
        """
        if self.patternIndex < self.maxIndex:
            return True
        else:
            return False

    def getPatternSize(self):
        """
        Returns the size of the pattern.

        Returns:
            int: The size of the pattern.
        """
        return len(self.pattern)

    def moveto(self,position):
        self.position = position
        
        absMove = True
        mvX = True
        mvY = True 
        mvZ = False
        mvTh = False
        
        distX = float(position[0])
        distY = float(position[1])
        distZ = 0.0 
        distTh = 0.0  
        
        accuracyX = 1.0
        accuracyY = 1.0 
        accuracyZ = 1.0 
        accuracyTh = 1.0
        
        waitEnd = True  # Wait for the movement to complete
        
        success = self.KoalaHost.MoveAxes(absMove, mvX, mvY, mvZ, mvTh, distX, distY, distZ, distTh, accuracyX, accuracyY, accuracyZ, accuracyTh, waitEnd) # Perform the movement
        print(success)

    def nextPosition(self):
        """
        Moves to the next position in the pattern.

        This method increments the `patternIndex` by 1 and moves the stage to the corresponding position in the `pattern` list.
        If `liveDisplay` is True, it also updates the plot to show the current position.
        """
        print(f'Going to position {self.patternIndex+1}/{self.maxIndex}')
        if self.patternIndex + 1 < self.maxIndex:
            self.patternIndex += 1
            self.moveto(self.pattern[self.patternIndex])
            if self.liveDisplay:
                self.plotPattern(currentPosition=self.patternIndex)
        else:
            print('Pattern finished')
            if self.liveDisplay:
                self.fig.canvas.flush_events()

    def snakePattern(self):
        """
        Generates a snake pattern on the stage.

        The snake pattern consists of a series of points forming a zigzag pattern.
        The pattern starts from the specified position and extends in the x and y directions
        based on the given dimensions and step sizes.

        Returns:
            list: A list of (x, y) coordinates representing the snake pattern.
        """
        pattern = []
        nRow = self.D // self.dD
        nCols = self.H // self.dH
        corner = self.position_center
        corner[0] -= self.H / 2
        corner[1] -= self.D / 2
        for i in range(nRow):  # iterate over lines
            y = i * self.dD + corner[1]
            if i % 2 == 0:
                for j in range(nCols):
                    x = j * self.dH + corner[0]
                    pattern.append((x, y))
            else:
                for j in range(nCols):
                    x = (nCols - j - 1) * self.dH + corner[0]
                    pattern.append((x, y))
        return pattern

    def spiralPattern(self):
        """
        Generates a spiral pattern of points around a center point. Spiral starts 
        from the outwards and moves inwards.

        Returns:
            list: A list of (x, y) coordinates representing the spiral pattern.
        """
        pattern = []
        R = self.D / 2
        dR = self.dD / 2
        nCircles = int(R // dR)
        startpoint = self.position_center
        for i in range(nCircles):
            r = R - i * dR
            nPoints = int(2 * np.pi * r / dR)
            for j in range(nPoints):
                x = startpoint[0] - r * np.cos(2 * np.pi * j / nPoints)
                y = startpoint[1] - r * np.sin(2 * np.pi * j / nPoints)
                pattern.append((x, y))
        return pattern

    def linePattern(self):
        """
        Generates a line pattern based on the given parameters.

        Returns:
            list: A list of tuples representing the coordinates of the pattern points.
        """
        pattern = []
        nRow = self.D // self.dD
        nCols = self.H // self.dH
        corner = self.position_center
        corner[0] -= self.H / 2
        corner[1] -= self.D / 2
        for i in range(nRow):
            for j in range(nCols):
                x = j * self.dH + corner[0]
                y = i * self.dD + corner[1]
                pattern.append((x, y))
        return pattern

    def circleLinePattern(self):
        """
        Generates a circle line pattern based on the given parameters.

        Returns:
            list: A list of tuples representing the coordinates of the pattern points.
        """
        pattern = []
        R = self.D / 2
        dR = self.dD / 2
        corner = self.position_center
        nRow = int(self.D / dR)
        for i in range(-(nRow // 2), nRow // 2 + 1):
            r = R - dR / 4 - (nRow // 2 - abs(i)) * dR
            d = 2 * np.sqrt(R ** 2 - r ** 2)
            nPoints = 2 * (int(d / dR) // 2) + 1
            y = i * self.dD + corner[1]
            for j in range(-nPoints // 2, nPoints // 2 + 1):
                x = corner[0] + j * self.dD
                pattern.append((x, y))
        return pattern

    def circleSnakePattern(self):
        """
        Generates a circle snake pattern based on the given parameters.

        Returns:
            list: A list of tuples representing the coordinates of the pattern points.
        """
        pattern = []
        R = self.D / 2
        dR = self.dD / 2
        corner = self.position_center
        nRow = int(self.D / dR)
        for i in range(-(nRow // 2), nRow // 2 + 1):
            r = R - dR / 4 - (nRow // 2 - abs(i)) * dR
            d = 2 * np.sqrt(R ** 2 - r ** 2)
            nPoints = 2 * (int(d / dR) // 2) + 1
            y = i * self.dD + corner[1]
            for j in range(-nPoints // 2, nPoints // 2 + 1):
                if i % 2 == 0:
                    x = corner[0] + j * self.dD
                else:
                    x = corner[0] + -(j + 1) * self.dD
                pattern.append((x, y))
        return pattern

    def snailPattern(self):
        nRow = self.D // self.dD
        if nRow%2!=0:
            print("Even number")
            nRow = 2 * (nRow//2 + 3)
        else:
            nRow = 2 * (nRow//2 + 3)
        center = self.position_center
        iSteps = 1
        jSteps = 1
        pattern = [center]
        for k in range(nRow//2):
            print(iSteps,jSteps)
            if k%2==0:
                position = pattern[-1]
                for i in range(iSteps):
                    pattern.append((position[0]+(i+1)*self.dD,position[1]))
                for j in range(jSteps):
                    pattern.append((position[0]+iSteps*self.dD,position[1]-(j+1)*self.dD))
            else:
                position = pattern[-1]
                for i in range(iSteps):
                    pattern.append((position[0]-(i+1)*self.dD,position[1]))
                for j in range(jSteps):
                    pattern.append((position[0]-iSteps*self.dD,position[1]+(j+1)*self.dD))
            iSteps +=1
            jSteps +=1
        position = pattern[-1]
        for i in range(iSteps-1):
            pattern.append((position[0]+(i+1)*self.dD,position[1]))
        #pattern = pattern[::-1]
        #print(pattern)
        return pattern

    def plotPattern(self, currentPosition=None):
        """
        Plots the pattern.

        Args:
            currentPosition (int, optional): The current position index. Defaults to None.
        """
        pattern = np.array(self.pattern)
        if self.fig is None or self.ax is None:
            fig, ax = plt.subplots(figsize=(5, 5))
            self.fig = fig
            self.ax = ax
            ax.set_xlabel('horizontal position')
            ax.set_ylabel('vertical position')
            ax.set_title('Stage Pattern')
            ax.invert_yaxis()
            ax.set_aspect('equal')
            if self.liveDisplay:
                colorDots = 'gray'
                colorLines = 'gray'
            else:
                colorDots = 'red'
                colorLines = 'blue'
            plt.scatter(pattern[:, 0], pattern[:, 1], color=colorDots)
            plt.plot(pattern[:, 0], pattern[:, 1], color=colorLines)
        else:
            colorDots = 'red'
            colorLines = 'blue'
            fig = self.fig
            ax = self.ax
            ax.set_title(f'Stage Pattern, Current Position {currentPosition}/{len(pattern)}')
            ax.scatter(pattern[currentPosition, 0], pattern[currentPosition, 1], color=colorDots)
            if currentPosition < len(pattern) - 1:
                ax.plot(pattern[currentPosition:currentPosition + 2, 0], pattern[currentPosition:currentPosition + 2, 1], color=colorLines)
        if not self.liveDisplay:
            plt.show()
        else:
            fig.canvas.draw()
            fig.canvas.flush_events()



# # Create an instance of StagePattern for each pattern type and plot the pattern
#snake_pattern = StagePattern("KoalaHost", D=6, dD=1, patternType="snail", liveDisplay=False)
#snake_pattern.plotPattern()

#spiral_pattern = StagePattern("KoalaHost", D=100, dD=10, patternType="spiral", liveDisplay=True)
# spiral_pattern.plotPattern()

# line_pattern = StagePattern("KoalaHost", D=100, H=100, dD=10, dH=10, patternType="line", liveDisplay=True)
# line_pattern.plotPattern()

# circle_snake_pattern = StagePattern("KoalaHost", D=100, dD=10, patternType="circleSnake", liveDisplay=True)
# circle_snake_pattern.plotPattern()

# circle_line_pattern = StagePattern("KoalaHost", D=100, dD=10, patternType="circleLine", liveDisplay=True)
# circle_line_pattern.plotPattern()

# # Create an instance of StagePattern for each pattern type and run the pattern with live view
# snake_pattern = StagePattern("KoalaHost", D=100, H=100, dD=10, dH=10, patternType="snake", liveDisplay=True)
# while snake_pattern.isRunning():
#     snake_pattern.nextPosition()
#     time.sleep(0.01)  # Delay between each position

# spiral_pattern = StagePattern("KoalaHost", D=100, dD=10, patternType="spiral", liveDisplay=True)
# while spiral_pattern.isRunning():
#     spiral_pattern.nextPosition()
#     time.sleep(0.01)  # Delay between each position

# line_pattern = StagePattern("KoalaHost", D=100, H=100, dD=10, dH=10, patternType="line", liveDisplay=True)
# while line_pattern.isRunning():
#     line_pattern.nextPosition()
#     time.sleep(0.01)  # Delay between each position

# circle_snake_pattern = StagePattern("KoalaHost", D=100, dD=10, patternType="circleSnake", liveDisplay=True)
# while circle_snake_pattern.isRunning():
#     circle_snake_pattern.nextPosition()
#     time.sleep(0.01)  # Delay between each position

# circle_line_pattern = StagePattern("KoalaHost", D=100, dD=10, patternType="circleLine", liveDisplay=True)
# while circle_line_pattern.isRunning():
#     circle_line_pattern.nextPosition()
#     time.sleep(0.01)  # Delay between each position