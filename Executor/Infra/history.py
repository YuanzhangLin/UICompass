from Infra.infra import Event



class Screen:
    def __init__(self):
        self.hierachy=None
        self.description = ""


    def add_description(self, description):
        self.description = description

    def add_hierarchy(self, hierarchy):
        self.hierarchy = hierarchy

    def __str__(self):
        return f"Screen(description={self.description}, hierarchy={self.hierarchy})"

class History:
    def __init__(self):
       self.histories = []

    def add_history(self,screen, action):
        self.histories.append((screen,action))

    def __str__(self):
       return f"History(screen={self.screen}, action={self.action})"