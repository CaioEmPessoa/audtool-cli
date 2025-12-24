import subprocess
from getkey import getkey, keys
import threading
import re
import os
from time import sleep

HELP = False
PAGE_SIZE = 15
ACTIONS = {
    "NONE" :      " ",
    "EXIT" :      "&",
    "SEARCH" :    "?",
    "JUMPID" :    ":",
    "ACTION" :    ">"
}

class audTool():
    def __init__(self):
        super().__init__()

        self.currentPageNumb = 1
        self.songsArray = [
            # {
                # songName:  str
                # songIndex: int
            # }
        ]
        self.allSongs = []
        self.indexingSongs = True
        self.running = True

        self.action = ACTIONS["NONE"]
        self.generalInput = []

        subprocess.run("clear")

        self.loadList()

        threading.Thread(target=self.loadAllSongs).start()
        threading.Thread(target=self.handleInput).start()
        threading.Thread(target=self.start).start().join()

        self.start()

    def start(self):
        while self.running:
            self.loadList() # Load info that will be printed with printInfo.
            # print(f"\033[1J\n{self.printInfo()}", end="", flush=True) # prints the info.
            print(self.printInfo()) # prints the info.
            sleep(0.01)

    def execShell(self, command):
        output = subprocess.check_output(command, shell=True)
        return output

    def loadAllSongs(self):
        # change into audtool --playlist-display
        i = 1
        while (i <= self.songAmmnt):
            self.allSongs.append(
                {
                    "songName": self.execShell(f"audtool --playlist-song {i}"),
                    "songIndex": i
                }
            )
            i+=1

        self.indexingSongs = False

    def loadList(self):
        self.songAmmnt = int(self.execShell("audtool --playlist-length"))
        self.songsArray = [] # clear songsArray before updating it

        # Populate songsArray list
        lastIndex = PAGE_SIZE + self.currentPageNumb-1
        i = self.currentPageNumb
        while (i <= lastIndex):
            self.songsArray.append(
                {
                    "songName": self.execShell(f"audtool --playlist-song {i}"),
                    "songIndex": i
                }
            )
            i+=1

    def printInfo(self):
        info = []

        info.append("====== AUDTOOL-CLI ======")
        if (self.indexingSongs):
            info.append("Indexing all songs... Search not enabled.")

        for i in self.songsArray:
            selected = False
            if (self.songsArray.index(i) == 0):
                selected = True

            info.append(f"{">" if selected else ""} {i["songIndex"]} - {i["songName"]}")

        info.append(f"Songs in Playlist: {self.songAmmnt}")
        info.append("")

        info.append(" ----- HELP ----- ")
        info.append(f" {ACTIONS["EXIT"]} -> Exits the program")
        info.append(f" {ACTIONS["JUMPID"]} -> Jump to this id on playlist")
        info.append(f" {ACTIONS["SEARCH"]} -> Search songs by name ({"Disabled" if self.indexingSongs else "Enabled"})")
        info.append(f" {ACTIONS["ACTION"]} -> Play or Queue the song (followed by a q or a p)")

        info.append(f"> {"".join(self.generalInput)}")
        info.append("\n")
        return "\n".join(info)

    def searchByString(self):
        re.search()

    def handleInput(self):
        while self.running:
            key = getkey()

            # match actions. Cannot be inside of a match-case.
            # for some reason ...
            if (key == ACTIONS["EXIT"]):
                os._exit(1)

            elif (key == ACTIONS["JUMPID"]) : # SEARCH BY ID
                self.generalInput.append(key)
                self.action = "JUMPID"

            elif (key == ACTIONS["SEARCH"]): # SEARCH BY STRING
                self.generalInput.append(key)
                if not self.indexingSongs:
                    self.action = "SEARCH"

            elif (key == ACTIONS["ACTION"]): # PLAY OR QUEUE
                self.generalInput.append(key)
                self.action = "ACTION"

            # Return if is an action.
            if (key in ACTIONS.values()):
                continue

            # Match case for fixed values.
            match key:
                # === MOVING LIST ===
                # --- moving one ---
                case keys.UP:
                    if(self.currentPageNumb > 1):
                        self.currentPageNumb -= 1
                case keys.DOWN:
                    if(self.currentPageNumb < self.songAmmnt):
                        self.currentPageNumb += 1
                # --- moving page ---
                case keys.RIGHT:
                    if(self.currentPageNumb+PAGE_SIZE < self.songAmmnt):
                        self.currentPageNumb += PAGE_SIZE
                    else:
                        self.currentPageNumb = self.songAmmnt
                case keys.LEFT:
                    if(self.currentPageNumb-PAGE_SIZE > 1):
                        self.currentPageNumb -= PAGE_SIZE
                    else:
                        self.currentPageNumb = 1

                case keys.BACKSPACE:
                    self.generalInput = self.generalInput[:-1]

                case _:
                    self.generalInput.append(key)

                    # Jump to ID
                    if (self.action == "JUMPID"):
                        idSearch = re.search(r'(?<=:)[1-9]\d*(?=\?|$)*', "".join(self.generalInput))
                        if idSearch:
                            idSearch = int(idSearch.group())

                            if(idSearch != None):
                                self.currentPageNumb = idSearch
                    # Searching
                    elif (self.action == "SEARCH"):
                        pass

                    # Song action.
                    elif (self.action == "ACTION"):
                        if (key == 'q'):
                            # Add current selected song to queue
                            self.execShell(f"audtool --playqueue-add {self.currentPageNumb}")

                        elif (key == 'c'):
                            # Add current selected song to queue
                            self.execShell(f"audtool --playqueue-clear")

                        elif (key == 'p'):
                            # Play selected song
                            self.execShell(f"audtool playlist-jump {self.currentPageNumb} --playback-play")
                            pass


audTool()