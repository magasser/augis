"""
Authors: Manuel Gasser, Julian Haldimann
Created: 25.03.2021
Last Modified: 13.06.2021
"""


class Pid:
    # Proportional Const
    KP = 0.99
    # Integral Const
    KI = 0.0002
    # Differential Const
    KD = 0.1

    # Max Boundary
    MAX = 30000
    # Min Boundary
    MIN = -30000

    def __init__(self):
        # Accumulated Error
        self.i = 0
        # Prior Sample Time
        self.t0 = 0
        # Prior Error
        self.e0 = 0
        # Difference between desired and measured value
        self.e1 = 0

    """
    Calculate the corrective value
    
    :param r: desired value
    :param x: measured value
    :param t: 
    """

    def control(self, r, x, t):

        if r is not x:

            self.e1 = r - x
            # Calculate delta t
            dt = self.t0 - t
            # Accumulate Integral
            self.i = (self.i + self.e1) * dt
            # Stop Windup to + infinity
            if self.i > Pid.MAX:
                self.i = Pid.MAX
            # Stop Windup to - infinity
            elif self.i < Pid.MIN:
                self.i = Pid.MIN
            # Differentiate
            de = (self.e1 - self.e0) / dt
            self.e0 = self.e1
            # Corrective value
            return (Pid.KP * self.e1) + (Pid.KI * self.i) + (Pid.KD * de)
        else:
            return 0
